/**
 * QQ ↔ OpenClaw 桥接中间件
 * 
 * 架构: QQ客户端 → NapCat ←[WebSocket]→ 桥接脚本 ←[HTTP API]→ OpenClaw
 * 
 * 前置条件：
 * 1. 安装并运行 NapCat (https://napcat.napneko.icu/)
 * 2. NapCat 配置好 WebSocket 连接
 * 3. 知道 OpenClaw 的 gateway token
 * 
 * 运行: npm start
 */

const { WebSocket } = require('ws');
const http = require('http');

// ============ 配置 ============
const CONFIG = {
  openclaw: {
    host: '127.0.0.1',
    port: 7070,
    token: process.env.OPENCLAW_GATEWAY_TOKEN || '',
    httpApiPrefix: '/tools/invoke',
  },
  napcat: {
    // 'reverse': NapCat 连我们（推荐，稳定）
    // 'forward': 我们去连 NapCat（需要知道 NapCat 的 WS 地址）
    mode: 'reverse',
    reversePort: 8085,
    forwardUrl: 'ws://127.0.0.1:3001',
  },
  // 允许响应的群/用户（空数组 = 全部放行）
  allowedGroups: [],
  allowedUsers: [],
  // 响应方式
  respondToAt: true,     // @机器人时回复
  respondAll: false,     // true = 所有消息都回复（慎用）
  maxReplyLen: 2000,
};

// ============ 全局状态 ============
let napcatWs = null;
const pendingReplies = new Map(); // key: 用户标识, value: {resolve, timer}

// ============ OpenClaw HTTP API ============

function openclawRequest(tool, args) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      tool,
      action: 'json',
      args,
      sessionKey: 'qq-bridge',
      dryRun: false,
    });

    const req = http.request(
      `http://${CONFIG.openclaw.host}:${CONFIG.openclaw.port}${CONFIG.openclaw.httpApiPrefix}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${CONFIG.openclaw.token}`,
        },
        timeout: 120000, // AI 思考可能需要较长时间
      },
      (res) => {
        let data = '';
        res.on('data', c => data += c);
        res.on('end', () => {
          try { resolve(JSON.parse(data)); }
          catch { resolve({ ok: false, error: data }); }
        });
      }
    );
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(body);
    req.end();
  });
}

// ============ 消息处理 ============

async function handleQQMessage(msg) {
  // 只处理消息事件
  if (msg.post_type !== 'message') return;

  const msgType = msg.message_type; // 'group' | 'private'
  const userId = String(msg.user_id);
  const groupId = msg.group_id ? String(msg.group_id) : '';
  const rawMsg = msg.raw_message || '';
  const sender = msg.sender?.nickname || msg.sender?.card || `用户${userId}`;

  // 过滤白名单
  if (msgType === 'group' && CONFIG.allowedGroups.length && !CONFIG.allowedGroups.includes(groupId)) return;
  if (msgType === 'private' && CONFIG.allowedUsers.length && !CONFIG.allowedUsers.includes(userId)) return;

  // 提取纯文本
  const text = rawMsg.replace(/\[CQ:[^\]]*\]/g, '').trim();
  if (!text) return;

  // 判断是否应该回复
  let shouldReply = CONFIG.respondAll;

  // @ 触发
  if (!shouldReply && CONFIG.respondToAt) {
    const atSelf = msg.message?.find?.(s => s.type === 'at' && String(s.data.qq) === String(msg.self_id));
    if (atSelf) shouldReply = true;
  }

  if (!shouldReply) return;

  // 构造上下文消息
  const context = msgType === 'group'
    ? `[QQ群(${groupId}) ${sender}] ${text}`
    : `[QQ私聊 ${sender}] ${text}`;

  console.log(`\n📨 [${msgType}] ${sender}: ${text}`);

  // 在 QQ 发一个"正在输入"效果
  sendAction(msgType, msgType === 'group' ? groupId : userId);

  try {
    // 发消息到 OpenClaw，等 AI 回复
    const result = await openclawRequest('sessions_send', {
      sessionKey: 'qq-bridge',
      message: context,
      // 30 秒超时
      timeoutSeconds: 30,
    });

    // 从返回结果提取 AI 回复
    let reply = '';
    if (result?.ok && result?.result?.response) {
      reply = result.result.response;
    } else if (result?.ok && result?.result?.message) {
      reply = result.result.message;
    } else if (result?.result) {
      reply = typeof result.result === 'string' ? result.result : JSON.stringify(result.result);
    } else {
      reply = '嗯？我没理解。';
    }

    // 清理回复文本
    reply = cleanReply(reply);

    if (reply) {
      sendReply(msgType, userId, groupId, reply, msg);
      console.log(`✅ 回复: ${reply.slice(0, 100)}`);
    }
  } catch (err) {
    console.error(`❌ 错误: ${err.message}`);
  }
}

function cleanReply(text) {
  if (typeof text !== 'string') return '';
  // 去掉可能的系统消息
  return text
    .replace(/^\[.*?\]\s*/g, '')
    .trim()
    .slice(0, CONFIG.maxReplyLen);
}

function sendAction(msgType, target) {
  if (!napcatWs || napcatWs.readyState !== WebSocket.OPEN) return;
  const action = msgType === 'group' ? 'send_group_msg' : 'send_private_msg';
  const params = msgType === 'group'
    ? { group_id: Number(target), message: '...' }
    : { user_id: Number(target), message: '...' };
  napcatWs.send(JSON.stringify({ action, params, echo: `typing_${Date.now()}` }));
}

function sendReply(msgType, userId, groupId, text, originalMsg) {
  if (!napcatWs || napcatWs.readyState !== WebSocket.OPEN) return;

  let message = text;
  // 群聊 @ 发送者
  if (msgType === 'group') {
    message = `[CQ:at,qq=${originalMsg.user_id}] ${text}`;
  }

  const action = msgType === 'group' ? 'send_group_msg' : 'send_private_msg';
  const params = msgType === 'group'
    ? { group_id: Number(groupId), message }
    : { user_id: Number(userId), message };

  napcatWs.send(JSON.stringify({ action, params, echo: `reply_${Date.now()}` }));
}

// ============ WebSocket 服务 ============

function startReverseWs() {
  const server = http.createServer();
  const wss = new (require('ws').Server)({ server });

  wss.on('connection', (ws) => {
    console.log('✅ NapCat 已连接（反向WS）');
    napcatWs = ws;

    ws.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());
        handleQQMessage(msg);
      } catch (e) {
        console.error('❌ 消息解析错误:', e.message);
      }
    });

    ws.on('close', () => {
      console.log('⚠️ NapCat 断开');
      napcatWs = null;
    });

    ws.on('error', (e) => console.error('WS错误:', e.message));
  });

  server.listen(CONFIG.napcat.reversePort, () => {
    console.log(`✅ 反向WS服务: ws://127.0.0.1:${CONFIG.napcat.reversePort}`);
  });
}

function startForwardWs() {
  const connect = () => {
    const ws = new WebSocket(CONFIG.napcat.forwardUrl);
    ws.on('open', () => {
      console.log(`✅ 已连接 NapCat: ${CONFIG.napcat.forwardUrl}`);
      napcatWs = ws;
    });
    ws.on('message', (data) => {
      try { handleQQMessage(JSON.parse(data.toString())); }
      catch (e) { console.error('❌ 消息解析错误:', e.message); }
    });
    ws.on('close', () => {
      console.log('⚠️ NapCat 断开，15秒后重连');
      napcatWs = null;
      setTimeout(connect, 15000);
    });
    ws.on('error', (e) => console.error('WS错误:', e.message));
  };
  connect();
}

// ============ 启动 ============

function main() {
  // 检查 token
  if (!CONFIG.openclaw.token) {
    console.error('❌ 缺少 OpenClaw token');
    console.error('   通过环境变量设置: set OPENCLAW_GATEWAY_TOKEN=xxx');
    console.error('   或在 CONFIG.openclaw.token 中填写');
    process.exit(1);
  }

  console.log('╔═══════════════════════════════════════╗');
  console.log('║   QQ ↔ OpenClaw 桥接 v1.0            ║');
  console.log('╚═══════════════════════════════════════╝');
  console.log(`  OpenClaw: http://${CONFIG.openclaw.host}:${CONFIG.openclaw.port}`);
  console.log(`  NapCat:   ${CONFIG.napcat.mode === 'reverse' ? '反向WS :8085' : '正向WS ' + CONFIG.napcat.forwardUrl}`);
  console.log(`  回复模式: ${CONFIG.respondAll ? '全部消息' : CONFIG.respondToAt ? '@触发' : '前缀触发'}`);
  console.log('');

  if (CONFIG.napcat.mode === 'reverse') {
    startReverseWs();
  } else {
    startForwardWs();
  }
}

main();
