package com.qiezi.app.service

import android.util.Base64
import android.util.Log
import java.io.ByteArrayOutputStream
import java.io.File
import java.security.SecureRandom
import java.security.spec.KeySpec
import javax.crypto.Cipher
import javax.crypto.SecretKey
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.PBEKeySpec
import javax.crypto.spec.SecretKeySpec

/**
 * AES-256-GCM 加密解密工具
 * 使用 PBKDF2 从密码派生密钥
 */
object CryptoUtil {
    private const val TAG = "CryptoUtil"
    private const val ALGORITHM = "AES/GCM/NoPadding"
    private const val KEY_ALGORITHM = "AES"
    private const val KEY_DERIVATION = "PBKDF2WithHmacSHA256"
    private const val KEY_LENGTH = 256
    private const val GCM_TAG_LENGTH = 128  // bits
    private const val GCM_IV_LENGTH = 12    // bytes
    private const val PBKDF2_ITERATIONS = 100000
    private const val SALT_LENGTH = 16

    /**
     * 从密码派生 AES 密钥
     */
    private fun deriveKey(password: String, salt: ByteArray): SecretKey {
        val factory: SecretKeyFactory = SecretKeyFactory.getInstance(KEY_DERIVATION)
        val spec: KeySpec = PBEKeySpec(password.toCharArray(), salt, PBKDF2_ITERATIONS, KEY_LENGTH)
        val tmp = factory.generateSecret(spec)
        return SecretKeySpec(tmp.encoded, KEY_ALGORITHM)
    }

    /**
     * 加密数据
     * @return Triple(encryptedData, iv, salt)
     */
    fun encrypt(data: ByteArray, password: String): Triple<ByteArray, ByteArray, ByteArray> {
        val salt = ByteArray(SALT_LENGTH)
        SecureRandom().nextBytes(salt)
        val key = deriveKey(password, salt)

        val iv = ByteArray(GCM_IV_LENGTH)
        SecureRandom().nextBytes(iv)
        val spec = GCMParameterSpec(GCM_TAG_LENGTH, iv)

        val cipher = Cipher.getInstance(ALGORITHM)
        cipher.init(Cipher.ENCRYPT_MODE, key, spec)
        val encryptedData = cipher.doFinal(data)

        Log.d(TAG, "加密完成: ${data.size} bytes -> ${encryptedData.size} bytes")
        return Triple(encryptedData, iv, salt)
    }

    /**
     * 解密数据
     */
    fun decrypt(encryptedData: ByteArray, password: String, iv: ByteArray, salt: ByteArray): ByteArray {
        val key = deriveKey(password, salt)
        val spec = GCMParameterSpec(GCM_TAG_LENGTH, iv)

        val cipher = Cipher.getInstance(ALGORITHM)
        cipher.init(Cipher.DECRYPT_MODE, key, spec)
        val data = cipher.doFinal(encryptedData)

        Log.d(TAG, "解密完成: ${encryptedData.size} bytes -> ${data.size} bytes")
        return data
    }

    /**
     * 生成备份文件格式：
     * [魔数 5B][版本号 4B][salt 16B][iv 12B][数据长度 4B][加密数据]
     */
    fun packToFileBytes(data: ByteArray, password: String): ByteArray {
        val (encrypted, iv, salt) = encrypt(data, password)
        val bos = ByteArrayOutputStream()

        // 魔数
        bos.write(BackupPackage.MAGIC_HEADER.toByteArray(Charsets.US_ASCII))
        // 版本
        bos.write(intToBytes(BackupPackage.HEADER_VERSION))
        // salt
        bos.write(salt)
        // iv
        bos.write(iv)
        // 加密数据长度
        bos.write(intToBytes(encrypted.size))
        // 加密数据
        bos.write(encrypted)

        return bos.toByteArray()
    }

    /**
     * 从备份文件解析并解密
     */
    fun unpackFromFileBytes(fileBytes: ByteArray, password: String): ByteArray {
        var offset = 0

        // 验证魔数
        val magic = String(fileBytes, offset, 5, Charsets.US_ASCII)
        if (magic != BackupPackage.MAGIC_HEADER) {
            throw IllegalArgumentException("无效的备份文件格式")
        }
        offset += 5

        // 版本
        val version = bytesToInt(fileBytes, offset)
        offset += 4
        if (version != BackupPackage.HEADER_VERSION) {
            throw IllegalArgumentException("不支持的备份版本: $version")
        }

        // salt
        val salt = fileBytes.copyOfRange(offset, offset + SALT_LENGTH)
        offset += SALT_LENGTH

        // iv
        val iv = fileBytes.copyOfRange(offset, offset + GCM_IV_LENGTH)
        offset += GCM_IV_LENGTH

        // 加密数据长度
        val dataLen = bytesToInt(fileBytes, offset)
        offset += 4

        // 加密数据
        val encrypted = fileBytes.copyOfRange(offset, offset + dataLen)

        return decrypt(encrypted, password, iv, salt)
    }

    private fun intToBytes(value: Int): ByteArray = byteArrayOf(
        (value shr 24).toByte(),
        (value shr 16).toByte(),
        (value shr 8).toByte(),
        value.toByte()
    )

    private fun bytesToInt(bytes: ByteArray, offset: Int): Int =
        ((bytes[offset].toInt() and 0xFF) shl 24) or
        ((bytes[offset + 1].toInt() and 0xFF) shl 16) or
        ((bytes[offset + 2].toInt() and 0xFF) shl 8) or
        (bytes[offset + 3].toInt() and 0xFF)
}
