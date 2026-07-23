-- ============================================================================
-- 三角洲行动 - 地图制作工具 (懒人精灵版)
-- 功能：你走一遍，工具自动记录路径 → 生成地图数据 → 用于A*寻路
-- ============================================================================

-- ===== 配置 =====
local CONFIG = {
    -- 地图网格参数
    MAP_NAME = "零号大坝",
    GRID_SIZE = 10,       -- 每个格子代表游戏内约10个坐标单位
    MAP_WIDTH = 600,      -- 游戏地图总宽度（坐标范围）
    MAP_HEIGHT = 600,     -- 游戏地图总高度
    
    -- 录制参数
    RECORD_INTERVAL = 500,  -- 每500ms记录一次位置
    MIN_MOVE_DIST = 5,      -- 至少移动5单位才记录新点
    
    -- 摇杆操作参数
    JOYSTICK_CENTER_X = 150,   -- 摇杆中心X（根据屏幕分辨率调整）
    JOYSTICK_CENTER_Y = 900,   -- 摇杆中心Y
    JOYSTICK_RADIUS = 120,     -- 摇杆拖拽半径
}

-- ===== 地图数据 =====
local map_data = {
    name = CONFIG.MAP_NAME,
    grid_size = CONFIG.GRID_SIZE,
    cols = math.floor(CONFIG.MAP_WIDTH / CONFIG.GRID_SIZE),
    rows = math.floor(CONFIG.MAP_HEIGHT / CONFIG.GRID_SIZE),
    obstacles = {},   -- 障碍物集合 "col,row" → true
    walkable = {},    -- 已确认可行走区域
    paths = {},       -- 录制的路径点
    landmarks = {},   -- 地标（撤离点/出生点等）
    empty_zone = {},  -- 空区（确定是空地，不是障碍也不是路）
}

-- ===== 工具函数 =====

function log(msg)
    nLog("[地图工具] " .. msg)
end

function wait(ms)
    mSleep(ms)
end

-- 获取当前游戏坐标（通过位置信息读取）
-- 暂时用OCR读屏幕顶部坐标，失败了用最后已知坐标
local last_known_x = 0
local last_known_y = 0

function get_game_coords()
    local img = snapShot()
    if not img then return nil, nil end
    
    local w, h = displayWidth(), displayHeight()
    
    -- 游戏坐标通常显示在屏幕顶部中间区域
    local results = ocrText(img, w*0.3, 0, w*0.4, h*0.06)
    if results then
        for _, r in ipairs(results) do
            -- 匹配坐标格式如 "(105, 150)" 或 "105,150"
            local x_str, y_str = string.match(r.text, "(%d+)[%s,]+(%d+)")
            if x_str and y_str then
                local x = tonumber(x_str)
                local y = tonumber(y_str)
                if x and y then
                    last_known_x = x
                    last_known_y = y
                    return x, y
                end
            end
        end
    end
    
    return last_known_x, last_known_y
end

-- 坐标 → 网格坐标
function to_grid(game_x, game_y)
    local col = math.floor(game_x / CONFIG.GRID_SIZE)
    local row = math.floor(game_y / CONFIG.GRID_SIZE)
    col = math.max(0, math.min(col, map_data.cols - 1))
    row = math.max(0, math.min(row, map_data.rows - 1))
    return col, row
end

-- 网格键
function grid_key(col, row)
    return col .. "," .. row
end

-- 设置障碍物
function set_obstacle(col, row)
    local key = grid_key(col, row)
    map_data.obstacles[key] = true
    map_data.walkable[key] = nil
end

-- 设置可行走
function set_walkable(col, row)
    local key = grid_key(col, row)
    map_data.walkable[key] = true
    map_data.obstacles[key] = nil
end

-- 保存地图数据到文件
function save_map_data()
    -- 序列化地图数据
    local lines = {}
    lines[#lines+1] = "-- 地图数据: " .. map_data.name
    lines[#lines+1] = "-- 生成时间: " .. os.date("%Y-%m-%d %H:%M:%S")
    lines[#lines+1] = "-- 格子大小: " .. CONFIG.GRID_SIZE .. "单位/格"
    lines[#lines+1] = "-- 地图尺寸: " .. CONFIG.MAP_WIDTH .. "x" .. CONFIG.MAP_HEIGHT
    lines[#lines+1] = "-- 网格: " .. map_data.cols .. "x" .. map_data.rows
    lines[#lines+1] = ""
    lines[#lines+1] = "local MAP_DATA = {"
    lines[#lines+1] = "  name = '" .. map_data.name .. "',"
    lines[#lines+1] = "  grid_size = " .. CONFIG.GRID_SIZE .. ","
    lines[#lines+1] = "  cols = " .. map_data.cols .. ","
    lines[#lines+1] = "  rows = " .. map_data.rows .. ","
    
    -- 障碍物列表
    lines[#lines+1] = "  obstacles = {"
    local obs_count = 0
    for key, _ in pairs(map_data.obstacles) do
        lines[#lines+1] = "    {'" .. key .. "'},"
        obs_count = obs_count + 1
    end
    lines[#lines+1] = "  }, -- " .. obs_count .. "个障碍物"
    
    -- 路径点
    lines[#lines+1] = "  paths = {"
    for _, p in ipairs(map_data.paths) do
        lines[#lines+1] = string.format("    {x=%d, y=%d},", p.x, p.y)
    end
    lines[#lines+1] = "  }, -- " .. #map_data.paths .. "个路径点"
    
    -- 地标
    lines[#lines+1] = "  landmarks = {"
    for _, lm in ipairs(map_data.landmarks) do
        lines[#lines+1] = string.format("    {name='%s', x=%d, y=%d, type='%s'},", lm.name, lm.x, lm.y, lm.type)
    end
    lines[#lines+1] = "  }, -- " .. #map_data.landmarks .. "个地标"
    
    lines[#lines+1] = "}"
    lines[#lines+1] = "return MAP_DATA"
    
    local content = table.concat(lines, "\n")
    local file = io.open(devicePath() .. "/delta_map_" .. map_data.name .. ".lua", "w")
    if file then
        file:write(content)
        file:close()
        log("地图数据已保存到: delta_map_" .. map_data.name .. ".lua")
    else
        log("[错误] 无法保存文件！")
    end
end

-- ===== 摇杆控制 =====

-- 向指定方向滑动摇杆
-- direction: 角度（0=右, 90=下, 180=左, 270=上）
function joystick_swipe(angle, duration_ms)
    local cx = CONFIG.JOYSTICK_CENTER_X
    local cy = CONFIG.JOYSTICK_CENTER_Y
    local r = CONFIG.JOYSTICK_RADIUS
    
    local rad = math.rad(angle)
    local end_x = cx + r * math.cos(rad)
    local end_y = cy + r * math.sin(rad)
    
    touchDown(0, cx, cy)
    wait(50)
    touchMove(0, end_x, end_y)
    wait(duration_ms)
    touchUp(0)
end

-- 摇杆停
function joystick_release()
    touchUp(0)
end

-- ===== 模式1: 路径录制 =====
-- 你手动走，工具自动记录坐标

function mode_record()
    log("===== 路径录制模式 =====")
    log("请手动操作角色开始跑图")
    log("工具会自动记录你的路径")
    log("按音量+停止录制并保存")
    log("")
    
    local path_count = 0
    local prev_x, prev_y = get_game_coords()
    log("起始位置: (" .. (prev_x or 0) .. ", " .. (prev_y or 0) .. ")")
    
    -- 记录起点
    if prev_x and prev_y then
        table.insert(map_data.paths, {x = prev_x, y = prev_y, type = "start"})
        path_count = 1
    end
    
    -- 注册按键监听（音量+键停止）
    local stopped = false
    registerKeyEvent(24, function()  -- 24 = 音量+
        stopped = true
    end)
    
    while not stopped do
        wait(CONFIG.RECORD_INTERVAL)
        
        local x, y = get_game_coords()
        if x and y then
            -- 检查是否移动了足够距离
            local dx = x - (prev_x or x)
            local dy = y - (prev_y or y)
            local dist = math.sqrt(dx*dx + dy*dy)
            
            if dist >= CONFIG.MIN_MOVE_DIST then
                table.insert(map_data.paths, {x = x, y = y})
                path_count = path_count + 1
                
                -- 标记为可行走
                local col, row = to_grid(x, y)
                set_walkable(col, row)
                
                -- 每10个点输出一次状态
                if path_count % 10 == 0 then
                    log(string.format("已记录 %d 个路径点, 当前位置: (%d, %d)", path_count, x, y))
                end
                
                prev_x, prev_y = x, y
            end
        else
            -- 读取坐标失败，尝试备用方法
            log("[警告] 坐标读取失败，尝试再次读取...")
        end
    end
    
    -- 结束录制
    unregisterKeyEvent(24)
    log("")
    log("===== 录制完成 =====")
    log("共记录 " .. path_count .. " 个路径点")
    
    -- 询问是否保存
    local col_count = 0
    for _, _ in pairs(map_data.walkable) do
        col_count = col_count + 1
    end
    log("已标记 " .. col_count .. " 个可行走网格")
    
    save_map_data()
    log("录制完成！")
end

-- ===== 模式2: 障碍物标记 =====
-- 你走到障碍物前，标记不可行走区域

function mode_obstacle_marker()
    log("===== 障碍物标记模式 =====")
    log("走到墙/石头/水边，按音量+标记当前格及其前方")
    log("按音量-切换到下一个标记方向")
    log("按电源键结束标记")
    log("")
    
    local directions = {
        {name = "前方", angle = 270, step = 1},
        {name = "右侧", angle = 0, step = 1},
        {name = "左前方", angle = 315, step = 1},
        {name = "右前方", angle = 225, step = 1},
    }
    
    local dir_index = 1
    local marked = 0
    
    -- 音量+标记当前方向
    registerKeyEvent(24, function()
        local x, y = get_game_coords()
        if not x then
            log("[错误] 无法获取当前坐标")
            return
        end
        
        local col, row = to_grid(x, y)
        local dir = directions[dir_index]
        
        -- 标记当前位置和前方几个格子为障碍物
        for i = 0, 3 do
            local dc, dr = 0, -i  -- 默认朝上（游戏里朝北）
            if dir.angle == 0 then
                dc, dr = i, 0
            elseif dir.angle == 315 then
                dc, dr = i, -i
            elseif dir.angle == 225 then
                dc, dr = -i, -i
            end
            set_obstacle(col + dc, row + dr)
        end
        
        marked = marked + 1
        log(string.format("已标记 %d 个障碍物方向: %s (坐标: %d,%d 网格: %d,%d)", 
            marked, dir.name, x or 0, y or 0, col, row))
    end)
    
    -- 音量-切换方向
    registerKeyEvent(25, function()
        dir_index = dir_index % 4 + 1
        log("切换到: " .. directions[dir_index].name)
    end)
    
    -- 等待直到电源键（按一个未被占用的键）
    log("按音量+标记障碍物，按音量-切换方向")
    log("手动按停止按钮结束...")
    
    -- 简单方案：等10秒后自动结束
    -- 实际使用按懒人精灵的停止按钮
    wait(60000)
    
    unregisterKeyEvent(24)
    unregisterKeyEvent(25)
    
    log("障碍物标记完成，共标记 " .. marked .. " 个方向")
    save_map_data()
end

-- ===== 模式3: 地标标记 =====
-- 在关键位置标记地标

function mode_landmarks()
    log("===== 地标标记模式 =====")
    log("走到地标位置，选择类型：")
    log("  音量+ → 撤离点")
    log("  音量- → 出生点")
    log("  电源键 → 重要位置")
    log("按停止按钮结束")
    log("")
    
    local lm_count = 0
    
    registerKeyEvent(24, function()  -- 音量+
        local x, y = get_game_coords()
        if not x then return end
        table.insert(map_data.landmarks, {name = "撤离点" .. (lm_count+1), x = x, y = y, type = "evac"})
        lm_count = lm_count + 1
        log(string.format("标记撤离点 %d: (%d, %d)", lm_count, x, y))
        wait(500)
    end)
    
    registerKeyEvent(25, function()  -- 音量-
        local x, y = get_game_coords()
        if not x then return end
        table.insert(map_data.landmarks, {name = "出生点" .. (lm_count+1), x = x, y = y, type = "spawn"})
        lm_count = lm_count + 1
        log(string.format("标记出生点 %d: (%d, %d)", lm_count, x, y))
        wait(500)
    end)
    
    wait(120000)  -- 2分钟超时
    unregisterKeyEvent(24)
    unregisterKeyEvent(25)
    
    log("地标标记完成，共 " .. lm_count .. " 个")
    save_map_data()
end

-- ===== 模式4: A*路径测试 =====
-- 测试A*在两个地标之间找路

function mode_test_astar()
    log("===== A*路径测试 =====")
    log("需要先有地图数据文件")
    
    local map_file = devicePath() .. "/delta_map_" .. CONFIG.MAP_NAME .. ".lua"
    local file = io.open(map_file, "r")
    if not file then
        log("[错误] 没有地图数据文件！请先录制路径")
        return
    end
    file:close()
    
    -- 加载地图数据
    local loaded_map = dofile(map_file)
    if not loaded_map then
        log("[错误] 地图数据加载失败")
        return
    end
    
    -- 重建障碍物表
    map_data.obstacles = {}
    for _, obs in ipairs(loaded_map.obstacles) do
        map_data.obstacles[obs[1]] = true
    end
    map_data.landmarks = loaded_map.landmarks or {}
    map_data.cols = loaded_map.cols
    map_data.rows = loaded_map.rows
    map_data.grid_size = loaded_map.grid_size
    
    log("地图 " .. loaded_map.name .. " 加载成功")
    log("网格: " .. map_data.cols .. "x" .. map_data.rows)
    log("障碍物: " .. #loaded_map.obstacles .. "个")
    log("地标: " .. #map_data.landmarks .. "个")
    
    -- 列出所有地标
    log("可用地标：")
    for i, lm in ipairs(map_data.landmarks) do
        log(string.format("  [%d] %s (%d, %d) - %s", i, lm.name, lm.x, lm.y, lm.type))
    end
end

-- ===== 主菜单 =====
function main()
    log("========================================")
    log("  三角洲行动 - 地图制作工具")
    log("========================================")
    log("")
    
    -- 获取屏幕信息
    local w, h = displayWidth(), displayHeight()
    log("屏幕分辨率: " .. w .. "x" .. h)
    
    -- 根据分辨率自动调整摇杆位置
    -- 默认摇杆在左下角，射击在右下角
    CONFIG.JOYSTICK_CENTER_X = math.floor(w * 0.08)
    CONFIG.JOYSTICK_CENTER_Y = math.floor(h * 0.82)
    CONFIG.JOYSTICK_RADIUS = math.floor(math.min(w, h) * 0.06)
    
    log("摇杆位置: (" .. CONFIG.JOYSTICK_CENTER_X .. ", " .. CONFIG.JOYSTICK_CENTER_Y .. ")")
    log("摇杆半径: " .. CONFIG.JOYSTICK_RADIUS)
    log("")
    
    log("选择模式：")
    log("  1 - 路径录制（推荐先做这个）")
    log("  2 - 障碍物标记")
    log("  3 - 地标标记")
    log("  4 - A*路径测试")
    log("")
    log("请在懒人精灵中修改脚本开头的 MODE 变量来切换模式")
    log("")
    log("或直接运行各模式的独立脚本:")
    log("  mode_record() - 路径录制")
    log("  mode_obstacle_marker() - 障碍物标记")
    log("  mode_landmarks() - 地标标记")
    log("  mode_test_astar() - A*测试")
end

-- 默认运行主菜单，根据需要注释/取消注释下面的行
main()
-- mode_record()  -- 路径录制
-- mode_obstacle_marker()  -- 障碍物标记
-- mode_landmarks()  -- 地标标记
-- mode_test_astar()  -- A*测试
