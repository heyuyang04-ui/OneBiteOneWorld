# 前后端循环优化第二轮方案

## 背景

第一轮循环优化已完成，已修复：

- 通知未读数闭环。
- 图片 MIME 链路。
- 手动补录 Agent 编排。
- 启动脚本执行权限。

本轮继续处理上一轮总结中的 P1/P2 问题，但不做无法快速验证的大规模重构。目标是继续沿用：

```text
发现问题 -> 修正 -> 测试 -> 复查 -> 输出下一轮建议
```

## 本轮优先目标

本轮选择三个高价值、可控范围的方向：

1. 前端统一处理 session 失效和 401 错误，改善“后端重启后用户不知道发生什么”的体验。
2. 后端为常见业务失败提供更明确的 HTTP 状态码辅助函数，并先覆盖高频接口。
3. 为 Agent 编排增加基础 trace 返回，让产品演示时能看到“事件 -> Agent -> Skill”的链路。

## 问题一：session 失效时前端体验不清晰

### 当前表现

当前 session 存在后端内存 `SESSION = {}` 中。后端重启或 reload 后，前端 localStorage 中仍可能保留：

```text
currentUserId
sessionId
```

虽然 `ProtectedLayout` 会调用 `/api/users/me` 校验，但其他接口收到 401 时，前端没有统一拦截和提示。

### 相关文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/services/api.ts`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`

### 修复方案

在 `api.ts` 中增加响应拦截器：

- 捕获 HTTP 401。
- 清理 `currentUserId` 和 `sessionId`。
- 派发全局事件 `auth:session-expired`。
- 避免同一轮多个 401 重复弹提示。

在 `App.tsx` 增加全局监听：

- 监听 `auth:session-expired`。
- 展示轻量提示：登录已失效，请重新登录。
- 跳转登录页。

为了保持最小改动，本轮不引入 toast 库、不改登录注册流程、不实现持久化 session。

### 预期结果

当后端 session 失效时，用户不再卡在内部页面，而是得到明确提示并回到登录页。

---

## 问题二：后端常见业务失败 HTTP 状态码不清晰

### 当前表现

项目中很多业务失败返回：

```json
{"success": false, "error": {"message": "..."}}
```

但 HTTP 状态仍是 200。这会让前端和调试工具难以区分成功和失败。

### 本轮控制范围

不一次性重写所有 router，只先补一个统一响应辅助工具，并覆盖高频接口：

- meal not found
- not authorized
- notification not found
- 手动补录空菜名
- 图片格式错误

### 相关文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`
- 可新增：`/Users/libowen/Desktop/one-bite-one-world/backend/utils/responses.py`

### 修复方案

新增统一函数：

```python
from fastapi.responses import JSONResponse

ERROR_STATUS = {
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
}

def error_response(message: str, code: str = "BAD_REQUEST", status_code: int | None = None):
    return JSONResponse(
        status_code=status_code or ERROR_STATUS.get(code, 400),
        content={"success": False, "error": {"code": code, "message": message}},
    )
```

然后在目标接口中替换部分高频错误返回。

### 预期结果

高频失败场景开始具备清晰 HTTP 语义，前端 axios 拦截器能更可靠地区分 401。

---

## 问题三：Agent 编排没有 trace，难以展示差异化

### 当前表现

后端已有：

- `AgentEvent`
- `Orchestrator`
- `TasteAgent` / `SocialAgent` / `CityAgent`
- `BaseAgent.run()` 的 perceive/reason/act/reflect

但 API 返回中没有展示本次事件经过了哪个 Agent、调用了哪些 skills、是否有 follow-up event。

### 相关文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/agents/orchestrator.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/agents/base.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/agents/protocol.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.css`

### 修复方案

在不改变 Agent 核心流程的前提下，为返回结果增加轻量 trace：

- `Orchestrator.process_event` 生成 trace list。
- trace 包括：
  - event_type
  - agent
  - skill names
  - follow_up count
- `AgentResult.data` 中增加 `__trace` 字段。
- `meals.py` 将 `agent_trace` 返回给前端。
- `MealResult.tsx` 如果 state 或 meal 中存在 `agent_trace`，展示“Agent 本次做了什么”。

示例返回：

```json
"agent_trace": [
  {"event_type": "meal.uploaded", "agent": "taste", "skills": ["report_skill", "notify_skill"], "follow_up_count": 0}
]
```

### 预期结果

上传或手动补录后，结果页可以展示简单的 Agent 编排过程，更有利于解释“一食万象不是单纯调用模型 API”。

---

## 本轮受影响文件

### 后端

- 新增：`/Users/libowen/Desktop/one-bite-one-world/backend/utils/responses.py`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/agents/orchestrator.py`

### 前端

- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/services/api.ts`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.css`

## 验证计划

### 后端语法检查

```bash
python3 -m py_compile routers/meals.py routers/notifications.py agents/orchestrator.py utils/responses.py
```

### 前端构建

```bash
npm run build
```

### API 验证

1. 未登录访问 `/api/meals` 返回 401。
2. 不存在餐食详情返回 404。
3. 不存在通知已读返回 404。
4. 手动补录空菜名返回 400。
5. 手动补录成功返回 `agent_trace`。

### 手动验证

1. 清理或伪造 `sessionId` 后访问内部页面，确认跳转登录并给出 session 失效提示。
2. 上传或手动补录一餐，确认结果页展示 Agent trace。
3. 原有餐食展示、纠错、历史记录仍正常。

## 收敛标准

本轮完成标准：

- session 失效有统一处理。
- 高频接口错误 HTTP 状态码更明确。
- 上传/补录结果具备基础 Agent trace。
- 后端语法检查通过。
- 前端构建通过。
- 生成本轮 `summary.md`，并列出下一轮建议。
