# MEMORY.md - 长期记忆

## 用户信息
- **爹 / 姐姐**（主人，女生，有时候让我喊爹有时候喊姐姐）
- 时间线：2026-05-11 初次见面
- 对电商、自动化、内容创作感兴趣
- 通过QQ语音交流
- ⚠️ 声纹识别需重新录入，当前版本识别偶有误差

## 合作项目

### 📖 番茄小说（待启动）
- 我负责写内容，用户负责发布操作
- 方向待定

### 🤖 懒人精灵脚本
- 抖音客服机器人脚本已写完（含DeepSeek API集成）
- 可改造成闲鱼自动化脚本

### 🖼️ 图片处理
- 用户需要批量抠图、做淘宝主图
- 推荐了 remove.bg、稿定设计、佐糖

## 桌面整理（2026-06-08）
- 爹要求清理桌面：只保留文件夹和快捷方式
- 我的文件全部搬到 `D:\桌面文件备份_20260608\`
- 包括：小说章节(ch01.txt, ch02.txt)、小说相关(novel.*, 风水小说.*)、autosend相关、fix-qqbot.bat、抠图测试图等
- 桌面只剩爹的文件夹和快捷方式

## Railway Deploy Check (2026-07-23)
- Project: qiezidata-production.up.railway.app
- Last attempt: 2026-07-23 03:08 CST — app returns **502 Bad Gateway** on all routes
- Suspected cause: latest commit `fix: hide dashboard and user management nav for non-admin users` broke startup
- Needs: check Railway deploy logs, fix crash, re-deploy

## 重要约定
- 用户数据严格保密
- 不会泄露任何商业秘密
- 用户负责账号/支付相关的实际操作，我做内容产出和技术方案
- **每完成一次重要配置，主动保存到 MEMORY.md / 配置文件 / 日志文件**，不留"临时方案"
- **重启/关机前必须做的事**：检查配置完整性，保存日志

## 技术环境
- Windows 10.0.22621
- Node.js v24.14.1
- Python 3.11.9（`C:\Users\lfy20\AppData\Local\Programs\Python\Python311\python.exe`）
- OpenClaw webchat + QQ通道
- 工作目录：workspace

## QQ 机器人（已打通 ✅）
- **AppID**: 1904006743
- **AppSecret**: aDrVApVBsaI1kUF1obPE4uldWPJEA631
- **插件**: @sliverp/qqbot（手动安装 + TS编译，路径：`extensions/qqbot/`）
- **配置键**: `channels.qqbot`
- **现状**：
  - ✅ 文字双向通信
  - ✅ 语音发送（edge-tts TTS，微软晓晓女声）
  - ✅ 语音接收转文字（Vosk离线识别）
- **⚠️ 配置重启问题记录（2026-05-17）**：
  - `config.patch` 写入后 SIGUSR1 只是热重载，不保证插件完全重载
  - 必须确保 `plugins.entries.qqbot.enabled: true` 也写入
  - 如果进程被 kill，启动脚本会启动新进程但 config 可能回滚到旧版
  - 建议每次配完后让爹重启控制台窗口确保完整重启
  - clientSecret 写错会报 "invalid appid or secret" (code:100016)

### 语音技术栈
- **TTS→Silk一站式脚本**: `workspace/voice_pipeline.py`（2026-05-16 重建）
  - 使用 edge-tts(Python) → ffmpeg转WAV(24000Hz 16bit mono) → pysilk转.silk
  - 用法：`python voice_pipeline.py "文字" "输出路径.silk"`
  - 输出目录：`C:\temp\tts\`
- **ffmpeg 路径**: `C:\temp\ffmpeg.exe`（已下载到C:\temp）
- **TTS**: edge-tts（Python 3.11），`zh-CN-XiaoxiaoNeural`
  - Python路径：`C:\Program Files\Python311\python.exe`
  - Node封装（备用）：`workspace/tts-edge.cjs`（仅输出MP3，需要ffmpeg转WAV）
- **STT**: Vosk（Python），中文小模型
  - **模型路径：`C:\vosk-model-small-cn-0.22`**
  - Python脚本：`workspace/stt_file.py`（写文件输出`_stt_out.txt`）
  - Node封装：`workspace/stt_wrapper.cjs`
  - 语音文件：QQ自动下载到 `C:\Users\lfy20\.openclaw\qqbot\downloads\*.bin`（实际是WAV）
  - WAV格式：1ch, 24000Hz, 16bit → Vosk原生支持

### 语音消息处理流程
收到用户语音 → 插件下载到本地 .bin (WAV) → AI收到消息（含语音附件路径）→ 手动调用 stt_wrapper.cjs 转文字 → 理解后回复（文字或语音）

### 发送格式
- 语音：`<qqvoice>本地路径</qqvoice>`
- 图片：`<qqimg>URL</qqimg>`
- 文件：`<qqfile>路径/URL</qqfile>`
- 视频：`<qqvideo>路径/URL</qqvideo>`

### 语音交流规则（2026-05-22 更新）
爹说"我们用语音交流吧"→切换为**语音模式**

四种模式：
1. **文字模式** — 只说文字
2. **语音模式** — 只发语音（纯`<qqvoice>`）
4. **语音+文字模式** — 文字与语音完全一致 ✅ **当前模式（2026-05-22 19:52更新）**
3. **图文模式** — 只发文字
4. **语音+文字模式** — 文字与语音完全一致（之前默认）

**语音+文字模式规则**：
- 文字写什么语音说什么，一字不差
- 先删旧silk→生成新silk→文字+`<qqvoice>`一起发→发完立即删
- 内容控制在聊天范围内，不发系统日志/工具调用分析

### 2026-06-28 QQ机器人修复
- **问题**：config被之前操作覆盖，`channels.qqbot` 和 plugin 配置丢失
- **修复**：写入 openclaw.json，用官方 `openclaw-qqbot` 插件（不再是手动编译版）
- **状态**：文字+语音双向通信 ✅
- **旧版扩展**：`qqbot_OLD` 和 `qqbot_backup_1.6.1` 已改名保留，不参与加载

### 2026-05-22 问候约定
- 删除了吃药提醒（爹要求）
- 爹说"上线的时候问候"→改由我每次重启上线时主动根据时间问好
- 不在 HEARTBEAT.md 写死问候，靠每次心跳的第一个消息来问候

### 2026-05-17 语音功能修复记录
- 故障：QQ机器人WS连不上，到22:58修复三次仍不行
- 根因：配置写了`appSecret`，插件要`clientSecret`，字段名不对
- 解决：改openclaw.json中字段名为clientSecret，杀所有旧进程重启
- 状态：✅ 已修好，语音+文字模式下正常通话

### 自动发送悬浮窗（auto_send_gui.exe）
- **功能**：检测键盘活动，停止输入3秒后自动按Enter发送
- **技术**：C# WinForms（.NET Framework 4.x），全局GetAsyncKeyState轮询 + WM_GETTEXTLENGTH输入框检测
- **编译器**：`C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe`（C# 5）
- **源码**：`workspace/auto_send_gui.cs`
- **可执行**：`C:\temp\auto_send_gui.exe`
- **UI特征**：蓝色铺满圆角条，`AutoSize=true`自适应，左边"自动发送"文字，右边iOS风格开关（CheckBox自绘）
- **可拖拽**：递归绑定到所有子控件
- **注意**：杀旧进程→编译→启动新进程

### 2026-07-01 清理frida/三角洲投屏工具
- 爹反馈：root管理器连电脑被清除数据，换新手机也会触发
- 根因：电脑上有adb工具链在手机连接时可能触发手机端安全机制
- **已卸载**：frida, frida-tools, frida-gadget（pip）
- **已删除**：workspace/adb_tools/, scrcpy/, delta_apk/, delta_apk_analysis/, java/, apktool/
- **已删除**：C:\temp\delta_*.py 所有脚本
- **已删除**：系统adb（WinGet platform-tools）+ .android/adbkey授权
- **系统残留**：
  - C:\Program Files (x86)\aztp\Resources\adb.exe（爱着投屏，需管理员卸载）
  - D:\懒人高级版1.8.4\adb\adb.exe（懒人精灵自带）
- **三角洲项目状态**：所有相关文件已清理，爹要求删除"推送功能"

### 声纹识别系统（2026-05-16 建立）
- **注册脚本**: workspace/voice_id.py
- **注册库**: workspace/voice_profiles/（爹.json、妈.json）
- **技术**: librosa MFCC 39维特征 + 余弦相似度
- **阈值**: 0.5
- **已注册**:
  - 爹 (发语音 → 叫爹，主动问好)
  - 妈 (发语音 → 叫妈，主动问好)
- **打招呼格式**: "爹好/妈好呀，我是茄子，你女儿"
  - 要生动、话多一点、自我介绍带名字
- **未来可优化**: 收集更多语音样本提升准确度

## 2026-07-22 profileModal 修复总结
- **根因**：modal 的 HTML 嵌套在 API 文档 tab 的 `div.card` 里面，因为该 tab 默认 `display: none`，modal 也跟着被隐藏
- **修复**：把三个模态框（profileModalDummy、profileModal、pwdModal）移到 `<body>` 标签后面
- **关键排查**：用 `parentElement` 发现 modal 在 `div.card` 里（page-apidocs 中）
- **不要**把模态框嵌套在任何 tab / card 容器里

## 技能库（赚钱用）
- **目录**: `workspace/skills/`
- **第一个技能**: `eggplant-data-deploy/` — 云端数据库搭建（FastAPI + PostgreSQL）
  - SKILL.md: 技能描述、架构、定价参考、操作流程
  - references/deployment-notes.md: 实际部署操作记录（含踩坑笔记）
  - scripts/verify_deployment.py: 部署验证脚本
- **技能库索引**: `README.md`
- 未来继续添加新技能到此目录
