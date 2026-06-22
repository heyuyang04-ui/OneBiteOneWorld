# 第八轮循环优化：session 过期时间与清理策略

## 背景与问题

第三轮已将 session 从内存升级为 SQLite 持久化，第七轮已补充显式登出并删除当前 session。但当前 `sessions` 表只有：

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    created_at TEXT
);
```

问题：

- 未登出的 session 会长期保留。
- 旧 sessionId 理论上可无限期访问受保护接口。
- `sessions` 表会长期累积历史记录。

本轮目标是为 session 增加过期时间和自动清理策略。

## 目标

- 给 `sessions` 表增加 `expires_at` 字段。
- 创建 session 时写入过期时间。
- 解析 session 时拒绝过期 session，并删除对应记录。
- 应用启动时清理过期 session。
- 保持 demo 用户 `user_bowen` 和现有登录/登出流程不变。

## 技术方案

### 1. 配置 session TTL

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/config.py
```

在 `AppConfig` 中新增：

```python
session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "168"))
```

默认 168 小时，即 7 天。

不修改 AIConfig，不修改 hardcoded AI API key fallback。

### 2. 扩展 sessions 表结构

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/database.py
```

新增字段：

```sql
expires_at TEXT
```

由于 SQLite `CREATE TABLE IF NOT EXISTS` 不会修改旧表，需要增加迁移函数：

```python
async def _ensure_session_columns(db):
    cursor = await db.execute("PRAGMA table_info(sessions)")
    columns = {row[1] for row in await cursor.fetchall()}
    if "expires_at" not in columns:
        await db.execute("ALTER TABLE sessions ADD COLUMN expires_at TEXT")
        await db.execute("UPDATE sessions SET expires_at=? WHERE expires_at IS NULL OR expires_at=''", (default_expires_at,))
```

为了避免迁移复杂化，旧 session 统一设置为“当前时间 + TTL”。

新增索引：

```sql
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
```

### 3. session_store 增加过期逻辑

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/services/session_store.py
```

新增工具函数：

```python
def _now() -> datetime:
    return datetime.now()

def _expires_at() -> str:
    return (_now() + timedelta(hours=app_config.session_ttl_hours)).isoformat()

def _is_expired(expires_at: str) -> bool:
    if not expires_at:
        return False
    try:
        return datetime.fromisoformat(expires_at) <= _now()
    except ValueError:
        return True
```

`create_session` 改为写入：

```sql
INSERT OR REPLACE INTO sessions (id, user_id, created_at, expires_at) VALUES (?,?,?,?)
```

`SESSION` 内存缓存当前是 `session_id -> user_id`，无法判断过期。为保持简单且正确，本轮改为：

```python
SESSION[session_id] = {"user_id": user_id, "expires_at": expires_at}
```

`resolve_session` 需要兼容旧缓存值：

- 如果缓存值是字符串，继续认为是旧缓存格式，返回 user_id。
- 如果缓存值是 dict，检查 `expires_at`。
- 如果过期，删除内存和 DB 记录，返回空字符串。

DB 查询改为：

```sql
SELECT user_id, expires_at FROM sessions WHERE id=?
```

如果 DB session 过期：

- 调用 `await delete_session(session_id)`。
- 返回空字符串。

新增：

```python
async def cleanup_expired_sessions():
    now = _now().isoformat()
    async with aiosqlite.connect(app_config.db_path) as db:
        await db.execute("DELETE FROM sessions WHERE expires_at IS NOT NULL AND expires_at <= ?", (now,))
        await db.commit()
    # 同步清理内存中过期 dict 缓存
```

### 4. 应用启动时清理过期 session

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/main.py
```

新增导入：

```python
from services.session_store import cleanup_expired_sessions, resolve_session
```

启动时：

```python
@app.on_event("startup")
async def startup():
    await init_db()
    await cleanup_expired_sessions()
```

### 5. 兼容现有 logout

`delete_session(session_id)` 和 `delete_user_sessions(user_id)` 保持语义不变，但需要兼容 `SESSION` value 从 string 变为 dict：

```python
for session_id, cached in list(SESSION.items()):
    cached_user_id = cached.get("user_id") if isinstance(cached, dict) else cached
```

### 6. 验证方案

后端语法检查：

```bash
python3 -m py_compile config.py database.py main.py services/session_store.py routers/auth.py
```

API 验证：

1. demo switch 创建 session。
2. 使用 session 访问 `/api/users/me` 返回 200。
3. 直接通过 `session_store.delete_session(session_id)` 删除，确认访问返回 401。
4. 使用 `session_store.create_session('user_bowen')` 创建 session，并手动将 DB 中 `expires_at` 改为过去时间。
5. 使用该过期 session 调用 `/api/users/me` 返回 401。
6. 调用 `cleanup_expired_sessions()` 后确认过期 session 被清理。

前端构建：

```bash
npm run build
```

## 受影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/config.py`
    - 新增 `session_ttl_hours`。
- `/Users/libowen/Desktop/one-bite-one-world/backend/database.py`
    - sessions 表新增 `expires_at`。
    - 增加旧表迁移。
    - 增加 `idx_sessions_expires_at`。
- `/Users/libowen/Desktop/one-bite-one-world/backend/services/session_store.py`
    - create/resolve/delete/cleanup 支持过期时间。
- `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`
    - startup 清理过期 session。

## 边界条件

- 不在本轮增加“退出所有设备”。
- 不改变前端登录态存储方式。
- 旧 session 迁移后设置为当前时间 + TTL，避免升级后立刻让所有用户掉线。
- 若 `expires_at` 格式异常，视为过期并清理。
- 不修改 AI 配置 key fallback。

## 预期结果

- 新 session 默认 7 天后过期。
- 过期 session 不能访问受保护接口。
- 服务启动时会清理历史过期 session。
- session 表不会无限累积无效记录。
