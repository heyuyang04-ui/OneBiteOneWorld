# 前后端循环优化第二轮任务清单

- [x] Task 1: 增加前端 session 失效统一处理
    - 1.1: 在 `frontend/src/services/api.ts` 中增加 axios 响应拦截器
    - 1.2: 捕获 HTTP 401 后清理 `currentUserId` 和 `sessionId`
    - 1.3: 派发 `auth:session-expired` 全局事件，并避免同一轮重复派发
    - 1.4: 在 `App.tsx` 中监听 `auth:session-expired`
    - 1.5: 展示轻量 session 失效提示并跳转 `/login`

- [x] Task 2: 增加后端统一错误响应辅助函数
    - 2.1: 新增 `backend/utils/responses.py`
    - 2.2: 实现 `error_response(message, code, status_code)`
    - 2.3: 覆盖 `BAD_REQUEST`、`UNAUTHORIZED`、`FORBIDDEN`、`NOT_FOUND`、`CONFLICT` 状态映射
    - 2.4: 保持响应体结构为 `{ success: false, error: { code, message } }`

- [x] Task 3: 覆盖高频后端错误状态码
    - 3.1: 在 `meals.py` 中使用 `error_response` 处理图片格式错误和手动补录空菜名
    - 3.2: 在 `meals.py` 中使用 `error_response` 处理餐食不存在和越权访问
    - 3.3: 在 `notifications.py` 中使用 `error_response` 处理通知不存在
    - 3.4: 保持成功响应结构不变，避免影响前端正常数据读取

- [x] Task 4: 增加后端 Agent trace 返回
    - 4.1: 修改 `agents/orchestrator.py`，在 `process_event` 中收集主事件和 follow-up trace
    - 4.2: trace 记录 `event_type`、`agent`、`skills`、`follow_up_count`
    - 4.3: 将 trace 放入 `AgentResult.data["__trace"]`
    - 4.4: 在 `meals.py` 上传识别路径返回 `agent_trace`
    - 4.5: 在 `meals.py` 手动补录路径返回 `agent_trace`

- [x] Task 5: 在结果页展示 Agent trace
    - 5.1: 修改 `MealResult.tsx`，从 `state.agent_trace` 或 `meal.agent_trace` 中读取 trace
    - 5.2: 在结果页新增“Agent 本次做了什么”展示区
    - 5.3: 展示事件类型、Agent 名称、调用 skills、follow-up 数量
    - 5.4: 在 `MealResult.css` 中补充 trace 展示样式
    - 5.5: 没有 trace 时不渲染该区域，兼容历史数据

- [x] Task 6: 执行构建、语法和 API 验证
    - 6.1: 执行后端语法检查：`python3 -m py_compile routers/meals.py routers/notifications.py agents/orchestrator.py utils/responses.py`
    - 6.2: 执行前端构建：`npm run build`
    - 6.3: 验证未登录 `/api/meals` 返回 401
    - 6.4: 验证不存在餐食详情返回 404
    - 6.5: 验证不存在通知已读返回 404
    - 6.6: 验证手动补录空菜名返回 400
    - 6.7: 验证手动补录成功返回 `agent_trace`

- [x] Task 7: 复查并生成第二轮总结
    - 7.1: 搜索本轮旧错误返回是否仍存在于目标接口
    - 7.2: 复查前端 session 失效逻辑是否会影响登录页公开接口
    - 7.3: 记录本轮修复内容和验证结果
    - 7.4: 输出下一轮候选优化任务到 `summary.md`
