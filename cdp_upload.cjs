// 通过CDP (Chrome DevTools Protocol) 直接上传文件到豆包
// 使用 DOM.setFileInputFiles 方法

const WebSocket = require('ws');
const fs = require('fs');
const http = require('http');

const FILE_PATH = 'E:\\openclaw压缩包及启动教程\\u-claw\\portable\\data\\.openclaw\\workspace\\source.jpg';

// 目标页面的targetId
const TARGET_ID = '825E046363830D181777113EB25B405A';

async function getWSURL() {
  // 尝试多个可能的CDP端口
  const ports = [9222, 9221, 9223, 9229];
  for (const port of ports) {
    try {
      const body = await fetch(`http://127.0.0.1:${port}/json/version`);
      const data = await body.json();
      if (data.webSocketDebuggerUrl) {
        console.log(`Found CDP at port ${port}`);
        return data.webSocketDebuggerUrl;
      }
    } catch(e) {}
  }
  // 如果没找到标准CDP端口，尝试通过OpenClaw的CDP代理
  // 读取OpenClaw的配置文件寻找CDP信息
  try {
    const config = JSON.parse(fs.readFileSync('E:\\openclaw压缩包及启动教程\\u-claw\\portable\\app\\core\\node_modules\\openclaw\\config\\default.json', 'utf8'));
    console.log('Default config keys:', Object.keys(config).join(', '));
  } catch(e) {
    console.log('Cannot read config');
  }
  return null;
}

async function main() {
  const wsUrl = await getWSURL();
  if (!wsUrl) {
    console.log('No CDP endpoint found. Trying to start Chrome with debug port...');
    console.log('Will use alternative approach');
    return;
  }
  
  console.log('Connecting to:', wsUrl);
  
  // 连接到浏览器的CDP
  const ws = new WebSocket(wsUrl);
  
  ws.on('open', () => {
    console.log('CDP connected');
    
    // 先获取targets
    const msg = JSON.stringify({ id: 1, method: 'Target.getTargets' });
    ws.send(msg);
  });
  
  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    console.log('Response:', JSON.stringify(msg).substring(0, 200));
    
    if (msg.id === 1) {
      // Find doubao target
      const targets = msg.result.targetInfos;
      const doubao = targets.find(t => t.url.includes('doubao.com'));
      if (doubao) {
        console.log('Found doubao target:', doubao.targetId);
        
        // Attach to doubao target
        ws.send(JSON.stringify({ id: 2, method: 'Target.attachToTarget', params: { targetId: doubao.targetId, flatten: true } }));
      } else {
        // Use the provided targetId
        ws.send(JSON.stringify({ id: 2, method: 'Target.attachToTarget', params: { targetId: TARGET_ID, flatten: true } }));
      }
    } else if (msg.id === 2) {
      const sessionId = msg.result.sessionId;
      console.log('Attached, session:', sessionId);
      
      // Find file input and set file
      ws.send(JSON.stringify({ 
        id: 3, sessionId, 
        method: 'DOM.getDocument' 
      }));
      
      // Save sessionId and proceed
      globalThis._sessionId = sessionId;
      
      // Use Runtime.evaluate to find and set the file input
      setTimeout(() => {
        ws.send(JSON.stringify({
          id: 4, sessionId,
          method: 'Runtime.evaluate',
          params: {
            expression: 'document.querySelector("input[type=\\"file\\"]") ? "found" : "not found"'
          }
        }));
      }, 500);
    } else if (msg.id === 4) {
      console.log('File input check:', JSON.stringify(msg.result));
      
      const sessionId = globalThis._sessionId;
      // Add a local file path - CDP's setFileInputFiles needs absolute path on the machine
      ws.send(JSON.stringify({
        id: 5, sessionId,
        method: 'DOM.setFileInputFiles',
        params: {
          files: [FILE_PATH],
          nodeId: 1 // This won't work without proper nodeId, just testing if we can get CDP
        }
      }));
    }
  });
  
  ws.on('error', (err) => {
    console.log('CDP Error:', err.message);
  });
  
  // Timeout after 5 seconds
  setTimeout(() => {
    console.log('Timeout');
    ws.close();
    process.exit(0);
  }, 5000);
}

// Use node's built-in fetch if available (Node 18+)
globalThis.fetch = require('node-fetch');

async function fetch(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ json: async () => JSON.parse(data) }));
    }).on('error', reject);
  });
}

main().catch(console.error);
