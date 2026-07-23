// QQ机器人独立脚本 - 直接用QQ官方WebSocket API
// 不依赖openclaw插件系统，独立运行

const WebSocket = require('ws');
const https = require('https');

const APP_ID = '1904006743';
const APP_SECRET = '8TpCayOoGiBfAgCkJsS3fIwaFwdL4oZK';
const TOKEN = `Bot ${APP_ID}.${APP_SECRET}`;

// 获取gateway地址
function getGateway() {
  return new Promise((resolve, reject) => {
    https.get('https://api.sgroup.qq.com/gateway', {
      headers: { Authorization: TOKEN }
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { const j = JSON.parse(data); resolve(j.url); }
        catch(e) { reject(data); }
      });
    }).on('error', reject);
  });
}

async function start() {
  console.log('[QQBot] Getting gateway URL...');
  const gatewayUrl = await getGateway();
  console.log('[QQBot] Gateway:', gatewayUrl);

  const ws = new WebSocket(gatewayUrl);
  let heartbeatInterval = 30000;
  let heartbeatTimer = null;
  let seq = null;

  ws.on('open', () => {
    console.log('[QQBot] WebSocket connected, sending Identify...');
  });

  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    const { op, d, s, t } = msg;
    // console.log('[QQBot] RX op:', op, 't:', t);

    switch (op) {
      case 10: // Hello
        heartbeatInterval = d.heartbeat_interval;
        // Send Identify
        ws.send(JSON.stringify({
          op: 2,
          d: {
            token: TOKEN,
            intents: 1 << 30 | 1 << 25 | 1 << 9 | 1 << 0, // GUILD_MESSAGES + AT_MESSAGES + DIRECT_MESSAGE + PUBLIC_GUILD_MESSAGES
            shard: [0, 1],
            properties: { $os: 'windows', $browser: 'openclaw', $device: 'openclaw' }
          }
        }));
        // Start heartbeat
        if (heartbeatTimer) clearInterval(heartbeatTimer);
        heartbeatTimer = setInterval(() => {
          ws.send(JSON.stringify({ op: 1, d: seq }));
        }, heartbeatInterval);
        break;

      case 0: // Dispatch
        if (s) seq = s;
        handleEvent(t, d);
        break;

      case 11: // Heartbeat ACK
        break;
    }
  });

  ws.on('close', (code, reason) => {
    console.log('[QQBot] Disconnected:', code, reason?.toString());
    if (heartbeatTimer) clearInterval(heartbeatTimer);
    // Reconnect after 5s
    setTimeout(() => start(), 5000);
  });

  ws.on('error', (err) => {
    console.error('[QQBot] Error:', err.message);
  });
}

function handleEvent(type, data) {
  switch (type) {
    case 'READY':
      console.log('[QQBot] Ready! Bot:', data.user?.id, data.user?.username);
      break;
    case 'AT_MESSAGE_CREATE':
      console.log('[QQBot] AT message from:', data.author?.username, ':', data.content);
      replyMessage(data, `你好，我是茄子！你的消息是：${data.content}`);
      break;
    case 'MESSAGE_CREATE':
      console.log('[QQBot] Guild message from:', data.author?.username, ':', data.content);
      break;
    case 'DIRECT_MESSAGE_CREATE':
      console.log('[QQBot] Direct message:', data.content);
      break;
    default:
      if (type) console.log('[QQBot] Event:', type);
  }
}

function replyMessage(msg, text) {
  const channelId = msg.channel_id;
  const postData = JSON.stringify({ content: text, msg_id: msg.id });

  const req = https.request(`https://api.sgroup.qq.com/channels/${channelId}/messages`, {
    method: 'POST',
    headers: {
      Authorization: TOKEN,
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData)
    }
  }, (res) => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
      console.log('[QQBot] Reply sent, status:', res.statusCode);
    });
  });
  req.on('error', e => console.error('[QQBot] Reply error:', e.message));
  req.write(postData);
  req.end();
}

start().catch(err => {
  console.error('[QQBot] Fatal:', err);
  process.exit(1);
});
