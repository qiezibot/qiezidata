-- ============================================================================
-- 闲鱼自动客服机器人 v1（懒人精灵版）
-- 功能：自动回复 / 自动上架 / 自动跟单
-- 接入DeepSeek API智能回复
-- ============================================================================

-- ===== 配置区 =====
local CONFIG = {
    -- DeepSeek API
    DEEPSEEK_API_KEY = "sk-your-key-here",
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions",
    
    -- 闲鱼包名
    XIANYU_PACKAGE = "com.taobao.idlefish",
    
    -- 检测间隔（秒）
    CHECK_INTERVAL = 5,
    
    -- 自动上架
    AUTO_RELIST = true,          -- 是否自动重新上架
    RELIST_INTERVAL = 1800,      -- 每30分钟检查一次需重新上架的商品
    MAX_RELIST_COUNT = 50,       -- 每次最多重新上架数量
    
    -- 自动跟单
    AUTO_FOLLOW_ORDER = true,    -- 卖出后是否自动跟单
    FOLLOW_ORDER_DELAY = 60,     -- 卖出后延迟60秒再跟单
    
    -- 关键词回复（不用AI时的备用话术）
    KEYWORD_REPLIES = {
        ["在吗"] = "在的亲，有什么可以帮您的？",
        ["你好"] = "你好呀，有什么想了解的？",
        ["价格"] = "价格已经很优惠了亲，诚心要可以小刀~",
        ["便宜"] = "已经是最低价了亲，品质保证哦~",
        ["包邮"] = "亲，这个价格不包邮哦，但是发顺丰很快的~",
        ["怎么卖"] = "直接拍下就行，有什么问题随时问我~",
        ["实物"] = "实物拍摄，所见即所得~",
        ["质量"] = "质量没问题的亲，不满意可以退~",
        ["退货"] = "支持七天无理由退换货的亲~",
    },
    
    -- 跟单话术（卖出后自动发送）
    FOLLOW_UP_MESSAGE = "亲，感谢您的购买！商品已经打包好了，今天内发出，快递单号出来了会第一时间通知您~如有任何问题随时找我哦！",
    
    -- 自动上架等待时间（秒）
    RELIST_DELAY_PER_ITEM = 3,
}

-- ===== 工具函数 =====

-- 截图
function screenshot()
    return snapShot()
end

-- OCR识别文字（懒人精灵自带OCR）
function ocr_text(img, x, y, w, h)
    if img then
        return ocrText(img, x, y, w, h)
    else
        return ocrText(nil, x, y, w, h)
    end
end

-- 找图
function find_image(img_path, x1, y1, x2, y2, sim)
    sim = sim or 0.8
    local ret = findImg(img_path, x1, y1, x2, y2, sim)
    if ret and #ret > 0 then
        return ret[1]
    end
    return nil
end

-- 点击
function tap(x, y)
    touchDown(0, x, y)
    mSleep(50)
    touchUp(0)
    mSleep(200)
end

-- 输入文字
function input_text(text)
    paste(text)
    mSleep(300)
end

-- 等待并点击
function wait_and_tap(text_or_image, timeout, region)
    timeout = timeout or 10
    local start = os.time()
    while os.time() - start < timeout do
        local img = screenshot()
        local pos = nil
        
        -- 如果是文字，用OCR找
        if type(text_or_image) == "string" and string.len(text_or_image) > 3 then
            local results = ocr_text(img, 0, 0, displayWidth(), displayHeight())
            for _, r in ipairs(results) do
                if string.find(r.text, text_or_image) then
                    pos = {x = r.x + r.w/2, y = r.y + r.h/2}
                    break
                end
            end
        else
            -- 如果是图片路径
            pos = find_image(text_or_image, 0, 0, displayWidth(), displayHeight())
        end
        
        if pos then
            tap(pos.x, pos.y)
            return true
        end
        mSleep(500)
    end
    return false
end

-- ===== DeepSeek AI回复 =====
function get_ai_reply(user_message, product_info)
    local prompt = string.format([[
你是一个闲鱼卖家客服，正在回复买家消息。
商品信息：%s
买家消息：%s

请用亲切、自然的中文回复，不要超过50字。回复要简短礼貌，引导成交。
]], product_info or "未知商品", user_message)

    local headers = {
        ["Content-Type"] = "application/json",
        ["Authorization"] = "Bearer " .. CONFIG.DEEPSEEK_API_KEY
    }
    
    local body = {
        model = "deepseek-chat",
        messages = {
            {role = "system", content = "你是一个闲鱼卖家客服，回复简短亲切，不超过50字。"},
            {role = "user", content = prompt}
        },
        max_tokens = 100,
        temperature = 0.7
    }
    
    local ok, resp = httpPost(CONFIG.DEEPSEEK_API_URL, jsonEncode(body), headers, 10000)
    if ok then
        local data = jsonDecode(resp)
        if data and data.choices and #data.choices > 0 then
            return data.choices[1].message.content
        end
    end
    
    -- AI失败时用关键词匹配
    return keyword_reply(user_message)
end

-- 关键词回复（备用）
function keyword_reply(msg)
    for keyword, reply in pairs(CONFIG.KEYWORD_REPLIES) do
        if string.find(msg, keyword) then
            return reply
        end
    end
    return "亲，有什么可以帮您的？"
end

-- ===== 主功能模块 =====

-- 1. 检测并回复消息
function check_and_reply()
    nLog("[闲鱼Bot] 检查新消息...")
    
    -- 打开闲鱼
    runApp(CONFIG.XIANYU_PACKAGE)
    mSleep(3000)
    
    -- 截图分析当前页面
    local img = screenshot()
    
    -- 检测是否有消息tab/按钮（底部导航栏）
    -- "消息" 按钮通常在底部
    local msg_tab = find_image("res/msg_tab.png", 0, displayHeight()-150, displayWidth(), displayHeight())
    if msg_tab then
        tap(msg_tab.x, msg_tab.y)
        mSleep(2000)
    end
    
    -- 检测未读消息列表
    local results = ocr_text(nil, 0, 0, displayWidth(), displayHeight())
    local unread_count = 0
    
    for _, r in ipairs(results) do
        -- 检测红点/未读标记（实际需要找红点图片）
        -- 简单策略：检测对话列表中的"回复"按钮
        if r.text == "回复" or r.text == "立即回复" then
            tap(r.x, r.y)
            mSleep(1500)
            unread_count = unread_count + 1
            
            -- 获取对方消息
            local chat_results = ocr_text(nil, 0, 0, displayWidth(), displayHeight()/2)
            local last_msg = ""
            for _, cr in ipairs(chat_results) do
                if string.len(cr.text) > 2 then
                    last_msg = cr.text
                end
            end
            
            -- 获取AI回复
            local reply = get_ai_reply(last_msg, "闲鱼商品")
            nLog("[闲鱼Bot] 回复: " .. reply)
            
            -- 输入回复
            -- 找到输入框
            local input_box = find_image("res/input_box.png", 0, displayHeight()-200, displayWidth(), displayHeight())
            if input_box then
                tap(input_box.x, input_box.y)
                mSleep(500)
                input_text(reply)
                mSleep(300)
                -- 点发送
                local send_btn = find_image("res/send_btn.png", 0, 0, displayWidth(), displayHeight())
                if send_btn then
                    tap(send_btn.x, send_btn.y)
                end
                mSleep(1000)
            end
            
            -- 返回消息列表
            -- 点左上角返回
            tap(50, 50)
            mSleep(1500)
        end
    end
    
    if unread_count == 0 then
        nLog("[闲鱼Bot] 没有新消息")
    else
        nLog("[闲鱼Bot] 已回复 " .. unread_count .. " 条消息")
    end
end

-- 2. 自动上架商品
function auto_relist()
    nLog("[闲鱼Bot] 检查需重新上架的商品...")
    
    runApp(CONFIG.XIANYU_PACKAGE)
    mSleep(3000)
    
    -- 进入"我的"页面
    local my_tab = find_image("res/my_tab.png", displayWidth()*0.6, displayHeight()-150, displayWidth(), displayHeight())
    if my_tab then
        tap(my_tab.x, my_tab.y)
    else
        -- 已知底部"我的"大约位置
        tap(displayWidth() * 0.85, displayHeight() - 50)
    end
    mSleep(2000)
    
    -- 找"我发布的"或"我卖出的"
    tap(displayWidth() * 0.5, displayHeight() * 0.3)
    mSleep(2000)
    
    -- 找"重新上架"或"再次上架"按钮
    local relisted = 0
    for i = 1, CONFIG.MAX_RELIST_COUNT do
        local relist_btn = find_image("res/relist_btn.png", 0, 0, displayWidth(), displayHeight())
        if not relist_btn then
            -- OCR找"重新上架"
            local results = ocr_text(nil, 0, 0, displayWidth(), displayHeight())
            local found = false
            for _, r in ipairs(results) do
                if string.find(r.text, "重新上架") or string.find(r.text, "再次上架") or string.find(r.text, "一键上架") then
                    tap(r.x + r.w/2, r.y + r.h/2)
                    mSleep(1000)
                    found = true
                    break
                end
            end
            if not found then
                break  -- 没有更多可上架的商品
            end
        end
        
        relisted = relisted + 1
        nLog("[闲鱼Bot] 已重新上架第 " .. relisted .. " 个商品")
        mSleep(CONFIG.RELIST_DELAY_PER_ITEM * 1000)
        
        -- 确认重新上架
        local confirm_btn = find_image("res/confirm_btn.png", 0, 0, displayWidth(), displayHeight())
        if confirm_btn then
            tap(confirm_btn.x, confirm_btn.y)
            mSleep(1000)
        end
    end
    
    nLog("[闲鱼Bot] 本次共重新上架 " .. relisted .. " 个商品")
end

-- 3. 自动跟单
function auto_follow_order()
    nLog("[闲鱼Bot] 检查待跟单的订单...")
    
    runApp(CONFIG.XIANYU_PACKAGE)
    mSleep(3000)
    
    -- 进入"我的" → "我卖出的"
    tap(displayWidth() * 0.85, displayHeight() - 50)
    mSleep(2000)
    
    -- 找"我卖出的"
    local results = ocr_text(nil, 0, 0, displayWidth(), displayHeight())
    for _, r in ipairs(results) do
        if string.find(r.text, "我卖出的") or string.find(r.text, "卖出的") then
            tap(r.x + r.w/2, r.y + r.h/2)
            break
        end
    end
    mSleep(2000)
    
    -- 找"待发货"标签
    results = ocr_text(nil, 0, 0, displayWidth(), displayHeight())
    local followed = 0
    
    for _, r in ipairs(results) do
        if string.find(r.text, "待发货") or string.find(r.text, "等待发货") then
            -- 点击进入订单详情
            tap(r.x - 100, r.y)  -- 点击左侧商品区域
            mSleep(2000)
            
            -- 点"联系买家"或"发消息"
            local msg_btn = find_image("res/contact_buyer.png", 0, 0, displayWidth(), displayHeight())
            if msg_btn then
                tap(msg_btn.x, msg_btn.y)
                mSleep(1500)
            end
            
            -- 发送跟单消息
            local input_box = find_image("res/input_box.png", 0, displayHeight()-200, displayWidth(), displayHeight())
            if input_box then
                tap(input_box.x, input_box.y)
                mSleep(500)
                input_text(CONFIG.FOLLOW_UP_MESSAGE)
                mSleep(300)
                -- 发送
                local send_btn = find_image("res/send_btn.png", 0, 0, displayWidth(), displayHeight())
                if send_btn then
                    tap(send_btn.x, send_btn.y)
                end
                followed = followed + 1
                nLog("[闲鱼Bot] 已跟单1个订单")
                mSleep(2000)
            end
            
            -- 返回
            tap(50, 50)
            mSleep(1500)
        end
    end
    
    nLog("[闲鱼Bot] 本次共跟单 " .. followed .. " 个订单")
end

-- ===== 主循环 =====
function main()
    nLog("=" .. string.rep("=", 50))
    nLog("  闲鱼自动客服机器人 v1")
    nLog("  " .. os.date("%Y-%m-%d %H:%M:%S"))
    nLog("=" .. string.rep("=", 50))
    
    -- 初始化：获取屏幕分辨率
    local w, h = displayWidth(), displayHeight()
    nLog("[闲鱼Bot] 屏幕分辨率: " .. w .. "x" .. h)
    
    -- 先打开闲鱼
    runApp(CONFIG.XIANYU_PACKAGE)
    mSleep(3000)
    
    local cycle = 0
    local last_relist_time = 0
    
    while true do
        cycle = cycle + 1
        nLog("[闲鱼Bot] === 第 " .. cycle .. " 轮循环 ===")
        
        -- 1. 检查回复消息（每轮都做）
        check_and_reply()
        
        -- 2. 检查自动上架（间隔执行）
        if CONFIG.AUTO_RELIST and (os.time() - last_relist_time) > CONFIG.RELIST_INTERVAL then
            auto_relist()
            last_relist_time = os.time()
        end
        
        -- 3. 检查自动跟单（间隔执行）
        if CONFIG.AUTO_FOLLOW_ORDER and cycle % 6 == 0 then  -- 每6轮跟单一次
            auto_follow_order()
        end
        
        -- 等待下一轮
        nLog("[闲鱼Bot] 等待 " .. CONFIG.CHECK_INTERVAL .. " 秒...")
        mSleep(CONFIG.CHECK_INTERVAL * 1000)
    end
end

-- 启动
main()
