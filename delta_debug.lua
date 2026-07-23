-- ============================================================================
-- 三角洲行动 - 跑刀调试脚本
-- 功能：输出游戏屏幕信息用于定位按钮坐标
-- ============================================================================

-- 输出分隔线
function log_sep(title)
    nLog("")
    nLog("===== " .. title .. " =====")
end

-- 画面截图并保存
function save_debug_screenshot(name)
    local img = snapShot()
    if img then
        saveToAlbum(img, name .. ".png")
        nLog("[截图已保存] " .. name .. ".png (存到相册)")
    end
end

-- 主调试函数
function debug_screen()
    log_sep("屏幕信息")
    
    -- 1. 基本信息
    local w, h = displayWidth(), displayHeight()
    nLog("屏幕分辨率: " .. w .. " x " .. h)
    nLog("屏幕方向: " .. screenDirection())
    nLog("设备ID: " .. deviceId())
    nLog("系统版本: " .. osVersion())
    nLog("")
    
    -- 2. 截图
    log_sep("截取当前画面")
    local img = snapShot()
    if not img then
        nLog("[错误] 截图失败！")
        return
    end
    
    -- 保存截图到相册
    save_debug_screenshot("delta_debug_screen")
    nLog("截图成功！")
    
    -- 3. OCR识别全屏文字
    log_sep("全屏OCR识别")
    local results = ocrText(img)
    if results and #results > 0 then
        nLog("识别到 " .. #results .. " 个文字区域：")
        for i, r in ipairs(results) do
            if r.text and #r.text > 1 then
                nLog(string.format("  [%d] \"%s\" (x=%d y=%d w=%d h=%d)",
                    i, r.text, r.x, r.y, r.w, r.h))
            end
            if i >= 30 then
                nLog("  ... (只显示前30个)")
                break
            end
        end
    else
        nLog("没有识别到文字（或者当前不是游戏画面）")
    end
    
    -- 4. 色彩取样（关键区域）
    log_sep("关键位置颜色取样")
    local check_points = {
        {"中心点", w/2, h/2},
        {"左上角", 10, 10},
        {"右上角", w-10, 10},
        {"左下角", 10, h-10},
        {"右下角", w-10, h-10},
        {"摇杆区", w*0.1, h*0.85},
        {"射击区", w*0.9, h*0.7},
        {"小地图", w*0.92, h*0.08},
        {"底部中间", w/2, h-50},
        {"底部偏左1/3", w*0.33, h-50},
        {"底部偏右1/3", w*0.66, h-50},
    }
    for _, p in ipairs(check_points) do
        local r, g, b = getColor(img, p[2], p[3])
        nLog(string.format("  %s (%.0f, %.0f) → RGB(%d,%d,%d)", p[1], p[2], p[3], r, g, b))
    end
    
    -- 5. 其他常用区域
    log_sep("九宫格区域颜色")
    for y = 1, 3 do
        for x = 1, 3 do
            local px = w * x / 4
            local py = h * y / 4
            local r, g, b = getColor(img, px, py)
            nLog(string.format("  区域(%d,%d) → (%.0f,%.0f) → RGB(%d,%d,%d)", x, y, px, py, r, g, b))
        end
    end
    
    nLog("")
    nLog("========== 调试完成 ==========")
    nLog("截图已保存到相册: delta_debug_screen.png")
end

-- 运行
debug_screen()
