"""
Build railway_file_server.py with password UI.
Strategy: don't modify _ADMIN template at all.
Instead, inject a self-contained inline script + modal HTML into the
_admin return statement in the home() function.

The approach:
  _ADMIN + EXTRA_HTML + '<script>' + EXTRA_JS + '</script>'

This keeps _ADMIN unchanged and the extra content is only ~2KB minified.
"""
import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 构造要追加的 HTML+JS（内联，最小化）
# HTML 模态框 + 样式 + script
extra = """<style>
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000}
.modal-content{background:#fff;padding:24px;border-radius:12px;width:420px;max-width:90vw;position:relative}
.modal-close{position:absolute;top:12px;right:16px;font-size:22px;cursor:pointer;color:#999}
.modal-close:hover{color:#333}
.modal .form-group{margin-bottom:12px}
.modal .form-group label{display:block;font-size:13px;color:#666;margin-bottom:4px}
.modal .form-group input{width:100%;padding:8px 10px;border:1px solid #ddd;border-radius:6px;font-size:14px}
.modal .btn{width:100%;padding:10px;background:#667eea;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}
.modal .msg{padding:10px;border-radius:6px;margin-top:10px;font-size:14px;text-align:center}
</style>
<div id=pModal class=modal style=display:none><div class=modal-content><span class=modal-close onclick=pClose()>×</span><h3>个人资料</h3><div class=form-group><label>用户名</label><input id=pU type=text disabled></div><div class=form-group><label>显示名称</label><input id=pDN type=text placeholder="输入显示名称"></div><div class=form-group><label>角色</label><input id=pR type=text disabled></div><button class=btn onclick=pSave()>保存</button><div id=pSaveMsg class=msg style=display:none></div><hr style=margin:16px 0><h4>修改密码</h4><div class=form-group><label>旧密码</label><input id=pOld type=password placeholder="输入旧密码"></div><div class=form-group><label>新密码</label><input id=pNew type=password placeholder="至少4个字符"></div><div class=form-group><label>确认新密码</label><input id=pNew2 type=password placeholder="再次输入"></div><button class=btn onclick=pSubmit()>修改密码</button><div id=pPwdMsg class=msg style=display:none></div></div></div>
<div id=cpModal class=modal style=display:none><div class=modal-content><span class=modal-close onclick=document.getElementById("cpModal").style.display="none">×</span><h3>修改用户密码</h3><p id=cpInfo style=color:#666;margin-bottom:12px;font-size:13px></p><div class=form-group><label>新密码</label><input id=cpNewPwd type=password placeholder="至少4个字符"></div><button class=btn onclick=cpSubmit()>确认修改</button><div id=cpMsg class=msg style=display:none></div></div></div>
<script>
function pOpen(){document.getElementById("pModal").style.display="flex";fetch("/me",{credentials:"include"}).then(function(r){return r.json()}).then(function(u){document.getElementById("pU").value=u.username||"";document.getElementById("pDN").value=u.display_name||"";document.getElementById("pR").value=u.role||""})}
function pClose(){document.getElementById("pModal").style.display="none"}
function pSave(){var dn=document.getElementById("pDN").value.trim();var m=document.getElementById("pSaveMsg");m.style.display="none";fetch("/me",{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent="已保存",m.style.color="#27ae60"):(m.textContent=d.detail||"保存失败",m.style.color="#e74c3c");m.style.display="block";setTimeout(function(){m.style.display="none"},3000)})}
function pSubmit(){var o=document.getElementById("pOld").value,n=document.getElementById("pNew").value,n2=document.getElementById("pNew2").value,m=document.getElementById("pPwdMsg");m.style.display="none";if(!o){m.textContent="请输入旧密码";m.style.display="block";return}if(n.length<4){m.textContent="新密码至少4个字符";m.style.display="block";return}if(n!==n2){m.textContent="两次输入不一致";m.style.display="block";return}fetch("/me/change_password",{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({old_password:o,new_password:n})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent="密码已修改",m.style.color="#27ae60",document.getElementById("pOld").value="",document.getElementById("pNew").value="",document.getElementById("pNew2").value=""):(m.textContent=d.detail||"修改失败",m.style.color="#e74c3c");m.style.display="block";setTimeout(function(){m.style.display="none"},3000)})}
var _cu=0;
function aCP(u){_cu=u;document.getElementById("cpModal").style.display="flex";document.getElementById("cpInfo").textContent="\u7528\u6237ID: "+u;document.getElementById("cpNewPwd").value="";document.getElementById("cpMsg").style.display="none"}
function cpSubmit(){var n=document.getElementById("cpNewPwd").value,m=document.getElementById("cpMsg");m.style.display="none";if(n.length<4){m.textContent="\u65b0\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26";m.style.display="block";return}fetch("/admin/user/"+_cu+"/change_password",{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({new_password:n})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent="\u5bc6\u7801\u5df2\u4fee\u6539",m.style.color="#27ae60",setTimeout(function(){document.getElementById("cpModal").style.display="none"},1500)):(m.textContent=d.detail||"\u4fee\u6539\u5931\u8d25",m.style.color="#e74c3c");m.style.display="block"})}
</script>"""

# 在 _ADMIN return 语句中拼接到最后
# 找到这两行（admin 和 user 两种角色）
old1 = "return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))"
# 两次 return 的内容完全一样
new1 = "return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')) + '''" + extra + "''')"

# 只是替换，模板内容不变
c = c.replace(old1, new1)

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)

import ast
ast.parse(c)
print(f'OK! {len(c)} bytes')
print(f'Extra size: {len(extra)}')
