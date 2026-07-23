# 茄子 ProGuard 规则
-keepattributes *Annotation*

# Keep 数据模型
-keep class com.qiezi.app.model.** { *; }

# Keep 序列化
-keep class * implements java.io.Serializable { *; }

# OkHttp / Retrofit (如果用到)
-dontwarn okhttp3.**
-dontwarn retrofit2.**

# 加密库
-keep class javax.crypto.** { *; }
-keep class java.security.** { *; }
