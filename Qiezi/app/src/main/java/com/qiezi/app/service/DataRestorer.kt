package com.qiezi.app.service

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

/**
 * 数据恢复器
 * 负责解密数据、修改 Android ID、恢复微信数据
 */
class DataRestorer(
    private val onProgress: (phase: String, progress: Int, message: String) -> Unit
) {
    private val TAG = "DataRestorer"
    private val WECHAT_DATA_DIR = "/data/data/com.tencent.mm"

    /**
     * 恢复结果
     */
    data class RestoreResult(
        val success: Boolean,
        val message: String,
        val androidId: String? = null,
        val dataSize: Long = 0
    )

    /**
     * 完整恢复流程
     */
    suspend fun restore(fileBytes: ByteArray, password: String): RestoreResult = withContext(Dispatchers.IO) {
        try {
            // 1. 检查 Root
            onProgress("检查权限", 5, "检查 Root 权限...")
            if (!RootManager.hasRoot()) {
                return@withContext RestoreResult(false, "未获取到 Root 权限")
            }

            // 2. 解析备份文件头，获取 Android ID
            onProgress("解析备份", 10, "解析备份文件...")
            val headerInfo = parseBackupHeader(fileBytes)
            val oldAndroidId = headerInfo?.androidId
            if (oldAndroidId.isNullOrEmpty()) {
                return@withContext RestoreResult(false, "备份文件中未找到 Android ID")
            }

            // 3. 解密数据
            onProgress("解密数据", 20, "正在解密数据...")
            val decryptedData: ByteArray
            try {
                decryptedData = CryptoUtil.unpackFromFileBytes(fileBytes, password)
            } catch (e: Exception) {
                Log.e(TAG, "解密失败", e)
                return@withContext RestoreResult(false, "解密失败，密码错误或文件损坏")
            }

            // 4. 停止微信（避免文件占用）
            onProgress("停止微信", 30, "正在停止微信...")
            RootManager.execute(
                "am force-stop $WECHAT_DATA_DIR 2>/dev/null",
                "sleep 2"
            )

            // 5. 修改 Android ID
            onProgress("修改设备ID", 40, "正在修改 Android ID...")
            val setAidResult = RootManager.execute("settings put secure android_id '$oldAndroidId'")
            if (!setAidResult.isSuccess) {
                return@withContext RestoreResult(false, "修改 Android ID 失败: ${setAidResult.stderr}")
            }
            // 验证
            val verifyResult = RootManager.execute("settings get secure android_id")
            if (verifyResult.stdout.trim() != oldAndroidId) {
                Log.w(TAG, "Android ID 可能未生效: 期望='$oldAndroidId', 实际='${verifyResult.stdout.trim()}'")
            }

            // 6. 备份旧微信数据
            onProgress("备份旧数据", 50, "备份旧微信数据...")
            RootManager.execute(
                "mv $WECHAT_DATA_DIR ${WECHAT_DATA_DIR}_bak_$(date +%s) 2>/dev/null; echo 'OK'"
            )

            // 7. 恢复微信数据
            onProgress("恢复数据", 60, "正在恢复微信数据...")
            val tempTarFile = "/data/local/tmp/qiezi_restore.tar"
            // 写入 tar 数据
            RootManager.execute(
                "echo '${decryptedData.decodeToString().replace("'", "'\\''")}' > $tempTarFile"
            )
            // 解压
            val restoreResult = RootManager.execute(
                "mkdir -p $WECHAT_DATA_DIR",
                "cd / && tar xf $tempTarFile 2>/dev/null",
                "rm -f $tempTarFile"
            )

            // 8. 修复权限
            onProgress("修复权限", 80, "正在修复文件权限...")
            val uid = RootManager.getAppUid("com.tencent.mm")
            if (uid != null && uid > 0) {
                RootManager.execute(
                    "chown -R $uid:$uid $WECHAT_DATA_DIR",
                    "chmod -R 755 $WECHAT_DATA_DIR",
                    "chmod -R 700 $WECHAT_DATA_DIR/shared_prefs",
                    "chmod -R 700 $WECHAT_DATA_DIR/databases",
                    "chmod -R 700 $WECHAT_DATA_DIR/MicroMsg"
                )
                // 修复 SELinux 上下文
                RootManager.execute("chcon -R u:object_r:app_data_file:s0:c512,c768 $WECHAT_DATA_DIR 2>/dev/null")
            }

            onProgress("完成", 100, "恢复完成！请重启微信")

            val dataSize = RootManager.execute("du -sb $WECHAT_DATA_DIR 2>/dev/null | cut -f1")
            return@withContext RestoreResult(
                success = true,
                message = "恢复成功！已修改 Android ID 并恢复微信数据，请重启微信",
                androidId = oldAndroidId,
                dataSize = dataSize.stdout.trim().toLongOrNull() ?: 0
            )

        } catch (e: Exception) {
            Log.e(TAG, "恢复过程异常", e)
            return@withContext RestoreResult(false, "恢复失败: ${e.message}")
        }
    }

    /**
     * 从备份文件头读取信息（不解密）
     */
    private fun parseBackupHeader(fileBytes: ByteArray): HeaderInfo? {
        return try {
            val magic = String(fileBytes, 0, 5, Charsets.US_ASCII)
            if (magic != "QIEZI") return null

            // 这个简化版不解析，从完整数据流中拿
            null
        } catch (e: Exception) {
            null
        }
    }

    data class HeaderInfo(
        val androidId: String,
        val deviceInfo: String,
        val appName: String
    )
}
