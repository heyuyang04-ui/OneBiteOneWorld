# 第三轮持久化登录态与认证错误语义统一任务清单

- [x] Task 1: 扩展数据库 session 表
    - 1.1: 在 `backend/database.py` 初始化脚本中新增 `sessions` 表
    - 1.2: 新增 `idx_sessions_user_id` 索引
    - 1.3: 保持原有 mock 数据导入逻辑不变

- [x] Task 2: 新增持久化 session store
    - 2.1: 新增 `backend/services/session_store.py`
    - 2.2: 实现 `create_session(user_id)` 并写入内存缓存与 SQLite
    - 2.3: 实现 `resolve_session(session_id)`，优先查内存，未命中时查 SQLite 并回填缓存
    - 2.4: 实现内部删除函数，为后续登出或账号安全治理预留能力

- [x] Task 3: 改造后端鉴权中间件
    - 3.1: 修改 `backend/main.py` 引入 `resolve_session`
    - 3.2: 将中间件中的内存 `SESSION` 直接判断替换为持久化解析
    - 3.3: 保持公开路径和未授权 401 响应结构不变

- [x] Task 4: 改造登录、注册和 demo 用户切换 session 创建
    - 4.1: 修改 `backend/routers/auth.py`，删除本地 `_create_session`
    - 4.2: `phone_login` 使用 `await create_session(user_id)`
    - 4.3: `register` 使用 `await create_session(user_id)`
    - 4.4: 修改 `backend/routers/users.py`，demo switch 使用 `await create_session(user_id)`
    - 4.5: 确认 `user_bowen` demo 用户切换能力不变

- [x] Task 5: 统一认证相关错误响应语义
    - 5.1: 在 `auth.py` 中引入并使用 `error_response`
    - 5.2: phone 缺失返回 400 / `BAD_REQUEST`
    - 5.3: phone 未注册返回 404 / `NOT_FOUND`
    - 5.4: 注册缺少 phone/name 返回 400 / `BAD_REQUEST`
    - 5.5: phone 已注册返回 409 / `CONFLICT`
    - 5.6: 在 `users.py` 中引入并使用 `error_response`
    - 5.7: demo switch 缺少 user_id 返回 400 / `BAD_REQUEST`
    - 5.8: 非 demo 用户直接切换返回 403 / `FORBIDDEN`
    - 5.9: 当前用户或 demo 用户不存在返回 404 / `NOT_FOUND`

- [x] Task 6: 改造通知 SSE session 解析
    - 6.1: 修改 `backend/routers/notifications.py` 引入 `resolve_session`
    - 6.2: 将 `_resolve_stream_user_id` 改为 async 函数
    - 6.3: 优先解析 query 参数 `x_session_id` 的持久化 session
    - 6.4: 保留 `request.state.user_id` 兜底
    - 6.5: 保持 SSE 数据格式和心跳逻辑不变

- [x] Task 7: 执行语法、构建和 API 验证
    - 7.1: 执行后端语法检查：`python3 -m py_compile main.py database.py services/session_store.py routers/auth.py routers/users.py routers/notifications.py`
    - 7.2: 执行前端构建：`npm run build`
    - 7.3: 验证 demo switch 成功返回 sessionId
    - 7.4: 验证使用 sessionId 访问 `/api/users/me` 返回 200
    - 7.5: 清空进程内 `SESSION` 后，验证同一 sessionId 仍可访问 `/api/users/me`
    - 7.6: 验证 phone-login 缺少 phone 返回 400
    - 7.7: 验证未注册 phone 返回 404
    - 7.8: 验证重复注册 phone 返回 409
    - 7.9: 验证非 demo 用户 switch 返回 403

- [x] Task 8: 复查并生成第三轮总结
    - 8.1: 搜索 `auth.py`、`users.py` 中旧错误返回是否仍存在
    - 8.2: 搜索后端是否仍有直接写入 `SESSION[session_id]` 的业务代码
    - 8.3: 记录本轮修复内容、验证结果和下一轮候选优化
    - 8.4: 生成 `.comate/specs/persistent-session-hardening-round-3/summary.md`
