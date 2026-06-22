# 第三轮循环优化：持久化登录态与认证错误语义统一

## 背景与问题

第二轮已经完成统一 401 处理、关键接口错误状态码、Agent trace 返回与展示。但当前后端 session 仍依赖 `config.py` 中的内存字典：

```python
SESSION = {}
```

这会带来真实用户体验问题：

- 后端重启或热重载后，前端 `localStorage` 中仍保存 `sessionId`，但后端内存已丢失，用户会被迫重新登录。
- 登录、注册、demo 用户切换等认证相关接口仍存在 `{ success: false }` 但 HTTP 200 的错误返回，不利于前端统一提示。
- SSE 通知流 `GET /api/notifications/stream` 通过 query 参数读取 session，但当前也只查内存 `SESSION`，重启后实时提醒会断开并无法恢复。

本轮聚焦后端认证稳定性，不改动 AI API key fallback，不改变 demo 用户 `user_bowen`。

## 目标

- 新增 SQLite 持久化 session 表，后端重启后已有 sessionId 仍可恢复。
- 保留内存 `SESSION` 作为热路径缓存，但以数据库为准做兜底。
- 统一 auth/users 高频认证错误状态码。
- 修复 notification SSE 对持久化 session 的兼容。
- 保持前端已有 session 失效处理逻辑不变，减少改动范围。

## 架构与技术方案

### 1. 新增 session 存储能力

新增文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/services/session_store.py
```

职责：

- 生成 sessionId。
- 将 session 写入 SQLite `sessions` 表。
- 根据 sessionId 解析 user_id。
- 删除单个 session 或按用户删除 session 的能力暂不做 UI 入口，但保留内部函数便于后续扩展。
- 写入内存 `SESSION` 缓存，减少每次 API 鉴权的数据库查询。

核心函数设计：

```python
async def create_session(user_id: str) -> str:
    session_id = str(uuid.uuid4())
    SESSION[session_id] = user_id
    async with aiosqlite.connect(app_config.db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO sessions (id, user_id, created_at) VALUES (?,?,?)",
            (session_id, user_id, datetime.now().isoformat()),
        )
        await db.commit()
    return session_id

async def resolve_session(session_id: str) -> str:
    if not session_id:
        return ""
    if session_id in SESSION:
        return SESSION[session_id]
    async with aiosqlite.connect(app_config.db_path) as db:
        cursor = await db.execute("SELECT user_id FROM sessions WHERE id=?", (session_id,))
        row = await cursor.fetchone()
    if not row:
        return ""
    SESSION[session_id] = row[0]
    return row[0]
```

边界处理：

- 空 sessionId 返回空字符串。
- 不存在或已删除 session 返回空字符串。
- DB 查询异常不吞掉全局异常；由 FastAPI 全局错误处理兜底。

### 2. 扩展数据库初始化

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/database.py
```

新增表：

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    created_at TEXT
);
```

可选索引：

```sql
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
```

### 3. 修改鉴权中间件

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/main.py
```

当前逻辑只查内存：

```python
if session_id and session_id in SESSION:
    request.state.user_id = SESSION[session_id]
```

改为异步解析：

```python
user_id = await resolve_session(session_id)
if user_id:
    request.state.user_id = user_id
    return await call_next(request)
```

影响：

- 所有受保护 `/api/*` 接口在后端重启后仍能根据 DB 中 session 恢复用户。
- 内存命中时仍快速返回。
- 未授权仍返回 401，与第二轮前端拦截器兼容。

### 4. 修改登录/注册/session 创建调用点

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/routers/auth.py
/Users/libowen/Desktop/one-bite-one-world/backend/routers/users.py
```

改动点：

- `auth.py` 删除本地 `_create_session`，改用 `await create_session(user_id)`。
- `users.py` demo 用户切换也改用 `await create_session(user_id)`。
- 保留 `user_bowen` 和其他 demo 用户切换能力。

### 5. 修改 notification SSE session 解析

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py
```

当前 `_resolve_stream_user_id` 是同步函数，只查内存：

```python
def _resolve_stream_user_id(request: Request) -> str:
    session_id = request.query_params.get("x_session_id", "")
    if session_id and session_id in SESSION:
        return SESSION[session_id]
    return getattr(request.state, "user_id", "")
```

改为异步：

```python
async def _resolve_stream_user_id(request: Request) -> str:
    session_id = request.query_params.get("x_session_id", "")
    user_id = await resolve_session(session_id)
    return user_id or getattr(request.state, "user_id", "")
```

调用处：

```python
user_id = await _resolve_stream_user_id(request)
```

### 6. 统一 auth/users 高频错误响应

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/routers/auth.py
/Users/libowen/Desktop/one-bite-one-world/backend/routers/users.py
```

引入：

```python
from utils.responses import error_response
```

替换：

- phone 缺失：400 / `BAD_REQUEST`
- phone 未注册：404 / `NOT_FOUND`
- 注册缺少 phone/name：400 / `BAD_REQUEST`
- phone 已注册：409 / `CONFLICT`
- demo switch 缺少 user_id：400 / `BAD_REQUEST`
- demo switch 非 demo 用户：403 / `FORBIDDEN`
- demo user 不存在：404 / `NOT_FOUND`
- `/users/me` 找不到用户：404 / `NOT_FOUND`

### 7. 验证方案

后端语法检查：

```bash
python3 -m py_compile main.py database.py services/session_store.py routers/auth.py routers/users.py routers/notifications.py
```

前端构建确认不受影响：

```bash
npm run build
```

API 验证：

- `PUT /api/users/me/switch` 成功返回 sessionId。
- 使用 sessionId 访问 `/api/users/me` 返回 200。
- 清空当前进程内 `SESSION` 后，使用同一 sessionId 再访问 `/api/users/me` 仍返回 200，用于模拟后端重启后的 session 恢复。
- 缺少 phone 调用 `/api/auth/phone-login` 返回 400。
- 未注册 phone 返回 404。
- 注册重复 phone 返回 409。
- 非 demo 用户直接切换返回 403。
- SSE stream 解析函数可通过 query sessionId 命中持久化 session。

## 受影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/database.py`
    - 新增 `sessions` 表和索引。
- `/Users/libowen/Desktop/one-bite-one-world/backend/services/session_store.py`
    - 新增 session 创建、解析、删除能力。
- `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`
    - 鉴权中间件改用 `resolve_session`。
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/auth.py`
    - 登录/注册 session 创建改用持久化 store。
    - 认证错误改用 `error_response`。
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/users.py`
    - demo switch 改用持久化 session。
    - 高频错误改用 `error_response`。
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`
    - SSE query sessionId 改用持久化解析。

## 预期结果

- 后端热重载/重启后，已登录用户不会因为内存 session 丢失而立即失效。
- 登录注册和 demo 切换错误语义更明确，前端可稳定依赖 HTTP 状态码。
- 通知 SSE 在刷新或后端恢复后能继续识别用户 session。
- 不影响现有前端 localStorage session 存储方式。
- 不影响 demo 用户 `user_bowen`。
- 不修改 AI 配置中的硬编码 fallback key。
