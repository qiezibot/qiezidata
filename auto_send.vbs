Set WshShell = CreateObject("WScript.Shell")
Dim lastTime, isEnabled
isEnabled = True
lastTime = Now()

' 系统托盘图标
Dim objShell
Set objShell = CreateObject("Shell.Application")

' 创建消息框提示
WshShell.Popup "自动发送已启动`n`n功能：停止输入3秒自动按Enter发送`n`n开关：按 Ctrl+Shift+A 开启/关闭`n状态：当前已开启", 3, "OpenClaw 自动发送", 64

WshShell.SendKeys "^+{HOME}"
WScript.Sleep 100
WshShell.SendKeys "{DELETE}"
WScript.Sleep 100

Do While True
    ' 检查开关快捷键 Ctrl+Shift+A
    If WshShell.GetAsyncKeyState(65) And WshShell.GetAsyncKeyState(16) And WshShell.GetAsyncKeyState(17) Then
        isEnabled = Not isEnabled
        If isEnabled Then
            WshShell.Popup "自动发送已开启", 1, "OpenClaw", 64
        Else
            WshShell.Popup "自动发送已关闭", 1, "OpenClaw", 48
        End If
        WScript.Sleep 1000
    End If
    
    Dim diff
    diff = DateDiff("s", lastTime, Now())
    
    If isEnabled Then
        ' 检测键盘是否按下
        Dim isPressed
        isPressed = False
        Dim keys
        keys = Array(8, 9, 13, 32, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, _
                     65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90)
        For Each k In keys
            If WshShell.GetAsyncKeyState(k) Then
                isPressed = True
                Exit For
            End If
        Next
        If isPressed Then
            lastTime = Now()
        End If
        
        If diff >= 3 Then
            WshShell.SendKeys "{ENTER}"
            lastTime = DateAdd("s", -10, Now())
        End If
    End If
    
    WScript.Sleep 300
Loop
