// ==UserScript==
// @name         OpenClaw 自动发送 + 按钮
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  输入框旁边加一个自动发送开关按钮
// @author       OpenClaw
// @match        *://127.0.0.1:18789/*
// @match        *://localhost:18789/*
// @grant        GM_addStyle
// ==/UserScript==

(function() {
    'use strict';

    let enabled = true;
    let timer = null;
    let lastVal = '';

    // 加样式
    GM_addStyle(`
        .auto-send-btn {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 4px 10px !important;
            margin-left: 6px !important;
            border: 2px solid #4CAF50 !important;
            border-radius: 6px !important;
            background: #4CAF50 !important;
            color: white !important;
            font-size: 13px !important;
            font-weight: bold !important;
            cursor: pointer !important;
            user-select: none !important;
            min-width: 60px !important;
            transition: all 0.2s !important;
        }
        .auto-send-btn.off {
            background: #999 !important;
            border-color: #999 !important;
        }
    `);

    function findInput() {
        const sel = ['textarea', 'input[type="text"]', '[contenteditable="true"]', '[role="textbox"]'];
        for (const s of sel) {
            const el = document.querySelector(s);
            if (el) return el;
        }
        return null;
    }

    function findSendBtn() {
        const sel = ['button[type="submit"]', '.send-btn', '#send-btn', 'button:last-of-type'];
        for (const s of sel) {
            const el = document.querySelector(s);
            if (el) return el;
        }
        return null;
    }

    function addButton(input) {
        if (document.querySelector('.auto-send-btn')) return;

        const btn = document.createElement('button');
        btn.className = 'auto-send-btn';
        btn.textContent = '⏱ 自动';
        btn.title = '停止输入3秒自动发送 (点击切换)';

        btn.addEventListener('click', () => {
            enabled = !enabled;
            btn.classList.toggle('off', !enabled);
            btn.textContent = enabled ? '⏱ 自动' : '⏸ 暂停';
        });

        // 插到输入框后面
        input.parentElement?.insertBefore(btn, input.nextSibling) ||
        input.insertAdjacentElement('afterend', btn);
    }

    // 监听输入
    function init() {
        const input = findInput();
        if (!input) return setTimeout(init, 1000);

        if (document.querySelector('.auto-send-btn')) return;

        addButton(input);

        input.addEventListener('input', function(e) {
            if (!enabled) return;
            const v = this.value || this.innerText || '';
            if (v === lastVal || !v.trim()) return;
            lastVal = v;
            if (timer) clearTimeout(timer);
            timer = setTimeout(() => {
                const btn = findSendBtn();
                if (btn) btn.click();
                else if (this.form) this.form.requestSubmit();
            }, 3000);
        });
    }

    // 监控DOM变化（SPA兼容）
    new MutationObserver(() => {
        if (!document.querySelector('.auto-send-btn')) {
            const input = findInput();
            if (input) addButton(input);
        }
    }).observe(document.body, { childList: true, subtree: true });

    init();
})();
