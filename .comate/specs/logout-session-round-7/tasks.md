# 第七轮显式登出与持久化 session 删除任务清单

- [x] Task 1: 后端新增 logout API
    - 1.1: 修改 `backend/routers/auth.py` 引入 `Request`
    - 1.2: 从 `services.session_store` 引入 `delete_session`
    - 1.3: 新增 `POST /api/auth/logout` 路由
    - 1.4: 从请求头读取 `X-Session-Id`
    - 1.5: 调用 `await delete_session(session_id)` 删除内存缓存和 SQLite session
    - 1.6: 返回 `{ success: true }`，保持接口幂等

- [x] Task 2: 前端设置页接入 logout API
    - 2.1: 修改 `frontend/src/pages/Settings.tsx`
    - 2.2: 新增 `loggingOut` 状态
    - 2.3: 新增 `clearLocalSession` 函数，清理 `currentUserId` 和 `sessionId`
    - 2.4: 将 `handleLogout` 改为 async 函数
    - 2.5: 调用 `api.post('/auth/logout')`
    - 2.6: 在 `finally` 中清理本地 session 并跳转 `/login`

- [x] Task 3: 调整设置页退出按钮体验
    - 3.1: 将按钮文案从“切换角色”改为“退出登录”
    - 3.2: loggingOut 时显示“正在退出...”
    - 3.3: loggingOut 时禁用按钮，防止重复点击
    - 3.4: 保持原有按钮视觉风格不做大范围重构

- [x] Task 4: 执行后端语法和前端构建验证
    - 4.1: 执行 `python3 -m py_compile routers/auth.py services/session_store.py main.py`
    - 4.2: 执行 `npm run build`
    - 4.3: 检查 TypeScript 编译是否通过
    - 4.4: 检查 Vite 构建是否通过

- [x] Task 5: 执行 logout API 行为验证
    - 5.1: 调用 `PUT /api/users/me/switch` 获取 sessionId
    - 5.2: 使用 sessionId 调用 `GET /api/users/me`，确认返回 200
    - 5.3: 使用同一 sessionId 调用 `POST /api/auth/logout`，确认返回 200
    - 5.4: 再次使用同一 sessionId 调用 `GET /api/users/me`，确认返回 401

- [x] Task 6: 复查并生成第七轮总结
    - 6.1: 复查 `auth.py` 中 logout 是否未加入公开路径
    - 6.2: 复查 `Settings.tsx` 是否无纯本地登出残留
    - 6.3: 记录构建结果、API 验证结果和后续优化项
    - 6.4: 生成 `.comate/specs/logout-session-round-7/summary.md`
