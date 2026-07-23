package com.qiezi.app.service

import android.util.Log
import java.io.BufferedReader
import java.io.DataOutputStream
import java.io.InputStreamReader

/**
 * Root 权限管理，通过 su 执行命令
 * 不需要 libsu 等外部依赖，纯原生实现
 */
object RootManager {
    private const val TAG = "RootManager"

    /**
     * 检查是否拥有 Root 权限
     */
    fun hasRoot(): Boolean {
        return try {
            val process = Runtime.getRuntime().exec("su")
            val outputStream = DataOutputStream(process.outputStream)
            outputStream.writeBytes("id\n")
            outputStream.writeBytes("exit\n")
            outputStream.flush()
            process.waitFor()

            val reader = BufferedReader(InputStreamReader(process.inputStream))
            val output = reader.readText()
            val success = output.contains("uid=0")
            process.destroy()
            success
        } catch (e: Exception) {
            Log.e(TAG, "Root 检查失败", e)
            false
        }
    }

    /**
     * 以 root 权限执行命令，返回标准输出
     */
    fun execute(vararg commands: String): CommandResult {
        val result = CommandResult()
        try {
            val process = Runtime.getRuntime().exec("su")
            val outputStream = DataOutputStream(process.outputStream)
            val inputReader = BufferedReader(InputStreamReader(process.inputStream))
            val errorReader = BufferedReader(InputStreamReader(process.errorStream))

            for (cmd in commands) {
                Log.d(TAG, "执行: $cmd")
                outputStream.writeBytes("$cmd\n")
                outputStream.flush()
            }
            outputStream.writeBytes("exit\n")
            outputStream.flush()

            result.stdout = inputReader.readText()
            result.stderr = errorReader.readText()
            result.exitCode = process.waitFor()

            process.destroy()
            Log.d(TAG, "返回码: ${result.exitCode}, stdout: ${result.stdout.take(200)}")
        } catch (e: Exception) {
            Log.e(TAG, "命令执行失败", e)
            result.exitCode = -1
            result.stderr = e.message ?: "未知错误"
        }
        return result
    }

    /**
     * 获取文件的 uid:gid 字符串 (如 u0_a123)
     */
    fun getFileOwner(filePath: String): String? {
        val result = execute("stat -c '%U:%G' '$filePath' 2>/dev/null")
        if (result.isSuccess) {
            return result.stdout.trim()
        }
        // 备用方案：用ls -n
        val result2 = execute("ls -dn '$filePath' 2>/dev/null | awk '{print \$3\":\"\$4}'")
        return if (result2.isSuccess) result2.stdout.trim() else null
    }

    /**
     * 获取目标 App 的 uid 数字
     */
    fun getAppUid(packageName: String): Int? {
        val result = execute("dumpsys package $packageName 2>/dev/null | grep userId= | head -1 | sed 's/.*userId=\\([0-9]*\\).*/\\1/'")
        if (result.isSuccess && result.stdout.trim().isNotEmpty()) {
            return result.stdout.trim().toIntOrNull()
        }
        // 备用：从data目录取
        val result2 = execute("stat -c '%u' /data/data/$packageName 2>/dev/null")
        return if (result2.isSuccess) result2.stdout.trim().toIntOrNull() else null
    }

    data class CommandResult(
        var stdout: String = "",
        var stderr: String = "",
        var exitCode: Int = -1
    ) {
        val isSuccess: Boolean get() = exitCode == 0
    }
}
