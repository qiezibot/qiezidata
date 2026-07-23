package com.qiezi.app.service

import android.util.Log
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * 数据提取器
 * 负责读取 Android ID 和打包微信数据
 */
class DataExtractor(
    private val onProgress: (phase: String, progress: Int, message: String) -> Unit
) {
    private val TAG = "DataExtractor"
    private val WECHAT_PACKAGE = "com.tencent.mm"
    private val WECHAT_DATA_DIR = "/data/data/com.tencent.mm"

    /**
     * 提取微信数据的完成结果
     */
    data class ExtractResult(
        val androidId: String,
        val deviceInfo: String,
        val tarFileBytes: ByteArray,
        val dataSize: Long
    )

    /**
     * 完整提取流程
     */
    suspend fun extract(password: String): ExtractResult = withContext(Dispatchers.IO) {
        // 1. 检查 Root
        onProgress("检查权限", 5, "检查 Root 权限...")
        if (!RootManager.hasRoot()) {
            throw IllegalStateException("未获取到 Root 权限")
        }

        // 2. 读取 Android ID
        onProgress("读取设备ID", 10, "读取 Android ID...")
        val androidId = readAndroidId()
        if (androidId.isNullOrEmpty()) {
            throw IllegalStateException("读取 Android ID 失败")
        }

        // 3. 获取设备信息
        onProgress("读取设备信息", 15, "读取设备信息...")
        val deviceInfo = readDeviceInfo()

        // 4. 检查微信数据目录是否存在
        onProgress("检查目录", 20, "检查微信数据目录...")
        val checkResult = RootManager.execute("[ -d '$WECHAT_DATA_DIR' ] && echo 'EXISTS' || echo 'NOT_EXISTS'")
        if (!checkResult.stdout.contains("EXISTS")) {
            throw IllegalStateException("微信数据目录不存在，请确认已安装微信")
        }

        // 5. 打包微信数据
        onProgress("打包数据", 30, "正在打包微信数据...")
        val tarData = packageWechatData()

        // 6. 加密
        onProgress("加密数据", 80, "正在加密数据...")
        val fileBytes = CryptoUtil.packToFileBytes(tarData, password)

        onProgress("完成", 100, "提取完成！")

        ExtractResult(
            androidId = androidId,
            deviceInfo = deviceInfo,
            tarFileBytes = fileBytes,
            dataSize = tarData.size.toLong()
        )
    }

    /**
     * 读取 Android ID
     */
    private fun readAndroidId(): String? {
        val result = RootManager.execute("settings get secure android_id")
        val id = result.stdout.trim()
        Log.d(TAG, "Android ID: $id")
        return id.ifEmpty { null }
    }

    /**
     * 读取设备信息（辅助验证用）
     */
    private fun readDeviceInfo(): String {
        val sb = StringBuilder()
        val cmds = listOf(
            "getprop ro.product.manufacturer",
            "getprop ro.product.model",
            "getprop ro.build.version.release",
            "getprop ro.build.version.sdk"
        )
        for (cmd in cmds) {
            val result = RootManager.execute(cmd)
            if (result.isSuccess) {
                sb.append(result.stdout.trim()).append("|")
            }
        }
        return sb.toString().trimEnd('|')
    }

    /**
     * 打包微信数据目录
     * 排除 cache 和其他不必要的大文件
     */
    private fun packageWechatData(): ByteArray {
        val tempDir = "/data/local/tmp/qiezi_wechat"
        val tarFile = "$tempDir/wechat.tar"

        // 创建临时目录
        RootManager.execute(
            "rm -rf $tempDir",
            "mkdir -p $tempDir"
        )

        // 计算微信数据大小（排除 cache）
        val sizeResult = RootManager.execute("du -sb $WECHAT_DATA_DIR --exclude=cache 2>/dev/null | cut -f1")
        val totalSize = sizeResult.stdout.trim().toLongOrNull() ?: 0L
        Log.d(TAG, "微信数据总大小: $totalSize bytes")

        // 打包关键目录
        val directories = listOf(
            "shared_prefs",
            "databases",
            "files",
            "MicroMsg"
        )

        // 使用 tar 打包（排除 cache 和大文件）
        val excludePatterns = listOf(
            "--exclude=cache",
            "--exclude=MicroMsg/diskcache",
            "--exclude=MicroMsg/sfs",
            "--exclude=*.tmp",
            "--exclude=*.log"
        )
        val excludeStr = excludePatterns.joinToString(" ")

        val tarCmd = "cd / && tar cf $tarFile $excludeStr ${directories.joinToString(" ") { "$WECHAT_DATA_DIR/$it" }} 2>/dev/null"
        val tarResult = RootManager.execute(tarCmd)
        if (!tarResult.isSuccess) {
            Log.w(TAG, "tar警告: ${tarResult.stderr}")
        }

        // 检查打包结果
        val checkResult = RootManager.execute("ls -l $tarFile 2>/dev/null")
        if (!checkResult.isSuccess) {
            throw IllegalStateException("微信数据打包失败")
        }

        // 读取 tar 文件
        val readResult = RootManager.execute(
            "cat $tarFile",
            "rm -rf $tempDir"
        )
        val data = readResult.stdout.toByteArray()

        Log.d(TAG, "打包完成: ${data.size} bytes")
        return data
    }
}
