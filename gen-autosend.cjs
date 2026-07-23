const fs = require('fs');
const path = require('path');

const js = fs.readFileSync(
  path.join(__dirname, 'webchat-autosend.user.js'),
  'utf8'
);

// 提取函数体，去掉UserScript头部
const fn = js.replace(/\/\/ ==UserScript==[\s\S]*?\/\/ ==\/UserScript==\n?/, '');
const minified = fn.replace(/\s+/g, ' ').replace(/; /g, ';').replace(/ {/g, '{').replace(/} /g, '}').trim();
const bookmarklet = 'javascript:' + encodeURIComponent(minified);

const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>OpenClaw 自动发送</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:system-ui,-apple-system,sans-serif; background:linear-gradient(135deg,#0f0c29,#302b63,#24243e); color:white; min-height:100vh; display:flex; align-items:center; justify-content:center; }
.card { background:rgba(255,255,255,0.08); backdrop-filter:blur(12px); border-radius:20px; padding:40px; text-align:center; max-width:520px; border:1px solid rgba(255,255,255,0.1); }
.logo { font-size:60px; margin-bottom:12px; }
h1 { font-size:24px; font-weight:600; margin-bottom:6px; }
.desc { color:rgba(255,255,255,0.5); font-size:14px; margin-bottom:28px; line-height:1.5; }
.steps { text-align:left; background:rgba(0,0,0,0.3); border-radius:12px; padding:20px; margin-bottom:24px; }
.steps ol { padding-left:20px; color:rgba(255,255,255,0.7); font-size:13px; line-height:1.8; }
.steps ol li::marker { color:#10a37f; font-weight:bold; }
.btn { display:inline-block; background:#10a37f; color:white; border:none; padding:14px 32px; border-radius:10px; font-size:16px; cursor:pointer; transition:0.2s; text-decoration:none; font-weight:500; }
.btn:hover { background:#0e8c6e; transform:translateY(-1px); }
.hint { margin-top:16px; font-size:12px; color:rgba(255,255,255,0.3); }
.code { margin-top:16px; background:rgba(0,0,0,0.3); border-radius:8px; padding:12px; font-size:11px; color:rgba(255,255,255,0.3); word-break:break-all; max-height:80px; overflow:hidden; display:none; }
</style>
</head>
<body>
<div class="card">
<div class="logo">🍆</div>
<h1>自动发送书签</h1>
<p class="desc">把下面的按钮拖到书签栏，打开WebChat点一下就行</p>
<div class="steps">
<ol>
<li>把这个页面保持打开</li>
<li>打开 OpenClaw WebChat（点下面的按钮）</li>
<li>再点书签栏的 <strong>"自动发送"</strong></li>
<li>打字，停2秒自动发送 ✓</li>
</ol>
</div>
<a class="btn" href="${bookmarklet}" onclick="alert('把这个"自动发送"链接拖到浏览器书签栏');return false;">📌 拖我到书签栏</a>
<br><br>
<a class="btn" href="http://localhost:18789/webchat" style="background:#7c3aed;" target="_blank">打开 WebChat</a>
<p class="hint">💡 书签栏看不到？按 Ctrl+Shift+B 显示书签栏</p>
</div>
</body>
</html>`;

const dest = 'C:\\Users\\lfy20\\Desktop\\autosend-install.html';
fs.writeFileSync(dest, html, 'utf8');
console.log('Generated: ' + dest);
console.log('Bookmarklet length: ' + bookmarklet.length + ' chars');
