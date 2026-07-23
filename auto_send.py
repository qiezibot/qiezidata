# -*- coding: utf-8 -*-
"""
OpenClaw 自动发送 v3
用 ctypes 直接发送键盘事件，不依赖任何第三方库
"""
import time
import ctypes
import threading

user32 = ctypes.windll.user32
VK_RETURN = 0x0D
KEYEVENTF_KEYUP = 0x0002

def press_enter():
    """发送 Enter 键"""
    user32.keybd_event(VK_RETURN, 0, 0, 0)  # 按下
    time.sleep(0.05)
    user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)  # 松开

running = True
last_key_time = time.time()

# Windows 键盘钩子（需要管理员权限）
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100

def hook_proc(nCode, wParam, lParam):
    global last_key_time
    if nCode >= 0 and wParam == WM_KEYDOWN:
        vk = ctypes.c_uint32.from_address(lParam).value
        # 任何按键（除了Enter本身）都更新时间戳
        if vk != VK_RETURN:
            last_key_time = time.time()
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

CMPFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_uint32))

def main():
    global running, last_key_time
    
    print("[自动发送] 启动中...")
    
    # 安装钩子
    hook_ptr = CMPFUNC(hook_proc)
    hhook = user32.SetWindowsHookExA(WH_KEYBOARD_LL, hook_ptr,
        ctypes.windll.kernel32.GetModuleHandleW(None), 0)
    
    if not hhook:
        print("[自动发送] × 安装钩子失败（重试启动中）")
        # 不用钩子，改用定时轮询（每0.5秒检测输入状态）
        # 这种情况下仅跟踪最后一次按键的大致时间
        return fallback_mode()
    
    print("[自动发送] ✓ 已启动 - 停止输入3秒后自动按 Enter 发送")
    print("[自动发送] 在这个聊天框打字，停3秒不动就会自动发送")
    print("[自动发送] 关掉这个窗口退出")
    
    msg = ctypes.wintypes.MSG()
    while running:
        # 检查是否超时3秒
        elapsed = time.time() - last_key_time
        if elapsed >= 3 and elapsed < 3.5:
            press_enter()
            last_key_time = time.time() + 4  # 防止重复
        # 处理消息队列
        ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
        if ret == 0:
            break
        user32.TranslateMessage(msg)
        user32.DispatchMessageW(msg)
    
    user32.UnhookWindowsHookEx(hhook)
    print("[自动发送] 已退出")

def fallback_mode():
    """不用钩子的降级方案 - 纯轮询检测键盘状态"""
    global running, last_key_time
    
    print("[自动发送] ✓ 已启动（降级模式）- 停止输入3秒后自动按 Enter")
    print("[自动发送] 关掉这个窗口退出")
    
    # 直接轮询：每0.5秒检查一次，用 GetAsyncKeyState 检测按键
    last_active = time.time()
    VK_KEYS = list(range(0x30, 0x5A)) + [0x08, 0x20, 0x25, 0x27]  # 字母数字+退格+空格+方向
    
    while running:
        is_typing = False
        for vk in VK_KEYS:
            if user32.GetAsyncKeyState(vk) & 0x8000:
                is_typing = True
                last_active = time.time()
                break
        
        if not is_typing:
            elapsed = time.time() - last_active
            if elapsed >= 3:
                press_enter()
                last_active = time.time() + 4  # 防止重复
                time.sleep(0.5)
        
        time.sleep(0.3)
    
    print("[自动发送] 已退出")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        running = False
