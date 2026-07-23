// logs/logger.cjs - Node.js 日志工具
// 用法: const log = require('./logs/logger.cjs')
//       log.info('QQBOT', '机器人已连接')
//       log.error('STT', '语音识别失败', err)

const fs = require('fs')
const path = require('path')

const LOG_DIR = __dirname
const LEVELS = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 }

function timestamp() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function write(service, level, message, err) {
  const line = `[${timestamp()}] [${level}] [${service}] ${message}${err ? '\n  ' + (err.stack || err.message || err) : ''}\n`
  const logFile = path.join(LOG_DIR, `${service.toLowerCase()}.log`)

  try {
    fs.appendFileSync(logFile, line, 'utf8')
  } catch(e) {
    // 写不了日志就用 console
    console.error('[LOGGER ERROR]', e.message)
  }

  // 同时输出到控制台
  if (level === 'ERROR') console.error(line.trim())
  else console.log(line.trim())
}

module.exports = {
  debug: (svc, msg) => write(svc, 'DEBUG', msg),
  info:  (svc, msg) => write(svc, 'INFO', msg),
  warn:  (svc, msg) => write(svc, 'WARN', msg),
  error: (svc, msg, err) => write(svc, 'ERROR', msg, err),
  // 快捷方法
  gateway: {
    info:  (m) => write('GATEWAY', 'INFO', m),
    warn:  (m) => write('GATEWAY', 'WARN', m),
    error: (m, e) => write('GATEWAY', 'ERROR', m, e),
  },
  qqbot: {
    info:  (m) => write('QQBOT', 'INFO', m),
    warn:  (m) => write('QQBOT', 'WARN', m),
    error: (m, e) => write('QQBOT', 'ERROR', m, e),
  },
  stt: {
    info:  (m) => write('STT', 'INFO', m),
    warn:  (m) => write('STT', 'WARN', m),
    error: (m, e) => write('STT', 'ERROR', m, e),
  }
}
