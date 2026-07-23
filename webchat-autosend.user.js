// ==UserScript==
// @name         OpenClaw Webchat 自动发送
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  输入框内容变化后，如果停止输入一段时间，自动点击发送按钮
// @author       AI助手
// @match        *://*/*openclaw*
// @match        *://*/control-ui/*
// @match        *://*/*control*
// @match        *://127.0.0.1:*/*
// @match        *://localhost:*/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    // ====== 配置 ======
    const DELAY_MS = 2000;  // 停止输入后等待 2 秒再自动发送
    const MIN_CHARS = 3;    // 最少输入几个字才触发自动发送
    // =================

    let timer = null;
    let lastText = '';
    let autoSendEnabled = true;

    // 创建浮动开关
    function createToggle() {
        const toggle = document.createElement('div');
        toggle.id = 'openclaw-auto-send-toggle';
        toggle.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            z-index: 99999;
            background: #10a37f;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 13px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            font-family: system-ui, -apple-system, sans-serif;
            transition: all 0.2s;
            user-select: none;
        `;
        toggle.textContent = '🔊 自动发送 开';
        toggle.onclick = function () {
            autoSendEnabled = !autoSendEnabled;
            toggle.textContent = autoSendEnabled ? '🔊 自动发送 开' : '🔇 自动发送 关';
            toggle.style.background = autoSendEnabled ? '#10a37f' : '#666';
        };
        document.body.appendChild(toggle);
    }

    function findInput() {
        // 优先找常见的输入框
        const selectors = [
            'textarea[placeholder*="输入"]',
            'textarea[placeholder*="发送"]',
            'textarea[placeholder*="消息"]',
            'textarea[placeholder*="Message"]',
            'textarea:not([disabled])',
            '[contenteditable="true"]',
            'div[data-slate-editor]',
            '.ProseMirror',
        ];
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) return el;
        }
        return null;
    }

    function findSendButton() {
        const selectors = [
            'button[aria-label*="发送"]',
            'button[aria-label*="Send"]',
            'button:has(svg)',
            'button:last-child',
            '[type="submit"]',
            'button:not([disabled]):not([class*="hidden"])',
        ];
        // 优先找输入框旁边的按钮
        const input = findInput();
        if (input) {
            const parent = input.closest('div') || input.parentElement;
            if (parent) {
                const btns = parent.querySelectorAll('button, [role="button"]');
                for (const btn of btns) {
                    if (btn.offsetWidth > 20 && btn.offsetHeight > 20) {
                        return btn;
                    }
                }
            }
        }
        // 兜底: 找所有可见按钮
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el && el.offsetWidth > 0) return el;
        }
        return null;
    }

    function getText(el) {
        if (!el) return '';
        if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
            return el.value.trim();
        }
        return el.textContent.trim();
    }

    function doSend() {
        const btn = findSendButton();
        if (btn) {
            btn.click();
            return true;
        }
        // 兜底: 按 Enter
        const input = findInput();
        if (input) {
            const evt = new KeyboardEvent('keydown', {
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                which: 13,
                bubbles: true,
                cancelable: true,
            });
            input.dispatchEvent(evt);
            return true;
        }
        return false;
    }

    function onInputChange() {
        if (!autoSendEnabled) return;

        const input = findInput();
        const text = getText(input);

        if (text === lastText) return;
        lastText = text;

        if (text.length < MIN_CHARS) {
            if (timer) {
                clearTimeout(timer);
                timer = null;
            }
            return;
        }

        // 清除之前的定时器
        if (timer) {
            clearTimeout(timer);
        }

        // 设置新的定时器
        timer = setTimeout(() => {
            if (text.length >= MIN_CHARS) {
                doSend();
                lastText = '';
            }
            timer = null;
        }, DELAY_MS);
    }

    // 初始化
    function init() {
        // 等待 DOM 加载
        if (document.body) {
            createToggle();
            const input = findInput();
            if (input) {
                input.addEventListener('input', onInputChange);
                input.addEventListener('keyup', onInputChange);
                input.addEventListener('compositionend', onInputChange);
                console.log('🔊 OpenClaw 自动发送已启动（2秒无输入自动发）');
            } else {
                // 如果还没渲染出来，继续等
                const observer = new MutationObserver(() => {
                    const el = findInput();
                    if (el && !el._autoSendBound) {
                        el._autoSendBound = true;
                        el.addEventListener('input', onInputChange);
                        el.addEventListener('keyup', onInputChange);
                        el.addEventListener('compositionend', onInputChange);
                        observer.disconnect();
                        console.log('🔊 OpenClaw 自动发送已启动');
                    }
                });
                observer.observe(document.body, { childList: true, subtree: true });
            }
        } else {
            setTimeout(init, 500);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
