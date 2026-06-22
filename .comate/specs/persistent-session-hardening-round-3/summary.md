# 第三轮循环优化总结：持久化登录态与认证错误语义统一

## 本轮完成内容

- 扩展数据库结构
    - 在 `backend/database.py` 中新增 `sessions` 表。
    - 新增 `idx_sessions_user_id` 索引。
    - 保持原有 mock 用户和 mock 餐食导入逻辑不变。

- 新增持久化 session store
    - 新增 `backend/services/session_store.py`。
    - `create_session(user_id)` 同时写入内存缓存 `SESSION` 和 SQLite `sessions` 表。
    - `resolve_session(session_id)` 优先读取内存缓存，未命中时读取 SQLite，并回填内存缓存。
    - 增加 `delete_session(session_id)` 与 `delete_user_sessions(user_id)`，为后续登出、账号安全或设备管理预留内部能力。

- 改造后端鉴权中间件
    - `backend/main.py` 不再直接判断 `SESSION`。
    - 所有带 `X-Session-Id` 的请求统一通过 `resolve_session` 解析。
    - 未授权 401 响应结构保持不变，继续兼容前端第二轮新增的 session 失效拦截器。

- 改造登录、注册和 demo 用户切换
    - `backend/routers/auth.py` 删除本地 `_create_session`。
    - 手机登录和注册改为 `await create_session(...)`。
    - `backend/routers/users.py` demo 用户切换改为 `await create_session(...)`。
    - demo 用户 `user_bowen` 保持可切换。

- 统一认证相关错误响应
    - `auth.py` 使用 `error_response`：
        - phone 缺失：400 / `BAD_REQUEST`
        - phone 未注册：404 / `NOT_FOUND`
        - 注册缺少 phone/name：400 / `BAD_REQUEST`
        - phone 已注册：409 / `CONFLICT`
    - `users.py` 使用 `error_response`：
        - demo switch 缺少 user_id：400 / `BAD_REQUEST`
        - 非 demo 用户直接 switch：403 / `FORBIDDEN`
        - 当前用户或 demo 用户不存在：404 / `NOT_FOUND`

- 改造通知 SSE session 解析
    - `backend/routers/notifications.py` 的 `_resolve_stream_user_id` 改为 async。
    - SSE query 参数 `x_session_id` 现在通过 `resolve_session` 支持持久化 session。
    - SSE 数据格式、未读数量变化推送和 heartbeat 逻辑保持不变。

## 验证结果

- 后端语法检查通过：
    - `python3 -m py_compile main.py database.py services/session_store.py routers/auth.py routers/users.py routers/notifications.py`

- 前端构建通过：
    - `npm run build`
    - 仍存在 Vite 大 chunk 警告，主 JS chunk 约 1.67MB，后续仍建议做页面懒加载和图表拆包。

- API 验证通过：
    - `PUT /api/users/me/switch` 返回 200，并返回 sessionId。
    - 使用 sessionId 访问 `GET /api/users/me` 返回 200。
    - 清空当前进程内 `SESSION` 后，通过 `resolve_session(sessionId)` 仍能解析为 `user_bowen`，说明 session 已落库并可在内存丢失后恢复。
    - `POST /api/auth/phone-login` 缺少 phone 返回 400 / `BAD_REQUEST`。
    - `POST /api/auth/phone-login` 未注册 phone 返回 404 / `NOT_FOUND`。
    - 重复注册同一 phone 返回 409 / `CONFLICT`。
    - 非 demo 用户 switch 返回 403 / `FORBIDDEN`。

## 复查结果

- `auth.py` 和 `users.py` 中未发现旧格式 `return {"success": False ...}` 错误返回。
- 后端直接写入 `SESSION[session_id]` 的代码仅保留在 `services/session_store.py`，业务路由不再直接操作 session 内存缓存。

## 下一轮候选优化

- 增加显式登出接口，并调用 `delete_session(session_id)` 删除当前 session。
- 给 `sessions` 表增加过期时间和清理策略，避免长期累积无效 session。
- 继续统一其他路由的错误响应语义，例如 `city.py`、`match.py`、`report.py`。
- 将前端页面改为懒加载，拆分 ECharts、城市地图等大依赖，解决当前 Vite 大 chunk 警告。
- 将 Agent trace 持久化到 `episodes` 或餐食扩展字段，支持历史详情页也能查看当时的 Agent 决策链。
