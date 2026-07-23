# 茄子数据 - 当前数据库 Schema（PostgreSQL / Railway）

## users 表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | SERIAL | PK | 用户ID |
| username | VARCHAR(64) | UNIQUE NOT NULL | 用户名 |
| password_hash | VARCHAR(128) | NOT NULL | 密码hash |
| display_name | VARCHAR(128) | - | 显示名称 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 注册时间 |
| role | VARCHAR(16) | NOT NULL DEFAULT 'user' | 角色: user/admin |

**当前数据: 8 条**

## files 表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | SERIAL | PK | 文件ID |
| user_id | INTEGER | NOT NULL REFERENCES users(id) | 所属用户 |
| filename | VARCHAR(255) | NOT NULL | 服务器存储文件名 |
| original_name | VARCHAR(255) | NOT NULL | 原始文件名 |
| size | BIGINT | NOT NULL | 文件大小(字节) |
| mime_type | VARCHAR(128) | - | MIME类型 |
| upload_time | TIMESTAMP | NOT NULL DEFAULT NOW() | 上传时间 |
| file_path | VARCHAR(512) | NOT NULL | 文件存储路径 |

**当前数据: 2 条，无索引**

## clouddata 表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | SERIAL | PK | 数据ID |
| k | VARCHAR(255) | UNIQUE NOT NULL | 键 |
| v | TEXT | NOT NULL | 值 |
| t | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 时间 |
| read | BOOLEAN | NOT NULL DEFAULT FALSE | 已读标记 |
| project_id | INTEGER | REFERENCES clouddata_projects(id) DEFAULT 1 | 所属项目 |
| name | VARCHAR(255) | DEFAULT '' | 名称 |
| md5 | VARCHAR(32) | DEFAULT '' | MD5校验 |

## clouddata_projects 表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | SERIAL | PK | 项目ID |
| name | VARCHAR(255) | NOT NULL | 项目名称 |
| token | VARCHAR(64) | NOT NULL | 访问令牌 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 当前的问题

1. **没有索引** — files 表的 user_id、upload_time 等常用查询字段没索引
2. **clouddata.k 虽 UNIQUE 但没单独建索引**
3. **files 表缺字段** — 没有文件描述、分类、更新时间
4. **没有用户配额限制** — 用户可无限上传
5. **clouddata 的 md5/name 字段是后来ALTER添加的，约束不一致**
6. **clouddata_projects 缺更新时间字段**
