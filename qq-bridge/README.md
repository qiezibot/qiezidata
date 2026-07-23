# QQ ↔ OpenClaw 桥接中间件

通过 NapCat + WebSocket 桥接，让 OpenClaw 接入 QQ。

## 架构

```
QQ客户端 ←→ NapCat (QQ机器人框架) ←[WebSocket]→ 桥接脚本 ←[HTTP API]→ OpenClaw
```

## 前置准备

### 1. 安装 NapCat

NapCat 是一个轻量级 QQ 机器人框架，基于 OneBot v11 协议。

**下载安装：**
- 官网教程：https://napcat.napneko.icu/guide/getting-started
- 下载对应系统的 NapCat 包，解压运行
- 扫码登录 QQ 小号

**配置 WebSocket：**

在 NapCat 配置中（通常在 `config/onebot11.json` 或 napcat UI 中）：
- 开启反向 WebSocket 服务端，配置地址 `ws://127.0.0.1:8085`
- 或者开启正向 WebSocket 客户端，默认端口 3001

### 2. 获取 OpenClaw Token

在 OpenClaw 控制台运行：
```
/config get gateway.auth.token
```

## 配置

编辑 `index.js` 顶部的 `CONFIG` 区域：

```js
// OpenClaw token（也可通过环境变量 OPENCLAW_GATEWAY_TOKEN 设置）
token: '你的token',

// NapCat 模式
// 'reverse' = NapCat 主动连我们（推荐）
// 'forward' = 我们去连 NapCat
mode: 'reverse',

// 如果需要限制只处理特定群/用户
allowedGroups: ['群号1', '群号2'],
allowedUsers: ['QQ号1'],

// 触发方式
triggerPrefix: ''       // 例如 '!' 则消息以 ! 开头才响应
respondToAt: true       // @机器人时响应
```

## 运行

```bash
cd qq-bridge
npm start
```

## 测试

启动后：
1. 确保 NapCat 已连接（控制台会显示"NapCat 已连接"）
2. 用 QQ 小号给自己大号发消息
3. 或者加机器人好友发消息
4. 机器人会把消息传给 OpenClaw 处理并回复
