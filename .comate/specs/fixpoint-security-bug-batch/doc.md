# fixpoint-security-bug-batch 需求说明

## 背景

当前 `/Users/libowen/Desktop/one-bite-one-world/fixpoint.txt` 更新为 32 个问题的新清单，包含 P0/P1/P2/P3 多类问题。本轮按“先修安全越权与明显影响体验的 bug”的原则处理，不一次性重构全部架构，避免引入大范围不稳定。

本轮优先修复：

- BUG-2：全局 user 识别无鉴权，默认 `user_01`。
- BUG-4：用户列表与切换用户无鉴权。
- BUG-5：`/match/{id}/detail` demo 兼容分支可越权读任意用户。
- BUG-6：`/notifications/{id}/read` 缺少 `user_id` 校验。
- BUG-7：match like 写入没有事务兜底。
- BUG-10：Decision parse 失败时可能把原始 LLM 输出落入 reasoning。
- BUG-12：前端 API baseURL 硬编码。
- BUG-19：新用户空向量不写库，导致匹配画像不可用。
- BUG-24：隐私设置失败无提示。
- BUG-25：CityMap tooltip 取值路径不稳，可能显示 NaN。

本轮暂不处理或仅记录：

- BUG-1：硬编码 AI API Key。此前已要求保留 `backend/config.py` 中 fallback，且 code-security skill 当前不开放硬编码凭证修复/托管，因此本轮不改。
- BUG-3：真实短信验证码/密码/JWT 认证属于产品级认证体系变更，会影响登录注册设计和演示入口。本轮先补强 session 鉴权边界，不引入短信服务或密码体系。
- BUG-9、BUG-14、BUG-16、BUG-20、BUG-21、BUG-23 等缓存、批量图、SESSION 存储、SSE 退避类优化可在后续单独做性能/稳定性批次。
- BUG-17、BUG-18 是上一轮修复策略的复审意见：目前有向 match 模型和前端二次拉图是有意保留的实现，不在本轮改动。

## 需求一：补强会话鉴权边界

### 场景与处理逻辑

当前 `backend/main.py` 中 `user_middleware` 在请求缺少有效 `X-Session-Id` 时会退回 `X-User-Id` 或默认 `user_01`。这会导致任意未登录请求访问或修改默认用户数据。

处理逻辑：

1. 公共接口允许无需 session：
   - `/`
   - `/docs`
   - `/openapi.json`
   - `/api/auth/phone-login`
   - `/api/auth/register`
   - `/api/users/me/switch` 仅作为演示用户入口保留，但限制只能切换到白名单演示用户。
   - `/api/notifications/stream` 因 EventSource 不能传 header，继续支持 query session，但必须是有效 session。
2. 其他 `/api/*` 接口必须提供有效 `X-Session-Id`，否则返回 401。
3. 不再从 `X-User-Id` 或默认 `user_01` 推断登录态。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`
  - 修改 `user_middleware()`。
  - 增加公开路径判断。
  - 无效 session 返回 `JSONResponse(status_code=401, ...)`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/services/api.ts`
  - 不再默认发送 `X-User-Id: user_01`。
  - API baseURL 改为读取 `import.meta.env.VITE_API_BASE`，默认 fallback 为本地接口。

### 边界条件

- 登录、注册、演示用户入口不能被 401 阻断。
- 已登录用户依靠 localStorage 中的 `sessionId` 正常访问。
- 旧的 `currentUserId` 仅用于前端显示和兼容，不再作为后端身份来源。

## 需求二：限制用户列表与 demo 切换入口

### 场景与处理逻辑

当前 `/api/users` 可直接拉取全站用户，`/api/users/me/switch` 可接受任意 `user_id` 创建 session。修复目标是降低数据暴露与任意冒充，同时保留 hackathon demo 的体验用户选择能力。

处理逻辑：

1. `/api/users` 需要有效 session，且仅返回脱敏字段。
2. `/api/users/me/switch` 仅允许切换到固定演示用户：`user_01`、`user_bowen`、`user_02`、`user_03`。
3. 不允许通过 switch 切换到任意注册用户或数据库中的其他用户。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/users.py`
  - `list_users(request)` 增加 request 入参，依赖中间件鉴权。
  - 增加 `DEMO_USER_IDS` 白名单。
  - `switch_user()` 校验白名单。

### 边界条件

- Bowen 必须保留为演示用户。
- 手机号注册/登录的真实用户不能被 switch 接口冒充。

## 需求三：修复 match detail 越权读取

### 场景与处理逻辑

当前 `/api/match/{match_id}/detail` 在找不到 match 记录时会把 `match_id` 当作 `other_user_id` 查询，这是 demo 兼容分支，但会导致传任意 user_id 读取对方画像。

处理逻辑：

1. 只允许使用真实 match id 查询。
2. match 必须存在。
3. 当前用户必须是 `user_a` 或 `user_b`。
4. 不满足条件返回错误，不读取对方画像。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/match.py`
  - 删除 direct user_id fallback。
  - 增加参与者校验。

## 需求四：通知标记已读增加归属校验

### 场景与处理逻辑

当前 `POST /api/notifications/{id}/read` 只按 id 更新，任意用户可标记任意 insight 已读。

处理逻辑：

- 从 `request.state.user_id` 获取当前用户。
- SQL 改为 `UPDATE insights SET is_read=1 WHERE id=? AND user_id=?`。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`
  - `mark_read(notification_id, request)`。

## 需求五：match like 写入使用事务兜底

### 场景与处理逻辑

当前 like 流程查询对方、查询已有记录、查询反向 pending、更新/插入之间没有显式事务。上一轮已添加唯一索引，本轮继续在写入段增加事务，降低中间状态风险。

处理逻辑：

- 在需要更新 mutual 或插入 pending 时使用 `BEGIN IMMEDIATE`。
- 在事务内再次检查已有关系，避免并发窗口。
- 提交失败时回滚并关闭连接。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/match.py`
  - 调整 `match_action()` 中 `like` 分支。

## 需求六：Decision parse 失败不落原始 LLM 输出

### 场景与处理逻辑

`agents/base.py` 和 `agents/protocol.py` 中如果 LLM 决策解析失败，可能把原始 Markdown/调试输出塞进 `reasoning`，后续 `AgentMemory` 可能落库并展示给用户。

处理逻辑：

- parse 失败时 `reasoning` 置空或固定为安全短文本。
- 保留内部异常处理，不把 raw LLM 输出进入用户可见数据链路。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/agents/base.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/agents/protocol.py`

## 需求七：补齐明显前端/画像 bug

### 场景与处理逻辑

处理本轮低风险但明确的功能问题：

1. `frontend/src/services/api.ts` baseURL 支持 `VITE_API_BASE`。
2. `backend/skills/vector_skill.py` 新用户没有餐食时也把 0 向量写入 `users.taste_vector`。
3. `frontend/src/pages/Settings.tsx` 隐私设置失败时给出提示并回滚状态。
4. `frontend/src/pages/CityMap.tsx` tooltip 从 `p.data.value` 读取，避免 NaN。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/services/api.ts`
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/vector_skill.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Settings.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx`

## 验证方案

- 后端：`python3 -m py_compile` 检查修改过的 Python 文件。
- 前端：`npm run build`。
- API smoke：
  - 无 session 访问 `/api/meals` 返回 401。
  - `/api/auth/register` 与 `/api/auth/phone-login` 不被 401 阻断。
  - `/api/users/me/switch` 只允许四个演示用户。
  - `/api/match/{user_id}/detail` 不再允许 direct user_id 查询。
  - 通知已读只更新当前用户记录。

## 预期结果

- 不再默认把未登录请求当作 `user_01`。
- 用户列表和演示切换入口不再暴露任意用户冒充能力。
- match detail 不再越权读取任意用户画像。
- 通知已读不能跨用户操作。
- match like 在数据库唯一索引之外增加事务保护。
- LLM parse 失败不会把原始输出展示给用户。
- 前端 API 配置、隐私失败提示、城市 tooltip、新用户向量写入更稳。