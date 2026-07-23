# QQ官方机器人 ←→ OpenClaw 桥接服务

## 架构

```
QQ客户端/群 ←→ QQ官方Bot API ←→ 中间服务(Node.js) ←→ OpenClaw Webhook
```

## 启动

```bash
# 1. 先确保 OpenClaw 已运行（必须）

# 2. 启动桥接服务
cd qq-bot
node server.js
```

## 配置

编辑 `server.js` 里的 `CONFIG` 区域：

| 配置项 | 说明 |
|--------|------|
| `qq.appId` | QQ开放平台的应用ID |
| `qq.token` | QQ开放平台的 Token |
| `qq.apiBase` | API地址（正式/沙箱） |
| `openclaw.hookUrl` | OpenClaw hooks 地址 |
| `openclaw.token` | 跟 openclaw.json 的 hooks.token 一致 |

## 管理接口

启动后在 `http://127.0.0.1:3800`：

- `GET /health` — 健康检查
- `POST /qq/send` — 手动发消息到QQ

### 发送消息示例

```json
// 发到群/频道
POST /qq/send
{
  "channelId": "123456",
  "content": "大家好！"
}

// 发私聊
POST /qq/send
{
  "type": "direct",
  "guildId": "123456",
  "userId": "789",
  "content": "你好呀"
}
```

## QQ 开放平台配置

1. 登录 https://q.qq.com/
2. 创建机器人应用，获取 AppID 和 Token
3. 开启沙箱/正式环境
4. 不需要特别配置回调地址（使用 WebSocket 推送模式）

## 日志

启动后可以看到：
- `[QQBot] 就绪! sessionId=xxx` — 连接成功
- `[消息] 群聊 | 张三: 你好` — 收到QQ消息
- `[OpenClaw] ✅ 已转发` — 成功发给 OpenClaw
