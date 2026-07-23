package com.qiezi.app.model

/**
 * 备份数据的封装
 */
data class BackupPackage(
    val appPackageName: String,       // 包名，固定 com.tencent.mm
    val appLabel: String,             // App名称，微信
    val androidId: String,            // 旧机的 Android ID
    val deviceInfo: String,           // 旧机设备信息
    val timestamp: Long,              // 备份时间戳
    val dataSize: Long,               // 数据大小（字节）
    val version: Int = 1,             // 格式版本
    val encryptedData: ByteArray,     // AES 加密的数据
    val iv: ByteArray,                // AES GCM IV
    val salt: ByteArray               // PBKDF2 salt
) {
    fun toMap(): Map<String, Any?> = mapOf(
        "appPackageName" to appPackageName,
        "appLabel" to appLabel,
        "androidId" to androidId,
        "deviceInfo" to deviceInfo,
        "timestamp" to timestamp,
        "dataSize" to dataSize,
        "version" to version,
        "encryptedData" to encryptedData,
        "iv" to iv,
        "salt" to salt
    )

    companion object {
        fun fromMap(map: Map<String, Any?>): BackupPackage = BackupPackage(
            appPackageName = map["appPackageName"] as String,
            appLabel = map["appLabel"] as String,
            androidId = map["androidId"] as String,
            deviceInfo = map["deviceInfo"] as String,
            timestamp = map["timestamp"] as Long,
            dataSize = map["dataSize"] as Long,
            version = (map["version"] as? Int) ?: 1,
            encryptedData = map["encryptedData"] as ByteArray,
            iv = map["iv"] as ByteArray,
            salt = map["salt"] as ByteArray
        )

        const val FILE_EXTENSION = ".qiezi"
        const val MAGIC_HEADER = "QIEZI"
        const val HEADER_VERSION = 1
    }
}

/**
 * 备份进度回调
 */
data class ProgressInfo(
    val phase: String,     // 当前阶段: 扫描/打包/加密/解密/恢复/写权限
    val progress: Int,     // 0-100
    val message: String    // 详细信息
)
