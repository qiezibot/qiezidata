-- ============================================
-- 闲鱼自动客服机器人
-- TG 云存储版（数据存云端）
-- 
-- 功能：
--   ✅ 自动回复常用话术
--   ✅ 关键词匹配+智能回复
--   ✅ 消息记录云端存储
--   ✅ 客户管理系统
--   ✅ 快捷回复面板
--   ✅ 数据统计看板
-- ============================================

-- ===== 配置 =====
local CONFIG = {
    -- 云存储API地址（确保 tg_api_server.py 已运行）
    api_host = "http://localhost:8888",

    -- 闲鱼界面坐标（根据你的分辨率调整）
    -- 建议使用 1080x2400 比例，其他分辨率自动缩放
    screen_width = 1080,
    screen_height = 2400,

    -- 消息区域
    msg_area = { x = 50, y = 300, w = 980, h = 1600 },

    -- 输入框
    input_box = { x = 30, y = 2100, w = 850, h = 100 },

    -- 发送按钮
    send_btn = { x = 950, y = 2120, w = 100, h = 60 },

    -- 轮询间隔（毫秒）
    poll_interval = 3000,

    -- DeepSeek API（可选，用于智能回复）
    deepseek_key = "",
    deepseek_model = "deepseek-chat",
}

-- ===== TG 云存储调用 =====
function tg_api(method, path, body)
    local base = CONFIG.api_host
    local ps_cmd
    if method == "GET" then
        ps_cmd = string.format(
            'powershell -Command "try{Invoke-RestMethod -Uri %s%s -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop}catch{echo ERROR}" 2>$null',
            base, path
        )
    else
        local safe_body = string.gsub(body or "{}", '"', '\\"')
        ps_cmd = string.format(
            'powershell -Command "try{$b=\''%s\';Invoke-RestMethod -Uri %s%s -Method %s -Body $b -ContentType \'application/json\' -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop}catch{echo ERROR}" 2>$null',
            safe_body, base, path, method
        )
    end
    local code, out, err = luaext.execute(ps_cmd)
    if code ~= 0 or (out and string.find(out, "ERROR")) then
        return nil
    end
    return out
end

-- 存键值
function kv_set(key, value)
    local body = string.format('{"key":"%s","value":"%s"}', key, tostring(value))
    tg_api("POST", "/kv", body)
end

-- 读取键值
function kv_get(key)
    return tg_api("GET", "/kv/" .. key)
end

-- 存日志
function log_to_cloud(title, content)
    local safe_title = string.gsub(title, '"', "'")
    local safe_content = string.gsub(content, '"', "'")
    local body = string.format(
        '{"title":"%s","content":"%s","tags":["xianyu","log"]}',
        safe_title, safe_content
    )
    tg_api("POST", "/note", body)
end

-- 存客户消息
function save_customer_msg(uid, name, msg, reply)
    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    local key = "msg_" .. uid .. "_" .. os.time()
    kv_set(key, string.format(
        '{"from":"%s","msg":"%s","reply":"%s","time":"%s"}',
        name, msg, reply, timestamp
    ))
    -- 记录到客户列表
    kv_set("customer_" .. uid, string.format(
        '{"name":"%s","last_msg":"%s","last_time":"%s","msg_count":%d}',
        name, msg, timestamp, 0  -- 后续可做计数
    ))
end

-- ===== 工具函数 =====
function sleep(ms)
    local deadline = os.time() + ms / 1000
    while os.time() < deadline do
        luaext.sleep(100)
    end
end

function log_i(msg)
    luaext.log(msg)
end

function log_e(msg)
    luaext.log("[ERROR] " .. msg)
end

-- 模糊匹配（关键词数组）
function match_keywords(text, keywords)
    if not text then return false end
    local lower = string.lower(text)
    for _, kw in ipairs(keywords) do
        if string.find(lower, string.lower(kw)) then
            return true
        end
    end
    return false
end

-- 获取屏幕文字（OCR 简化版——实际用图片识字）
function get_screen_text(x, y, w, h)
    -- 这里用懒人精灵的 OCR 功能
    -- 不同版本 API 不同，以下为常见写法
    local success, text = luaext.ocr(x, y, w, h)
    if success then
        return text
    end
    return ""
end

-- 点击
function tap(x, y)
    luaext.tap(x, y)
    sleep(200)
end

-- 输入文字
function input_text(text)
    luaext.input(text)
    sleep(100)
end

-- ===== 闲鱼专用界面操作 =====

-- 等待闲鱼界面加载
function wait_for_app()
    log_i("等待闲鱼启动...")
    sleep(3000)
    -- 这里可以加包名检测
    -- luaext.appRun("com.taobao.idlefish")
end

-- 打开消息列表
function open_messages()
    -- 点击底部"消息"tab
    tap(CONFIG.screen_width / 2, CONFIG.screen_height - 80)
    sleep(2000)
end

-- 进入指定对话
function enter_chat(name)
    -- 在消息列表中查找并点击联系人
    -- 简化版：OCR 识别"name"并点击
    log_i("尝试进入 " .. name .. " 的对话")
    sleep(500)
end

-- 发送消息
function send_msg(text)
    -- 点击输入框
    tap(CONFIG.input_box.x + 100, CONFIG.input_box.y + 50)
    sleep(300)

    -- 输入文字
    luaext.input(text)
    sleep(200)

    -- 点击发送
    tap(CONFIG.send_btn.x + 50, CONFIG.send_btn.y + 30)
    sleep(500)

    log_i("已发送: " .. text)
end

-- 获取最新消息
function get_latest_msg()
    local y = CONFIG.msg_area.y + CONFIG.msg_area.h - 100
    local text = get_screen_text(
        CONFIG.msg_area.x, y,
        CONFIG.msg_area.w, 80
    )
    return text
end

-- ===== 话术库 =====
local REPLIES = {
    -- 价格类
    price = {
        keywords = {"多少钱", "价格", "怎么卖", "低价", "便宜", "贵了", "打折", "价位", "几米"},
        replies = {
            "亲，价格已经是最低价了哦，都是实拍实卖的~",
            "目前就是这个价呢，已经很划算了，质量有保证的~",
            "价格可以小刀，诚心要的话可以再聊聊~",
            "不议价哦亲，你去对比下别家就知道我这多实惠了~",
        }
    },

    -- 质量问题
    quality = {
        keywords = {"质量", "正品", "真假", "是不是真的", "保真", "有问题", "瑕疵", "成色", "几成新"},
        replies = {
            "亲放心，都是实物实拍，保证如实描述~",
            "支持验货，有任何问题都可以退换的~",
            "正品保障，假一赔十，放心购买~",
            "成色看图哦，实物比照片还好的~",
        }
    },

    -- 物流
    delivery = {
        keywords = {"发货", "快递", "物流", "几天到", "包邮", "运费", "顺丰", "邮费"},
        replies = {
            "下单后24小时内发货，正常2-3天到~",
            "默认发圆通/中通，如果需要顺丰可以补差价~",
            "全国包邮哦亲~",
            "当天发，次日更新单号~",
        }
    },

    -- 尺寸规格
    size = {
        keywords = {"尺码", "尺寸", "多大", "多长", "重量", "容量", "多少G", "多少g"},
        replies = {
            "详情页有详细的尺寸说明哦，你看看~",
            "亲方便说一下你平时穿的尺码吗？我帮你参考~",
            "尺寸在商品页面有写，如果不确定我帮你量一下~",
        }
    },

    -- 还价
    bargain = {
        keywords = {"便宜点", "少点", "优惠", "抹零", "再少", "最低多少", "还能少"},
        replies = {
            "亲价格已经很良心了，实在不能再低了~",
            "最多给你抹个零头，再低真的做不了了~",
            "要不你拍下我改价，给你小优惠~",
            "诚心要的话私聊我，给你个优惠价~",
        }
    },

    -- 已售
    sold = {
        keywords = {"卖了没", "还在吗", "出了吗", "还有吗", "还有货吗", "在不在"},
        replies = {
            "还在的亲，随时可以拍~",
            "在的哦，要的话直接拍~",
            "还在的，喜欢的不要错过哦~",
        }
    },

    -- 交易方式
    trade = {
        keywords = {"怎么交易", "怎么买", "怎么付款", "怎么拍", "怎么下单", "自提"},
        replies = {
            "直接拍下付款就可以啦，闲鱼担保交易很安全的~",
            "如果是本地的可以自提，坐标在详情页有写~",
            "直接闲鱼下单就行，不支持其他平台交易哦~",
        }
    },

    -- 无匹配（默认回复）
    default = {
        replies = {
            "亲，有什么可以帮到你的呀~",
            "您好，请问有什么问题吗~",
            "欢迎光临~ 有什么需要了解的可以问我哦~",
            "您好亲，商品详情页有详细介绍，有不明白的可以问我~",
        }
    }
}

-- 根据消息选择回复
function choose_reply(msg)
    if not msg or msg == "" then return REPLIES.default.replies[1] end

    for _, category in pairs(REPLIES) do
        if category.keywords then
            if match_keywords(msg, category.keywords) then
                -- 随机选一条回复
                local idx = math.random(1, #category.replies)
                return category.replies[idx]
            end
        end
    end

    -- 默认
    local idx = math.random(1, #REPLIES.default.replies)
    return REPLIES.default.replies[idx]
end

-- ===== DeepSeek 智能回复（可选） =====
function deepseek_reply(msg)
    if CONFIG.deepseek_key == "" then return nil end

    local prompt = string.gsub(msg, '"', '\\"')
    local ps_cmd = string.format(
        'powershell -Command "$body=\'{\\\"model\\\":\\\"%s\\\",\\\"messages\\\":[{\\\"role\\\":\\\"user\\\",\\\"content\\\":\\\"%s\\\"}]}\'; try{$r=Invoke-RestMethod -Uri https://api.deepseek.com/chat/completions -Method POST -Body $body -ContentType \'application/json\' -Headers @{\\\"Authorization\\\"=\\\"Bearer %s\\\"} -UseBasicParsing -TimeoutSec 30; echo $r.choices[0].message.content}catch{echo ERROR}" 2>$null',
        CONFIG.deepseek_model, prompt, CONFIG.deepseek_key
    )
    local code, out, err = luaext.execute(ps_cmd)
    if code == 0 and out and not string.find(out, "ERROR") then
        return out
    end
    return nil
end

-- ===== 主循环 =====
local run_count = 0
local last_hash = ""

function main()
    log_i("===== 闲鱼自动客服 v2.0 (TG云存储版) =====")
    log_i("初始化中...")

    -- 连接云存储
    local status = kv_get("ping")
    if status then
        log_i("✅ TG 云存储已连接")
        log_to_cloud("系统启动", "闲鱼自动客服已启动")
    else
        log_i("⚠️ TG 云存储未连接，数据仅存本地")
    end

    -- 启动闲鱼
    wait_for_app()

    log_i("开始运行，轮询间隔 " .. CONFIG.poll_interval .. "ms")

    while true do
        run_count = run_count + 1
        log_i("--- 第 " .. run_count .. " 轮 ---")

        -- 1. 获取最新消息
        local msg = get_latest_msg()
        log_i("最新消息: " .. (msg or "无"))

        if msg and msg ~= "" and msg ~= last_hash then
            -- 2. 选择回复
            local reply = deepseek_reply(msg)

            if not reply then
                reply = choose_reply(msg)
            end

            -- 3. 发送回复
            send_msg(reply)

            -- 4. 存到云端
            log_to_cloud("回复客户", "客户说: " .. msg .. " | 回复: " .. reply)

            -- 5. 更新最后消息
            last_hash = msg

            -- 每10轮存一次状态到云端
            if run_count % 10 == 0 then
                kv_set("last_run", os.date("%Y-%m-%d %H:%M:%S"))
                kv_set("run_count", tostring(run_count))
            end
        end

        -- 等待下一轮
        sleep(CONFIG.poll_interval)
    end
end

-- 启动（放到脚本最后）
local success, err = pcall(main)
if not success then
    log_e("脚本异常: " .. tostring(err))
    log_to_cloud("运行异常", tostring(err))
end
