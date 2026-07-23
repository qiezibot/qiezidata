#!/usr/bin/env node
// 手动启动QQ Bot WebSocket连接
// 在干净的无代理环境中执行
import WebSocket from 'ws';

const APP_ID = '1904006743';
const SECRET = 'c3UwOrLpKpLrOwU3cCmNzbErV9oUArYG';

async function main() {
  // 1. 获取AccessToken
  console.log('[qqbot] Getting access token...');
  const r = await fetch('https://bots.qq.com/app/getAppAccessToken', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ appId: APP_ID, clientSecret: SECRET })
  });
  const d = await r.json();
  if (!d.access_token) {
    console.error('[qqbot] Failed to get token:', d);
    process.exit(1);
  }
  console.log('[qqbot] ✅ Token obtained');
  
  // 2. 获取Gateway地址
  const g = await fetch('https://api.sgroup.qq.com/gateway', {
    headers: { 'Authorization': `QQBot ${d.access_token}` }
  });
  const gd = await g.json();
  console.log('[qqbot] Gateway URL:', gd.url);
  
  // 3. 连接WebSocket
  console.log('[qqbot] Connecting WebSocket...');
  const ws = new WebSocket(gd.url);
  
  ws.on('open', () => {
    console.log('[qqbot] ✅ WebSocket connected!');
  });
  
  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data.toString());
      console.log('[qqbot] Received:', JSON.stringify(msg).slice(0, 200));
      
      if (msg.op === 10) { // Hello - 发心跳
        const heartbeat = msg.d.heartbeat_interval;
        console.log('[qqbot] Heartbeat interval:', heartbeat, 'ms');
        setInterval(() => {
          ws.send(JSON.stringify({ op: 1 }));
        }, heartbeat);
        // 发送Identify
        ws.send(JSON.stringify({
          op: 2,
          d: {
            token: `QQBot ${d.access_token}`,
            intents: 1 << 25, // GROUP_AND_C2C
            shard: [0, 1]
          }
        }));
      } else if (msg.op === 0) { // Dispatch - 有消息事件
        console.log('[qqbot] Event:', msg.t, msg.d?.content?.slice?.(0, 100));
      }
    } catch(e) {
      console.log('[qqbot] Parse error:', e.message);
    }
  });
  
  ws.on('error', (err) => {
    console.error('[qqbot] WS Error:', err.message);
  });
  
  ws.on('close', (code, reason) => {
    console.log('[qqbot] WS Closed:', code, reason?.toString());
  });
}

main().catch(err => console.error('[qqbot] Fatal:', err));
