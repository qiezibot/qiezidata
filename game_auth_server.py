# -*- coding: utf-8 -*-
"""
游戏账号授权管理系统 - 微信扫码授权登录管理
独立服务，不依赖茄子数据库
支持：微信 token 存储、游戏账号管理、登录记录
"""
import os, secrets, hashlib, json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Body, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

DATABASE_URL = os.environ.get('DATABASE_URL', '')
use_pg = bool(DATABASE_URL) and not DATABASE_URL.startswith('sqlite')
PORT = int(os.environ.get('PORT', '8001'))
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
os.makedirs(DATA_DIR, exist_ok=True)
# 微信开放平台配置（后续填入真实值）
WX_APPID = os.environ.get('WX_APPID', '')
WX_SECRET = os.environ.get('WX_SECRET', '')

app = FastAPI(title='Game Auth Manager', version='1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ===== Database =====
db_pool = None
DB_PATH = os.path.join(DATA_DIR, 'game_auth.db')
_sqlite_conn = None

def _get_sqlite():
    global _sqlite_conn
    if _sqlite_conn is None:
        import sqlite3
        _sqlite_conn = sqlite3.connect(DB_PATH)
        _sqlite_conn.row_factory = sqlite3.Row
    return _sqlite_conn


async def init_db():
    global db_pool
    if use_pg:
        import asyncpg
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        async with db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS game_accounts (
                    id SERIAL PRIMARY KEY,
                    game VARCHAR(64) NOT NULL DEFAULT 'cf',
                    account_name VARCHAR(255) NOT NULL DEFAULT '',
                    remark VARCHAR(512) DEFAULT '',
                    status VARCHAR(16) NOT NULL DEFAULT 'idle',
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    last_used_at TIMESTAMP,
                    owner VARCHAR(128) DEFAULT ''
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS wx_tokens (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER NOT NULL REFERENCES game_accounts(id) ON DELETE CASCADE,
                    access_token TEXT DEFAULT '',
                    refresh_token TEXT DEFAULT '',
                    openid VARCHAR(128) DEFAULT '',
                    unionid VARCHAR(128) DEFAULT '',
                    scope VARCHAR(512) DEFAULT '',
                    expires_at TIMESTAMP,
                    refresh_expires_at TIMESTAMP,
                    wx_nickname VARCHAR(128) DEFAULT '',
                    wx_avatar VARCHAR(512) DEFAULT '',
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER NOT NULL REFERENCES game_accounts(id) ON DELETE CASCADE,
                    session_key TEXT DEFAULT '',
                    session_data JSONB DEFAULT '{}',
                    device_id VARCHAR(128) DEFAULT '',
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS game_use_logs (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER NOT NULL REFERENCES game_accounts(id) ON DELETE CASCADE,
                    action VARCHAR(32) NOT NULL,
                    client_id VARCHAR(128) DEFAULT '',
                    client_ip VARCHAR(64) DEFAULT '',
                    detail TEXT DEFAULT '',
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            ''')
    else:
        conn = _get_sqlite()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS game_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT NOT NULL DEFAULT 'cf',
                account_name TEXT NOT NULL DEFAULT '',
                remark TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'idle',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_used_at TEXT,
                owner TEXT DEFAULT ''
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS wx_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                access_token TEXT DEFAULT '',
                refresh_token TEXT DEFAULT '',
                openid TEXT DEFAULT '',
                unionid TEXT DEFAULT '',
                scope TEXT DEFAULT '',
                expires_at TEXT,
                refresh_expires_at TEXT,
                wx_nickname TEXT DEFAULT '',
                wx_avatar TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES game_accounts(id) ON DELETE CASCADE
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                session_key TEXT DEFAULT '',
                session_data TEXT DEFAULT '{}',
                device_id TEXT DEFAULT '',
                expires_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES game_accounts(id) ON DELETE CASCADE
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS game_use_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                client_id TEXT DEFAULT '',
                client_ip TEXT DEFAULT '',
                detail TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES game_accounts(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()


@app.on_event('startup')
async def startup():
    await init_db()


# ===== Helpers =====

def _now():
    return datetime.utcnow()

def _now_str():
    return _now().isoformat()

def _hash(s):
    return hashlib.sha256((s + SECRET_KEY).encode()).hexdigest()


def _pg_to_sqlite(sql):
    """转换 PG 的 $1,$2 到 sqlite 的 ?（确保 $11 不被误替换为 ?1?1）"""
    import re
    def replacer(m):
        return '?'
    return re.sub(r'\$(\d+)', replacer, sql)

async def db_fetch(sql, *params):
    if use_pg:
        import asyncpg
        async with db_pool.acquire() as conn:
            return await conn.fetch(sql, *params)
    else:
        conn = _get_sqlite()
        return conn.execute(_pg_to_sqlite(sql), params).fetchall()

async def db_fetchrow(sql, *params):
    if use_pg:
        import asyncpg
        async with db_pool.acquire() as conn:
            return await conn.fetchrow(sql, *params)
    else:
        conn = _get_sqlite()
        return conn.execute(_pg_to_sqlite(sql), params).fetchone()

async def db_execute(sql, *params):
    if use_pg:
        async with db_pool.acquire() as conn:
            return await conn.execute(sql, *params)
    else:
        conn = _get_sqlite()
        cur = conn.execute(_pg_to_sqlite(sql), params)
        conn.commit()
        return cur

async def db_fetchval(sql, *params):
    if use_pg:
        import asyncpg
        async with db_pool.acquire() as conn:
            return await conn.fetchval(sql, *params)
    else:
        conn = _get_sqlite()
        row = conn.execute(_pg_to_sqlite(sql), params).fetchone()
        return row[0] if row else None

def _row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat()
    return d


# ===== API: 游戏账号管理 =====

@app.get('/api/accounts')
async def ga_list(
    game: str = Query(''),
    status: str = Query(''),
    search: str = Query(''),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """获取游戏账号列表"""
    conditions = []
    params = []
    if game:
        conditions.append(f"game = ${len(params)+1}")
        params.append(game)
    if status:
        conditions.append(f"status = ${len(params)+1}")
        params.append(status)
    if search:
        conditions.append(f"(account_name ILIKE ${len(params)+1} OR remark ILIKE ${len(params)+2})")
        params.append(f'%{search}%')
        params.append(f'%{search}%')
    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    rows = await db_fetch(f'SELECT * FROM game_accounts {where} ORDER BY updated_at DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}', *params, limit, offset)
    total_params = params[:-2]
    total = await db_fetchval(f'SELECT COUNT(*) FROM game_accounts {where}', *total_params) if total_params else \
        await db_fetchval('SELECT COUNT(*) FROM game_accounts')
    return {'ok': True, 'total': total, 'data': [_row_to_dict(r) for r in rows]}


@app.post('/api/accounts')
async def ga_create(data: dict = Body(...)):
    """添加游戏账号"""
    game = data.get('game', 'cf')
    account_name = data.get('account_name', '')
    remark = data.get('remark', '')
    owner = data.get('owner', '')
    now = _now_str() if not use_pg else _now()

    if use_pg:
        aid = await db_fetchval(
            'INSERT INTO game_accounts (game,account_name,remark,status,created_at,updated_at,owner) VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id',
            game, account_name, remark, 'idle', now, now, owner
        )
    else:
        await db_execute(
            'INSERT INTO game_accounts (game,account_name,remark,status,created_at,updated_at,owner) VALUES ($1,$2,$3,$4,$5,$6,$7)',
            game, account_name, remark, 'idle', now, now, owner
        )
        aid = await db_fetchval('SELECT last_insert_rowid()')
    return {'ok': True, 'id': aid, 'msg': '账号已添加'}


@app.get('/api/accounts/{aid}')
async def ga_get(aid: int):
    """获取单个账号详情（含微信 token + 最新 session）"""
    row = await db_fetchrow('SELECT * FROM game_accounts WHERE id=$1', aid)
    if not row:
        raise HTTPException(404, '账号不存在')
    d = _row_to_dict(row)
    # 查微信 token
    wx = await db_fetchrow('SELECT * FROM wx_tokens WHERE account_id=$1', aid)
    if wx:
        wd = _row_to_dict(wx)
        if wd.get('access_token'):
            wd['access_token'] = wd['access_token'][:20] + '...'
        if wd.get('refresh_token'):
            wd['refresh_token'] = wd['refresh_token'][:20] + '...'
        d['wx_auth'] = wd
    # 查最新 session
    sess = await db_fetchrow('SELECT * FROM game_sessions WHERE account_id=$1 ORDER BY created_at DESC LIMIT 1', aid)
    if sess:
        d['last_session'] = _row_to_dict(sess)
    return {'ok': True, 'data': d}


@app.put('/api/accounts/{aid}')
async def ga_update(aid: int, data: dict = Body(...)):
    """更新账号信息"""
    fields = []
    params = []
    for key in ['game', 'account_name', 'remark', 'status', 'owner']:
        if key in data:
            fields.append(f"{key} = ${len(params)+1}")
            params.append(data[key])
    if not fields:
        raise HTTPException(400, '没有要更新的字段')
    now = _now_str() if not use_pg else _now()
    fields.append(f"updated_at = ${len(params)+1}")
    params.append(now)
    params.append(aid)
    await db_execute(f'UPDATE game_accounts SET {", ".join(fields)} WHERE id = ${len(params)}', *params)
    return {'ok': True, 'msg': '已更新'}


@app.delete('/api/accounts/{aid}')
async def ga_delete(aid: int):
    """删除账号"""
    await db_execute('DELETE FROM game_accounts WHERE id=$1', aid)
    return {'ok': True, 'msg': '已删除'}


# ===== API: 微信授权 Token 管理 =====

@app.post('/api/accounts/{aid}/wx-token')
async def ga_save_wx_token(aid: int, data: dict = Body(...)):
    """保存微信授权 token（安卓端扫码后传给后台）"""
    exists = await db_fetchval('SELECT COUNT(*) FROM game_accounts WHERE id=$1', aid)
    if not exists:
        raise HTTPException(404, '账号不存在')

    access_token = data.get('access_token', '')
    refresh_token = data.get('refresh_token', '')
    openid = data.get('openid', '')
    unionid = data.get('unionid', '')
    scope = data.get('scope', '')
    expires_in = data.get('expires_in', 7200)
    refresh_expires_in = data.get('refresh_expires_in', 2592000)
    wx_nickname = data.get('wx_nickname', '')
    wx_avatar = data.get('wx_avatar', '')
    now = _now()
    now_str = _now_str()
    expires_at = (now + timedelta(seconds=expires_in)).isoformat() if not use_pg else (now + timedelta(seconds=expires_in))
    refresh_expires_at = (now + timedelta(seconds=refresh_expires_in)).isoformat() if not use_pg else (now + timedelta(seconds=refresh_expires_in))
    now_for_pg = now

    old = await db_fetchrow('SELECT id FROM wx_tokens WHERE account_id=$1', aid)
    if old:
        await db_execute(
            'UPDATE wx_tokens SET access_token=$1, refresh_token=$2, openid=$3, unionid=$4, scope=$5, '
            'expires_at=$6, refresh_expires_at=$7, wx_nickname=$8, wx_avatar=$9, updated_at=$10 WHERE account_id=$11',
            access_token, refresh_token, openid, unionid, scope,
            expires_at, refresh_expires_at, wx_nickname, wx_avatar, now_str if not use_pg else now_for_pg, aid
        )
    else:
        await db_execute(
            'INSERT INTO wx_tokens (account_id, access_token, refresh_token, openid, unionid, scope, '
            'expires_at, refresh_expires_at, wx_nickname, wx_avatar, created_at, updated_at) '
            'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)',
            aid, access_token, refresh_token, openid, unionid, scope,
            expires_at, refresh_expires_at, wx_nickname, wx_avatar,
            now_str if not use_pg else now_for_pg,
            now_str if not use_pg else now_for_pg
        )

    # 记录绑定日志
    await db_execute(
        'INSERT INTO game_use_logs (account_id, action, detail, created_at) VALUES ($1,$2,$3,$4)',
        aid, 'bind', f'微信授权绑定: openid={openid}',
        now_str if not use_pg else now_for_pg
    )
    return {'ok': True, 'msg': '微信 token 已保存'}


@app.get('/api/accounts/{aid}/wx-token/valid')
async def ga_check_wx_token(aid: int):
    """检查微信 token 是否有效，尝试自动刷新"""
    row = await db_fetchrow('SELECT * FROM wx_tokens WHERE account_id=$1', aid)
    if not row:
        return {'ok': False, 'valid': False, 'reason': '未绑定微信授权'}
    d = dict(row)
    now = _now()

    # 判断 refresh 是否过期
    refresh_exp = d.get('refresh_expires_at')
    if refresh_exp:
        exp = datetime.fromisoformat(refresh_exp) if isinstance(refresh_exp, str) else refresh_exp
        if exp < now:
            return {'ok': True, 'valid': False, 'reason': '微信授权已过期，需要重新扫码'}

    # access_token 是否有效
    exp = d.get('expires_at')
    if exp:
        exp_dt = datetime.fromisoformat(exp) if isinstance(exp, str) else exp
        if exp_dt > now:
            return {'ok': True, 'valid': True, 'access_token': d['access_token']}

    # access_token 过期，尝试刷新
    if d.get('refresh_token') and WX_APPID and WX_SECRET:
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    'https://api.weixin.qq.com/sns/oauth2/refresh_token',
                    params={
                        'appid': WX_APPID,
                        'grant_type': 'refresh_token',
                        'refresh_token': d['refresh_token']
                    }
                )
                wxr = r.json()
                if 'access_token' in wxr:
                    now_dt = _now()
                    ne = (now_dt + timedelta(seconds=wxr.get('expires_in', 7200))).isoformat() if not use_pg else (now_dt + timedelta(seconds=wxr.get('expires_in', 7200)))
                    nr = wxr.get('refresh_token', d['refresh_token'])
                    nrx = (now_dt + timedelta(seconds=wxr.get('refresh_expires_in', 2592000))).isoformat() if not use_pg else (now_dt + timedelta(seconds=wxr.get('refresh_expires_in', 2592000)))
                    now_s = _now_str() if not use_pg else now_dt
                    await db_execute(
                        'UPDATE wx_tokens SET access_token=$1, refresh_token=$2, expires_at=$3, refresh_expires_at=$4, updated_at=$5 WHERE account_id=$6',
                        wxr['access_token'], nr, ne, nrx, now_s, aid
                    )
                    return {'ok': True, 'valid': True, 'access_token': wxr['access_token']}
                else:
                    return {'ok': True, 'valid': False, 'reason': f'刷新失败: {wxr.get("errmsg", "未知错误")}'}
        except Exception as e:
            return {'ok': True, 'valid': False, 'reason': f'刷新出错: {str(e)}'}

    return {'ok': True, 'valid': False, 'reason': '未配置微信刷新参数'}


@app.post('/api/accounts/{aid}/login')
async def ga_record_login(aid: int, data: dict = Body(...)):
    """记录登录成功"""
    session_key = data.get('session_key', '')
    session_data = data.get('session_data', {})
    device_id = data.get('device_id', '')
    expires_in = data.get('expires_in', 86400)
    now_dt = _now()
    now_str = _now_str()
    expires_at_str = (now_dt + timedelta(seconds=expires_in)).isoformat()
    expires_at_pg = now_dt + timedelta(seconds=expires_in)

    # 存储 session
    if use_pg:
        await db_execute(
            'INSERT INTO game_sessions (account_id, session_key, session_data::jsonb, device_id, expires_at, created_at) VALUES ($1,$2,$3,$4,$5,$6)',
            aid, session_key, json.dumps(session_data, ensure_ascii=False), device_id, expires_at_pg, now_dt
        )
    else:
        await db_execute(
            'INSERT INTO game_sessions (account_id, session_key, session_data, device_id, expires_at, created_at) VALUES ($1,$2,$3,$4,$5,$6)',
            aid, session_key, json.dumps(session_data, ensure_ascii=False), device_id, expires_at_str, now_str
        )

    # 更新账号状态
    await db_execute(
        'UPDATE game_accounts SET status=$1, last_used_at=$2, updated_at=$3 WHERE id=$4',
        'using', now_str if not use_pg else now_dt, now_str if not use_pg else now_dt, aid
    )

    # 记录日志
    await db_execute(
        'INSERT INTO game_use_logs (account_id, action, client_id, detail, created_at) VALUES ($1,$2,$3,$4,$5)',
        aid, 'login', device_id, f'登录成功 device={device_id}',
        now_str if not use_pg else now_dt
    )
    return {'ok': True, 'msg': '登录记录已保存'}


@app.post('/api/accounts/{aid}/logout')
async def ga_record_logout(aid: int, data: dict = Body(...)):
    """记录登出，释放账号"""
    device_id = data.get('device_id', '')
    now_str = _now_str()
    now_dt = _now()

    await db_execute(
        'UPDATE game_accounts SET status=$1, updated_at=$2 WHERE id=$3',
        'idle', now_str if not use_pg else now_dt, aid
    )
    await db_execute(
        'INSERT INTO game_use_logs (account_id, action, client_id, detail, created_at) VALUES ($1,$2,$3,$4,$5)',
        aid, 'logout', device_id, f'登出 device={device_id}',
        now_str if not use_pg else now_dt
    )
    return {'ok': True, 'msg': '账号已释放'}


# ===== API: 使用日志 =====

@app.get('/api/logs')
async def ga_logs(
    account_id: int = Query(0),
    action: str = Query(''),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    conditions = []
    params = []
    if account_id:
        conditions.append(f"l.account_id = ${len(params)+1}")
        params.append(account_id)
    if action:
        conditions.append(f"l.action = ${len(params)+1}")
        params.append(action)
    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    rows = await db_fetch(
        f'SELECT l.*, a.account_name, a.game FROM game_use_logs l LEFT JOIN game_accounts a ON l.account_id=a.id {where} ORDER BY l.created_at DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}',
        *params, limit, offset
    )
    total_params = params[:-2]
    total = await db_fetchval(f'SELECT COUNT(*) FROM game_use_logs {where}', *total_params) if total_params else \
        await db_fetchval('SELECT COUNT(*) FROM game_use_logs')
    return {'ok': True, 'total': total, 'data': [_row_to_dict(r) for r in rows]}


# ===== API: 统计 =====

@app.get('/api/stats')
async def ga_stats():
    total = await db_fetchval('SELECT COUNT(*) FROM game_accounts') or 0
    idle = await db_fetchval("SELECT COUNT(*) FROM game_accounts WHERE status='idle'") or 0
    using = await db_fetchval("SELECT COUNT(*) FROM game_accounts WHERE status='using'") or 0
    banned = await db_fetchval("SELECT COUNT(*) FROM game_accounts WHERE status='banned'") or 0
    wx_bound = await db_fetchval('SELECT COUNT(DISTINCT account_id) FROM wx_tokens') or 0
    today = _now_str()[:10]
    if use_pg:
        today_logins = await db_fetchval(
            "SELECT COUNT(*) FROM game_use_logs WHERE action='login' AND created_at::date = $1::date", today
        ) or 0
    else:
        today_logins = await db_fetchval(
            "SELECT COUNT(*) FROM game_use_logs WHERE action='login' AND created_at LIKE $1", f'{today}%'
        ) or 0
    return {
        'ok': True,
        'data': {
            'total_accounts': total,
            'idle': idle, 'in_use': using, 'banned': banned,
            'wx_bound': wx_bound, 'today_logins': today_logins
        }
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=PORT)
