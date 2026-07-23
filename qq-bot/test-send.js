import express from 'express';

// ==================== 简单桥接服务 ====================
// 用途：QQ消息 → hooks/agent → OpenClaw → agent自动POST /qq/send → 回传QQ

const CONFIG = {
  qqBotToken: 'v1_MI6Q0voPd6cwJepr_t4ebmDGmaQulZn3x2rs8KNhQhozwiWiVuNdBq5HIrTZPbfAz6BAE3ET7EqTvotpDOiFoGtxUFMltzgwNAswazojVqs',
  qqAppId: '1904006743',
  oclawWebhookUrl: 'http://127.0.0.1:18789/hooks/agent',
  oclawWebhookToken: '8TpCayOoGiBfAgCkJsS3fIwaFwdL4oZK',
};

// 懒人精灵的OneBot协议可能更容易，但既然QQ Bot官方API的WS能连上却收不到消息，
// 我们直接提供一个完整的消息代理方案。
// 先写一个HTTP端点用来手动测试，后续可以用懒人精灵+onebot协议替代。

const app = express();
app.use(express.json());

// Agent回调接口 - QQ自动回复
app.post('/qq/send', async (req, res) => {
  const { channelId, content, msgId } = req.body;
  console.log(`[QQ回复] ${channelId}: ${content?.slice(0,30)}`);
  // 实际发QQ消息
  const token = await getAccessToken();
  const r = await fetch(`https://api.sgroup.qq.com/channels/${channelId}/messages`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, msg_id: msgId }),
  });
  const data = await r.text();
  res.json({ ok: r.ok, data });
});

app.get('/health', (req, res) => res.json({ ok: true }));

app.listen(3800, () => {
  console.log('QQ Bot Bridge running on :3800');
  console.log('POST /qq/send - agent回复QQ用');
  console.log('GET /health');
});

async function getAccessToken() {
  const r = await fetch('https://bots.qq.com/app/getAppAccessToken', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ appId: CONFIG.qqAppId, clientSecret: '8TpCayOoGiBfAgCkJsS3fIwaFwdL4oZK' }),
  });
  const data = await r.json();
  return data.access_token;
}
