-- ============================================
-- TG Cloud API 云端数据库模块
-- 懒人精灵专用，无需 Python 环境
-- 依赖：TG Cloud API 服务（已运行在 localhost:8888）
-- 用法：dofile("tg_cloud_api.lua")
-- ============================================

-- 配置
local API_HOST = "http://localhost:8888"

-- PowerShell 调用封装
function tg_request(method, api_path, body)
    local ps_cmd
    if method == "GET" then
        ps_cmd = string.format(
            'powershell -Command "Invoke-RestMethod -Uri %s%s -UseBasicParsing -TimeoutSec 10"',
            API_HOST, api_path
        )
    else
        -- POST / DELETE 需要转义 JSON
        local escaped_body = string.gsub(body or "{}", '"', '\\"')
        ps_cmd = string.format(
            'powershell -Command "Invoke-RestMethod -Uri %s%s -Method %s -Body ''%s'' -ContentType ''application/json'' -UseBasicParsing -TimeoutSec 10"',
            API_HOST, api_path, method, body or "{}"
        )
    end
    return ps_cmd
end

-- 执行并获取结果（返回字符串）
function tg_exec(method, api_path, body)
    local cmd = tg_request(method, api_path, body)
    local code, out, err = luaext.execute(cmd)
    if code ~= 0 then
        log_error("TG API 调用失败: " .. (err or "无输出"))
        return nil
    end
    return out
end

-- ============================================
-- 公开 API
-- ============================================

-- 检查服务状态
function tg_status()
    local ret = tg_exec("GET", "/status")
    if ret then
        log_info("TG云存储状态: 在线")
        return true
    end
    log_error("TG云存储状态: 离线，请确保 tg_api_server.py 正在运行")
    return false
end

-- ============================================
-- 键值存储（最常用）
-- ============================================

-- 存数据
-- key: 键名（建议加前缀，如 "user_10086"）
-- value: 值（可以是字符串、数字、JSON）
function tg_set(key, value)
    local body = string.format('{"key":"%s","value":%s}', key, tostring(value))
    return tg_exec("POST", "/kv", body)
end

-- 取数据
function tg_get(key)
    return tg_exec("GET", "/kv/" .. key)
end

-- 删数据
function tg_del(key)
    return tg_exec("DELETE", "/kv/" .. key)
end

-- ============================================
-- 笔记存储（长文本）
-- ============================================

-- 存笔记
function tg_note(title, content, tags)
    local tags_json = "[]"
    if tags then
        local parts = {}
        for _, t in ipairs(tags) do
            table.insert(parts, '"' .. t .. '"')
        end
        tags_json = "[" .. table.concat(parts, ",") .. "]"
    end
    -- 转义内容中的引号
    local safe_content = string.gsub(content, '"', '\\"')
    local safe_title = string.gsub(title or "", '"', '\\"')
    local body = string.format(
        '{"title":"%s","content":"%s","tags":%s}',
        safe_title, safe_content, tags_json
    )
    return tg_exec("POST", "/note", body)
end

-- 查看所有笔记
function tg_notes()
    return tg_exec("GET", "/notes")
end

-- 删笔记
function tg_note_del(id)
    return tg_exec("DELETE", "/note/" .. tostring(id))
end

-- ============================================
-- 文件上传
-- ============================================

-- 上传文件到云端
-- file_path: 本地文件完整路径
-- description: 描述文字（可选）
function tg_upload(file_path, description)
    local safe_path = string.gsub(file_path, "\\", "\\\\")
    local desc = description or ""
    local body = string.format(
        '{"file_path":"%s","description":"%s"}',
        safe_path, desc
    )
    return tg_exec("POST", "/file", body)
end

-- 查看所有已上传文件
function tg_files()
    return tg_exec("GET", "/files")
end

-- ============================================
-- 业务场景函数
-- ============================================

-- 保存用户数据
function tg_save_user(uid, user_data_json)
    return tg_set("user_" .. tostring(uid), user_data_json)
end

-- 读取用户数据
function tg_load_user(uid)
    return tg_get("user_" .. tostring(uid))
end

-- 保存运行日志
function tg_save_log(log_content)
    local time = os.date("%Y-%m-%d %H:%M:%S")
    return tg_note("运行日志 " .. time, log_content, {"log"})
end

-- 保存统计数据（计数器类）
function tg_increment(key)
    local val = tg_get(key)
    local count = 1
    if val then
        -- 尝试解析
        local _, _, num = string.find(val, '"value":(%d+)')
        if num then count = tonumber(num) + 1 end
    end
    tg_set(key, tostring(count))
    return count
end

-- ============================================
-- 初始化（在脚本开头调用）
-- ============================================
log_info("正在连接 TG 云存储...")
if tg_status() then
    log_info("TG 云存储就绪 ✅")
else
    log_warn("TG 云存储未连接，数据将仅保存本地")
end
