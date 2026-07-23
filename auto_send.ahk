; OpenClaw 自动发送脚本
; 检测键盘输入，停止3秒后自动按 Enter 发送
; 适用：OpenClaw控制台、QQ、微信等任意聊天窗口

#Persistent
#NoEnv
#SingleInstance Force
SendMode Input

lastTick := 0
timerActive := false

; 启动3秒计时器
SetTimer, CheckIdle, 200
return

CheckIdle:
    if (timerActive) {
        idle := A_TickCount - lastTick
        if (idle >= 3000) {
            ; 发送 Enter
            SendInput {Enter}
            timerActive := false
            ; 防止重复触发，等4秒后再重新开始计时
            lastTick := A_TickCount
        }
    }
return

; 监听所有键盘输入（任何窗口）
~LButton::
~RButton::
~*a::
~*b::
~*c::
~*d::
~*e::
~*f::
~*g::
~*h::
~*i::
~*j::
~*k::
~*l::
~*m::
~*n::
~*o::
~*p::
~*q::
~*r::
~*s::
~*t::
~*u::
~*v::
~*w::
~*x::
~*y::
~*z::
~*0::
~*1::
~*2::
~*3::
~*4::
~*5::
~*6::
~*7::
~*8::
~*9::
~*BackSpace::
~*Space::
~*Delete::
    timerActive := true
    lastTick := A_TickCount
return
