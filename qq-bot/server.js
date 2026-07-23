/**
 * QQ官方机器人 ↔ OpenClaw 双向桥接服务 v2.1
 *
 * 新增：自动把 OpenClaw 的回复回传给 QQ 用户
 *
 * 机制：
 *   QQ消息 → 桥接服务 → OpenClaw hooks/agent → agent处理
 *                                                     ↓
 *   QQ用户 ← 桥接服务 ← agent主动POST /qq/send ← agent处理完
 *
 * 每个 hook 消息都包含完整的 QQ 上下文 + 回复指引。
 * 你需要在 OpenClaw 中给 agent 配置 HTTP 工具权限。
 */

import express from 'express';
import fetch from 'node-fetch';

// ==================== 配置 ====================
const CONFIG = {
  qq: {
    appId: '1904006743',
    secret: '8TpCayOoGiBfAgCkJsS3fIwaFwdL4oZK',
    apiBase: 'https://api.sgroup.qq.com',
    oauthUrl: 'https://bots.qq.com/app/getAppAccessToken',
    port: 3800,
  },
  openclaw: {
    hookUrl: 'http://127.0.0.1:18789/hooks/agent',
    wakeUrl: 'http://127.0.0.1:18789/hooks/wake',
    token: '8TpCayOoGiBfAgCkJsS3fIwaFwdL4oZK',
    // 中间服务自己的地址（给 agent 回调用）
    replyCallbackUrl: 'http://127.0.0.1:3800/qq/send',
  },
};

// ==================== QQ机器人客户端 ====================
class QQBotClient {
  constructor(appId, secret) {
    this.appId = appId;
    this.secret = secret;
    this.apiBase = CONFIG.qq.apiBase;
    this.accessToken = null;
    this.tokenExpiresAt = 0;
    this.ws = null;
    this.sessionId = null;
    this.heartbeatTimer = null;
    this.messageHandler = null;
    this.intents = (1 << 9) | (1 << 25);
  }

  async refreshAccessToken() {
    console.log('[QQBot] 获取 Access Token...');
    const res = await fetch(CONFIG.qq.oauthUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appId: this.appId, clientSecret: this.secret }),
    });
    if (!res.ok) throw new Error(`获取Token失败 (${res.status}): ${await res.text()}`);
    const data = await res.json();
    this.accessToken = data.access_token;
    this.tokenExpiresAt = Date.now() + (parseInt(data.expires_in) - 30) * 1000;
    console.log(`[QQBot] Token 获取成功，有效期 ${data.expires_in}s`);
    return this.accessToken;
  }

  async ensureToken() {
    if (!this.accessToken || Date.now() >= this.tokenExpiresAt) {
      await this.refreshAccessToken();
    }
    return this.accessToken;
  }

  async getAuthHeader() {
    return { 'Authorization': `Bearer ${await this.ensureToken()}` };
  }

  async request(method, path, body = null) {
    const headers = await this.getAuthHeader();
    headers['Content-Type'] = 'application/json';
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${this.apiBase}${path}`, opts);
    if (!res.ok) {
      const text = await res.text();
      // 如果 token 过期，刷新并重试一次
      if (res.status === 500 && text.includes('token')) {
        await this.refreshAccessToken();
        return this.request(method, path, body);
      }
      throw new Error(`API ${method} ${path} (${res.status}): ${text}`);
    }
    return await res.json();
  }

  async getGatewayUrl() {
    const data = await this.request('GET', '/gateway');
    return data.url;
  }

  // 发送群/频道消息
  async sendMessage(channelId, content, msgId = null) {
    const body = { content };
    if (msgId) body.msg_id = msgId;
    return await this.request('POST', `/channels/${channelId}/messages`, body);
  }

  // 发送私聊
  async sendDirectMessage(guildId, userId, content) {
    const dmData = await this.request('POST', '/users/@me/dms', {
      recipient_id: userId,
      source_guild_id: guildId,
    });
    if (!dmData.id) throw new Error(`创建DM失败: ${JSON.stringify(dmData)}`);
    return await this.sendMessage(dmData.id, content);
  }

  // 方便外部调用的统一发消息方法
  async reply(msg, text) {
    try {
      if (msg.type === 'group') {
        return await this.sendMessage(msg.channelId, text, msg.msgId);
      } else {
        return await this.sendDirectMessage(msg.guildId, msg.userId, text);
      }
    } catch (err) {
      console.error('[QQBot] 回复失败:', err.message);
    }
  }

  onMessage(handler) { this.messageHandler = handler; }

  async connect() {
    try {
      await this.ensureToken();
      const gatewayUrl = await this.getGatewayUrl();
      console.log(`[QQBot] 网关: ${gatewayUrl}`);

      const { default: WebSocket } = await import('ws');
      const ws = new WebSocket(`${gatewayUrl}/?v=1&encoding=json`);
      this.ws = ws;

      ws.on('open', () => console.log('[QQBot] ✅ WebSocket 已连接'));

      ws.on('message', (raw) => {
        try { this._handlePayload(JSON.parse(raw.toString())); }
        catch (err) { console.error('[QQBot] 解析失败:', err.message); }
      });

      ws.on('close', (code, reason) => {
        const r = reason ? Buffer.from(reason).toString() : '未知';
        console.log(`[QQBot] 断开 (${code}): ${r}`);
        this._cleanup();
        setTimeout(() => this.connect(), 3000);
      });

      ws.on('error', (err) => console.error('[QQBot] WS错误:', err.message));
    } catch (err) {
      console.error('[QQBot] 连接失败:', err.message);
      setTimeout(() => this.connect(), 5000);
    }
  }

  _cleanup() {
    if (this.heartbeatTimer) { clearInterval(this.heartbeatTimer); this.heartbeatTimer = null; }
    this.ws = null;
  }

  _handlePayload(payload) {
    const { op, d, t } = payload;
    const ws = this.ws;
    switch (op) {
      case 0: this._onDispatch(t, d); break;
      case 7: ws?.close(); break;
      case 9: ws?.close(); break;
      case 10:
        const interval = d?.heartbeat_interval || 30000;
        this.heartbeatTimer = setInterval(() => {
          if (ws?.readyState === 1) ws.send(JSON.stringify({ op: 1, d: null }));
        }, interval);
        ws.send(JSON.stringify({
          op: 2, d: {
            token: `QQBot ${this.accessToken}`,
            intents: this.intents,
            shard: [0, 1],
          },
        }));
        break;
      case 11: break;
    }
  }

  _onDispatch(t, d) {
    switch (t) {
      case 'READY':
        this.sessionId = d.session_id;
        console.log(`[QQBot] ✅ 就绪! sessionId=${d.session_id}, 用户名=${d.user?.username}`);
        break;
      case 'MESSAGE_CREATE':
        if (d.author?.bot) return;
        this.messageHandler?.({
          type: 'group',
          message: d.content,
          author: d.author?.username || '未知',
          userId: d.author?.id,
          channelId: d.channel_id,
          guildId: d.guild_id,
          msgId: d.id,
        });
        break;
      case 'DIRECT_MESSAGE_CREATE':
        if (d.author?.bot) return;
        this.messageHandler?.({
          type: 'direct',
          message: d.content,
          author: d.author?.username || '未知',
          userId: d.author?.id,
          channelId: d.channel_id,
          guildId: d.guild_id,
          msgId: d.id,
        });
        break;
    }
  }
}

// ==================== OpenClaw 客户端 ====================
class OpenClawClient {
  /**
   * 发送消息给 OpenClaw agent，并在消息中嵌入 QQ 上下文信息，
   * 这样 agent 知道怎么回复到 QQ。
   */
  async sendToAgent(qqMsg) {
    const label = qqMsg.type === 'group' ? '群聊' : '私聊';

    // 构建 agent 消息，包含完整的回复指引
    const msgBuilder = `[QQ消息]

来源：${label}
发送者：${qqMsg.author}（ID: ${qqMsg.userId}）
${qqMsg.type === 'group' ? `群ID: ${qqMsg.guildId}\n频道ID: ${qqMsg.channelId}` : `群ID: ${qqMsg.guildId}\n用户ID: ${qqMsg.userId}`}

消息内容：${qqMsg.message}

━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 【重要 - 关于回复】
如果你想回复这条QQ消息，请用 HTTP POST 请求调用：
POST ${CONFIG.openclaw.replyCallbackUrl}
Content-Type: application/json

请求体格式（群聊回复）：
{"channelId": "${qqMsg.channelId}", "content": "你的回复内容", "msgId": "${qqMsg.msgId}"}

请求体格式（私聊回复）：
{"type": "direct", "guildId": "${qqMsg.guildId}", "userId": "${qqMsg.userId}", "content": "你的回复内容"}

你不需要必须回复，但如果你觉得需要回复，请务必通过上述接口发送。
━━━━━━━━━━━━━━━━━━━━━━━━━━`;

    const payload = {
      message: msgBuilder,
      name: 'QQ-Bot',
      deliver: true,
      channel: 'last',
      wakeMode: 'now',
      sessionKey: `qq:${qqMsg.userId || 'unknown'}`,
    };

    try {
      const res = await fetch(CONFIG.openclaw.hookUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${CONFIG.openclaw.token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      return res.ok;
    } catch (err) {
      console.error('[OpenClaw] 发送失败:', err.message);
      return false;
    }
  }
}

// ==================== HTTP 服务 ====================
function startHttpServer(bot, openclaw) {
  const app = express();
  app.use(express.json());

  // 健康检查
  app.get('/health', (req, res) => {
    res.json({
      status: 'ok',
      qq: bot.ws?.readyState === 1 ? 'connected' : 'disconnected',
      appId: CONFIG.qq.appId,
      tokenExpires: bot.tokenExpiresAt ? new Date(bot.tokenExpiresAt).toISOString() : null,
    });
  });

  // 发消息到 QQ（OpenClaw agent 回调这个接口来回复）
  app.post('/qq/send', async (req, res) => {
    const { type, channelId, guildId, userId, content, msgId } = req.body;
    if (!content) return res.status(400).json({ error: '缺少 content' });

    try {
      let result;
      if (type === 'direct' || userId) {
        if (!guildId || !userId) return res.status(400).json({ error: '私聊需要 guildId 和 userId' });
        result = await bot.sendDirectMessage(guildId, userId, content);
      } else if (channelId) {
        result = await bot.sendMessage(channelId, content, msgId);
      } else {
        return res.status(400).json({ error: '需要 type+channelId 或 type=direct+guildId+userId' });
      }
      console.log(`[回复] ✅ 已发送到 QQ: ${content.slice(0, 50)}`);
      res.json(result);
    } catch (err) {
      console.error('[回复] ❌ 发送失败:', err.message);
      res.status(500).json({ error: err.message });
    }
  });

  app.listen(CONFIG.qq.port, () => {
    console.log(`[HTTP] 管理: http://127.0.0.1:${CONFIG.qq.port}`);
    console.log(`[HTTP]   GET  /health          — 健康检查`);
    console.log(`[HTTP]   POST /qq/send          — 发消息到QQ（agent调用此接口回复）`);
  });
}

// ==================== 消息处理 ====================
async function handleQQMessage(msg, bot, openclaw) {
  const label = msg.type === 'group' ? '群聊' : '私聊';
  console.log(`[消息] ${label} | ${msg.author}: ${msg.message}`);

  const ok = await openclaw.sendToAgent(msg);

  if (!ok) {
    console.error('[OpenClaw] 转发失败，直接回复QQ');
    await bot.reply(msg, '🤖 我现在不在状态，稍后再试试~');
  } else {
    console.log('[OpenClaw] ✅ 已转发（等待agent回复）');
  }
}

// ==================== 启动 ====================
async function main() {
  console.log('');
  console.log('═══════════════════════════════════');
  console.log('   QQ机器人 ←→ OpenClaw 双向桥接');
  console.log('   v2.1 — 支持双向回复');
  console.log('═══════════════════════════════════');
  console.log(`   QQ AppID  : ${CONFIG.qq.appId}`);
  console.log(`   API       : ${CONFIG.qq.apiBase}`);
  console.log(`   OpenClaw  : ${CONFIG.openclaw.hookUrl}`);
  console.log(`   回调地址  : ${CONFIG.openclaw.replyCallbackUrl}`);
  console.log(`   HTTP端口  : ${CONFIG.qq.port}`);
  console.log('═══════════════════════════════════\n');

  const openclaw = new OpenClawClient();
  const bot = new QQBotClient(CONFIG.qq.appId, CONFIG.qq.secret);

  bot.onMessage((msg) => handleQQMessage(msg, bot, openclaw));
  startHttpServer(bot, openclaw);

  await bot.connect();
}

main().catch((err) => {
  console.error('[FATAL]', err);
  process.exit(1);
});
