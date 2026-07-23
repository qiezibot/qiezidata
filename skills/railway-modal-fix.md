# Railway 文件服务器 - Profile Modal 不显示故障排查记录

## 问题描述
Admin 管理页面中，点击用户名（`onclick="openProfile()"`）弹不出用户资料模态框（profileModal），但**先切换到 API 文档 tab 后再点击就能正常弹出**。同样 pwdModal（修改密码弹窗）也有类似问题。

## 根因
**模态框的 HTML 被嵌套在了 API 文档 tab 页面的内容容器中**。

HTML 模板结构：
```html
<div class="tab-page" id="page-dashboard" class="active">...</div>
<div class="tab-page" id="page-apidocs">
  <div class="card" style="background:#e8f4fd;padding:15px">
    <h3>API 对接文档</h3>
    ...
    <!-- ⚠️ profileModal / pwdModal 的 HTML 在这里！ -->
    <div id="profileModalDummy" style="display:none">...</div>
    <div id="profileModal" style="display:none">...</div>
    <div id="pwdModal" style="display:none">...</div>
  </div>
</div>
```

CSS 规则：`.tab-page { display: none }`，`.tab-page.active { display: block }`。

默认打开的是 Dashboard（`page-dashboard` 激活），所以 `page-apidocs` 是 `display: none`。虽然 `openProfile()` 把 modal 自己的 `display` 改成了 `flex`，但被 **`display: none` 的父容器**限制了渲染——`position: fixed` 也不能突破 `display:none` 的父元素限制。

切换到 API 文档 tab 后（`page-apidocs` 变成 `display: block`），父容器不再隐藏，modal 就能正常显示了。

## 排查过程
1. 检查 JS 语法错误：所有脚本块括号平衡，无语法错误
2. 检查元素重复 ID：`profileModal` 有两个重复（一个空的 profileModalDummy 已被重命名）
3. 检查 Content-Security-Policy：服务器没有 CSP 限制
4. 控制台手动调用 `openProfile()` 发现函数执行成功，CSS 修改也应用了（`display: flex`），但页面看不到
5. 检查 `getComputedStyle` 确认 CSS 值正确
6. **关键一步：** 检查 `parentElement` 发现 modal 的父级是 `div.card`，在 `page-apidocs` 里
7. 通过 `start-sleep 90` 等待 Railway 部署后用 curl 验证

## 修复
将三个模态框的 HTML 从 tab-page 内容区**移到 `<body>` 标签后面**，脱离所有 tab 容器：

```python
# 提取每个 modal div 的 HTML
dummy_html = extract_div(template, pmd_pos)
real_html = extract_div(template, pm_pos)
pwd_html = extract_div(template, pwd_pos)

# 从原位置移除
new_template = template[:all_start] + template[all_end:]

# 插入到 <body> 后
body_pos = new_template.find('<body>')
all_modals = dummy_html + '\n' + real_html + '\n' + pwd_html
new_template = new_template[:body_pos+6] + '\n' + all_modals + '\n' + new_template[body_pos+6:]
```

## 经验教训
- **Modal 必须放在 `<body>` 的直接子级**，不能嵌套在 tab、card、modal 容器内
- 即使元素自身 `position: fixed`，如果父元素 `display: none`，仍然不可见
- `document.getElementById` 返回第一个匹配元素——重复 ID 导致取到了空的模态框（先解决）
- 调试技巧：用 `parentElement` 检查 DOM 树定位元素的实际容器
- Railway 部署推送到 GitHub 后约需 90 秒生效
