# 前后端循环优化第二轮总结

## 本轮完成内容

- 增加前端统一 session 失效处理
    - 在 `frontend/src/services/api.ts` 中增加 axios 401 响应拦截器。
    - 401 后清理 `currentUserId`、`sessionId`，派发 `auth:session-expired` 事件。
    - 在 `frontend/src/App.tsx` 中改为 Router 内 `useNavigate('/login', { replace: true })` 跳转，避免只修改 URL 不触发 React Router 页面更新。
    - 增加 session 失效提示条样式。

- 增加后端统一错误响应辅助函数
    - 新增 `backend/utils/responses.py`。
    - 统一输出 `{ success: false, error: { code, message } }`。
    - 支持 `BAD_REQUEST`、`UNAUTHORIZED`、`FORBIDDEN`、`NOT_FOUND`、`CONFLICT` 状态码映射。

- 覆盖高频后端错误状态码
    - `backend/routers/meals.py`：图片校验失败、手动补录空菜名、餐食不存在、越权访问、图片不存在等路径改为明确 HTTP 状态码。
    - `backend/routers/notifications.py`：未登录、通知不存在等路径改为明确 HTTP 状态码。
    - 复查 `meals.py` 后，补齐手动补录图片校验失败的旧错误结构。

- 增加 Agent trace 返回
    - `backend/agents/orchestrator.py` 在 `process_event` 中收集主事件与 follow-up trace。
    - trace 包含 `event_type`、`agent`、`skills`、`follow_up_count`。
    - 上传识别和手动补录餐食接口均返回 `agent_trace`。

- 在结果页展示 Agent trace
    - `frontend/src/pages/MealResult.tsx` 支持从 `state.agent_trace` 或 `meal.agent_trace` 读取 trace。
    - 新增“Agent 本次做了什么”区域，展示事件类型、Agent、调用能力、后续事件数量。
    - `frontend/src/pages/MealResult.css` 增加 trace 卡片和列表样式。
    - 无 trace 的历史数据不会渲染该区域。

## 验证结果

- 后端语法检查通过：
    - `python3 -m py_compile routers/meals.py routers/notifications.py agents/orchestrator.py utils/responses.py`

- 前端构建通过：
    - `npm run build`
    - 仍存在 Vite 大 chunk 警告：主 JS chunk 约 1.67MB，建议后续拆分 ECharts、页面路由等大依赖。

- API 验证通过：
    - 未登录 `GET /api/meals` 返回 401 / `UNAUTHORIZED`。
    - demo 用户切换登录 `PUT /api/users/me/switch` 返回 200。
    - 已登录访问不存在餐食详情返回 404 / `NOT_FOUND`。
    - 已登录标记不存在通知已读返回 404 / `NOT_FOUND`。
    - 手动补录空菜名返回 400 / `BAD_REQUEST`。
    - 手动补录成功返回 200，并包含 `agent_trace`，trace 长度为 1。

## 发现并修正的额外问题

- 原验证脚本误用了不存在的 `POST /api/auth/login`，实际当前登录入口是：
    - `PUT /api/users/me/switch`
    - `POST /api/auth/phone-login`
- `App.tsx` 原先使用 `window.history.replaceState(null, '', '/login')`，可能只改变地址栏、不触发 React Router 页面切换；已改为 Router 内 `useNavigate`。

## 下一轮候选优化

- 将 session 从内存 `SESSION = {}` 升级为持久化机制，避免后端重启后所有用户登录态失效。
- 对前端路由做懒加载和拆包，降低 Vite 大 chunk 警告。
- 将更多路由错误响应统一到 `error_response`，覆盖 `auth.py`、`users.py`、`city.py` 等模块。
- 将 Agent trace 持久化到餐食或 episode 记录，支持历史详情页也能展示当时的 Agent 决策链。
- 优化手动补录触发 Agent 链路的耗时，对 LLM/报告类调用做异步或后台化处理。
