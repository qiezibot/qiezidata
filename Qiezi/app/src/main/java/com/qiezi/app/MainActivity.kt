package com.qiezi.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.snackbar.Snackbar
import com.qiezi.app.databinding.ActivityMainBinding
import com.qiezi.app.service.DataExtractor
import com.qiezi.app.service.DataRestorer
import com.qiezi.app.service.RootManager
import kotlinx.coroutines.*

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var isRunning = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        checkRootStatus()
    }

    private fun setupUI() {
        binding.btnExtract.setOnClickListener {
            if (isRunning) return@setOnClickListener
            val password = binding.etPassword.text?.toString()
            if (password.isNullOrBlank()) {
                Snackbar.make(binding.root, "请先设置密码", Snackbar.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            if (password.length < 4) {
                Snackbar.make(binding.root, "密码长度至少4位", Snackbar.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            startExtract(password)
        }

        binding.btnRestore.setOnClickListener {
            if (isRunning) return@setOnClickListener
            val password = binding.etPassword.text?.toString()
            if (password.isNullOrBlank()) {
                Snackbar.make(binding.root, "请输入密码", Snackbar.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            // 打开文件选择器
            openFilePicker()
        }
    }

    private fun checkRootStatus() {
        scope.launch {
            val hasRoot = withContext(Dispatchers.IO) { RootManager.hasRoot() }
            if (!hasRoot) {
                binding.tvStatus.text = "⚠️ 未获取到 Root 权限\n请确认已授予 Root 权限"
                binding.tvStatus.setTextColor(getColor(android.R.color.holo_red_dark))
            } else {
                binding.tvStatus.text = "✅ Root 权限正常\n微信数据目录就绪"
                binding.tvStatus.setTextColor(getColor(android.R.color.holo_green_dark))
            }
        }
    }

    private fun startExtract(password: String) {
        isRunning = true
        setButtonsEnabled(false)
        showProgress(true)

        val extractor = DataExtractor { phase, progress, message ->
            runOnUiThread {
                binding.tvProgress.text = "[$phase] $message"
                binding.progressBar.progress = progress
            }
        }

        scope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    extractor.extract(password)
                }

                // 保存文件到下载目录
                val fileName = "wechat_backup_${System.currentTimeMillis()}.qiezi"
                val downloadsDir = getExternalFilesDir(null) ?: filesDir
                val backupFile = java.io.File(downloadsDir, fileName)
                backupFile.writeBytes(result.tarFileBytes)

                binding.tvStatus.text = """
                    ✅ 提取完成！
                    Android ID: ${result.androidId}
                    数据大小: ${formatSize(result.dataSize)}
                    文件: $fileName
                """.trimIndent()

                Snackbar.make(binding.root, "备份文件已保存到: $fileName", Snackbar.LENGTH_LONG)
                    .setAction("分享") {
                        shareFile(backupFile)
                    }
                    .show()

            } catch (e: Exception) {
                binding.tvStatus.text = "❌ 提取失败: ${e.message}"
                Snackbar.make(binding.root, "提取失败: ${e.message}", Snackbar.LENGTH_LONG).show()
            } finally {
                isRunning = false
                setButtonsEnabled(true)
                showProgress(false)
            }
        }
    }

    private fun openFilePicker() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
        }
        startActivityForResult(intent, FILE_PICK_REQUEST)
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == FILE_PICK_REQUEST && resultCode == RESULT_OK) {
            data?.data?.let { uri ->
                val password = binding.etPassword.text?.toString()
                if (!password.isNullOrBlank()) {
                    startRestore(uri, password)
                } else {
                    Snackbar.make(binding.root, "请输入密码", Snackbar.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun startRestore(uri: Uri, password: String) {
        isRunning = true
        setButtonsEnabled(false)
        showProgress(true)

        restoreAndRestart(uri, password)
    }

    // 用多线程避免ANR
    private fun restoreAndRestart(uri: Uri, password: String) {
        Thread {
            try {
                // 读取文件
                val fileBytes = contentResolver.openInputStream(uri)?.use { it.readBytes() }
                    ?: throw IllegalStateException("无法读取文件")

                runOnUiThread {
                    doRestore(fileBytes, password)
                }
            } catch (e: Exception) {
                runOnUiThread {
                    binding.tvStatus.text = "❌ 读取文件失败: ${e.message}"
                    isRunning = false
                    setButtonsEnabled(true)
                    showProgress(false)
                }
            }
        }.start()
    }

    private fun doRestore(fileBytes: ByteArray, password: String) {
        val restorer = DataRestorer { phase, progress, message ->
            runOnUiThread {
                binding.tvProgress.text = "[$phase] $message"
                binding.progressBar.progress = progress
            }
        }

        scope.launch {
            try {
                val result = restorer.restore(fileBytes, password)
                if (result.success) {
                    binding.tvStatus.text = """
                        ✅ ${result.message}
                        Android ID: ${result.androidId}
                        数据大小: ${formatSize(result.dataSize)}
                    """.trimIndent()

                    Snackbar.make(binding.root, "恢复成功！请重启微信", Snackbar.LENGTH_LONG)
                        .setAction("打开微信") {
                            val intent = packageManager.getLaunchIntentForPackage("com.tencent.mm")
                            if (intent != null) {
                                startActivity(intent)
                            }
                        }
                        .show()
                } else {
                    binding.tvStatus.text = "❌ 恢复失败: ${result.message}"
                }
            } catch (e: Exception) {
                binding.tvStatus.text = "❌ 恢复失败: ${e.message}"
            } finally {
                isRunning = false
                setButtonsEnabled(true)
                showProgress(false)
            }
        }
    }

    private fun setButtonsEnabled(enabled: Boolean) {
        binding.btnExtract.isEnabled = enabled
        binding.btnRestore.isEnabled = enabled
        binding.etPassword.isEnabled = enabled
    }

    private fun showProgress(show: Boolean) {
        binding.progressBar.visibility = if (show) android.view.View.VISIBLE else android.view.View.GONE
        binding.progressBar.progress = 0
        binding.tvProgress.visibility = binding.progressBar.visibility
    }

    private fun shareFile(file: java.io.File) {
        val uri = androidx.core.content.FileProvider.getUriForFile(
            this,
            "$packageName.fileprovider",
            file
        )
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "application/octet-stream"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(shareIntent, "分享备份文件"))
    }

    private fun formatSize(bytes: Long): String {
        return when {
            bytes < 1024 -> "$bytes B"
            bytes < 1024 * 1024 -> "${bytes / 1024} KB"
            else -> "${"%.1f".format(bytes.toDouble() / (1024 * 1024))} MB"
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
    }

    companion object {
        private const val FILE_PICK_REQUEST = 1001
    }
}
