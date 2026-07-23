// auto_send.cs - C# 5 compatible
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace AutoSend
{
    class Program
    {
        [DllImport("user32.dll")]
        static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc callback, IntPtr hMod, uint dwThreadId);

        [DllImport("user32.dll")]
        static extern bool UnhookWindowsHookEx(IntPtr hhk);

        [DllImport("user32.dll")]
        static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("kernel32.dll")]
        static extern IntPtr GetModuleHandle(string lpModuleName);

        [DllImport("user32.dll")]
        static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

        delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

        const int WH_KEYBOARD_LL = 13;
        const int WM_KEYDOWN = 0x0100;
        const int VK_RETURN = 0x0D;
        const int KEYEVENTF_KEYUP = 0x0002;

        static LowLevelKeyboardProc _proc;
        static IntPtr _hookId = IntPtr.Zero;
        static DateTime _lastKeyTime = DateTime.Now;
        static volatile bool _running = true;
        static volatile bool _enabled = true;

        static void Main()
        {
            bool created;
            using (var mutex = new Mutex(true, "AutoSend_OpenClaw", out created))
            {
                if (!created)
                {
                    MessageBox.Show("自动发送已在运行", "AutoSend");
                    return;
                }

                _proc = new LowLevelKeyboardProc(HookCallback);
                _hookId = SetHook(_proc);

                // 快捷键监听线程
                Thread keyThread = new Thread(KeyMonitorLoop);
                keyThread.IsBackground = true;
                keyThread.Start();

                // 定时检测线程
                Thread timerThread = new Thread(TimerLoop);
                timerThread.IsBackground = true;
                timerThread.Start();

                Application.Run();
                _running = false;
                UnhookWindowsHookEx(_hookId);
            }
        }

        static void KeyMonitorLoop()
        {
            while (_running)
            {
                if ((GetAsyncKeyState(0x10) & 0x8000) != 0 && (GetAsyncKeyState(0x70) & 0x8001) != 0)
                {
                    _enabled = !_enabled;
                    MessageBox.Show(_enabled ? "自动发送已开启" : "自动发送已关闭", "AutoSend",
                        MessageBoxButtons.OK, _enabled ? MessageBoxIcon.Information : MessageBoxIcon.Warning);
                    Thread.Sleep(500);
                }
                Thread.Sleep(200);
            }
        }

        static void TimerLoop()
        {
            while (_running)
            {
                if (_enabled)
                {
                    double elapsed = (DateTime.Now - _lastKeyTime).TotalSeconds;
                    if (elapsed >= 3)
                    {
                        keybd_event(VK_RETURN, 0, 0, UIntPtr.Zero);
                        keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, UIntPtr.Zero);
                        _lastKeyTime = DateTime.Now.AddSeconds(-10);
                    }
                }
                Thread.Sleep(200);
            }
        }

        static IntPtr SetHook(LowLevelKeyboardProc proc)
        {
            using (Process curProcess = Process.GetCurrentProcess())
            using (ProcessModule curModule = curProcess.MainModule)
            {
                return SetWindowsHookEx(WH_KEYBOARD_LL, proc,
                    GetModuleHandle(curModule.ModuleName), 0);
            }
        }

        static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0 && wParam == (IntPtr)WM_KEYDOWN)
            {
                _lastKeyTime = DateTime.Now;
            }
            return CallNextHookEx(_hookId, nCode, wParam, lParam);
        }

        [DllImport("user32.dll")]
        static extern short GetAsyncKeyState(int vKey);
    }
}
