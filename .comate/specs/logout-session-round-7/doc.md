# 第七轮循环优化：显式登出与持久化 session 删除

## 背景与问题

第三轮已经新增持久化 session 能力：

```python
async def delete_session(session_id: str):
    SESSION.pop(session_id, None)
    await db.execute("DELETE FROM sessions WHERE id=?", (session_id,))
```

但当前前端设置页的退出逻辑只是清理本地 localStorage：

```tsx
const handleLogout = () => {
  localStorage.removeItem('currentUserId')
  localStorage.removeItem('sessionId')
  navigate('/login', { replace: true })
}
```

这会导致：

- 后端 SQLite `sessions` 表中仍保留旧 session。
- 如果某个旧 sessionId 被复制或保留，理论上仍可继续访问。
- “切换角色”语义不准确，用户实际需要“退出登录 / 回登录页”。

本轮目标是补齐真实登出闭环。

## 目标

- 新增后端 `POST /api/auth/logout` 接口。
- 调用第三轮已有的 `delete_session(session_id)` 删除内存缓存和 SQLite session。
- 前端设置页调用 logout API 后清理本地 session 并回到登录页。
- 即使 logout 请求失败，也清理本地登录态，避免用户卡在当前会话。
- 将按钮文案从“切换角色”调整为“退出登录”。

## 技术方案

### 1. 后端新增 logout API

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/backend/routers/auth.py
```

新增导入：

```python
from fastapi import APIRouter, Request
from services.session_store import create_session, delete_session
```

新增接口：

```python
@router.post("/logout")
async def logout(request: Request):
    session_id = request.headers.get("X-Session-Id", "")
    if session_id:
        await delete_session(session_id)
    return {"success": True}
```

说明：

- `/api/auth/logout` 是受保护 API，不加入 `PUBLIC_API_PATHS`。
- 正常情况下中间件已确认 session 有效。
- 如果没有 session header，也返回 success，方便前端幂等清理。
- 不删除用户数据，不删除餐食、画像或匹配数据。

### 2. 前端设置页调用 logout

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Settings.tsx
```

当前：

```tsx
const handleLogout = () => {
  localStorage.removeItem('currentUserId')
  localStorage.removeItem('sessionId')
  navigate('/login', { replace: true })
}
```

改为：

```tsx
const [loggingOut, setLoggingOut] = useState(false)

const clearLocalSession = () => {
  localStorage.removeItem('currentUserId')
  localStorage.removeItem('sessionId')
  navigate('/login', { replace: true })
}

const handleLogout = async () => {
  if (loggingOut) return
  setLoggingOut(true)
  try {
    await api.post('/auth/logout')
  } finally {
    clearLocalSession()
  }
}
```

按钮：

- disabled 时防止重复点击。
- 文案：`loggingOut ? '正在退出...' : '退出登录'`。

### 3. 交互与失败处理

- logout 成功：后端删除 session，前端清理 localStorage，跳转 `/login`。
- logout 失败：前端仍清理 localStorage 并跳转 `/login`。
- logout 后同一个 sessionId 再访问 `/api/users/me` 应返回 401。

### 4. 受影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/auth.py`
    - 引入 `Request` 和 `delete_session`。
    - 新增 `POST /logout`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Settings.tsx`
    - 增加 `loggingOut` 状态。
    - 调用 `/auth/logout`。
    - 调整按钮文案和 disabled 状态。

## 验证方案

后端语法检查：

```bash
python3 -m py_compile routers/auth.py services/session_store.py main.py
```

前端构建：

```bash
npm run build
```

API 验证：

1. `PUT /api/users/me/switch` 获取 sessionId。
2. 用 sessionId 调用 `GET /api/users/me` 返回 200。
3. 用 sessionId 调用 `POST /api/auth/logout` 返回 200。
4. 再用同一个 sessionId 调用 `GET /api/users/me` 返回 401。

前端验证：

- TypeScript 构建通过。
- 设置页按钮文案为“退出登录”。
- 按钮 disabled 状态不破坏构建类型。

## 边界条件

- 本轮不实现“退出所有设备”。第三轮已预留 `delete_user_sessions(user_id)`，后续可增加。
- 本轮不增加 session 过期时间。
- 本轮不改登录页 UI 和注册逻辑。
- 不删除 demo 用户，不改 AI 配置，不影响 `user_bowen`。

## 预期结果

- 用户主动退出后，后端 session 立即失效。
- 前端本地 session 和后端持久化 session 状态一致。
- 旧 sessionId 不再能访问受保护接口。
- 设置页退出语义更符合真实产品。
