# fixpoint-experience-stability-batch 需求说明

## 背景

新版 `/Users/libowen/Desktop/one-bite-one-world/fixpoint.txt` 标记了第二轮复审结果。上一轮已处理主要鉴权越权和上传 500 问题。本轮继续修复剩余的用户可见体验、性能和稳定性问题。

本轮处理范围：

- BUG-8：`meal_companion_skill` 在向量缺失时固定返回“火锅/烤鱼”。
- BUG-9：`city/trends` 同步调用 AI 且无缓存。
- BUG-11：`/report/feedback` 与 `WeeklyReport` 的 highlight id 不匹配。
- BUG-13：Home quick-actions 按钮无点击反馈。
- BUG-14：MealHistory 图片 N+1 请求。
- BUG-21：notifications SSE 服务端无限循环，不检测客户端断开。
- BUG-22：vision `max_tokens=2000` 偏小。
- BUG-23：Layout SSE 前端无限自动重连。
- BUG-26：上传失败或非食物后 ImageUpload preview 不清空。

本轮不处理：

- BUG-1：硬编码 AI API Key。按此前约束保留 fallback，不修改 `backend/config.py`。
- BUG-3：短信验证码/密码/JWT 属于认证产品方案变更，不在本轮实现。
- BUG-16：SESSION Redis/TTL 属于部署架构变更，后续单独处理。
- BUG-17：match 方向规范化会改变已有有向匹配语义，后续单独评估。
- P3 大型重构类问题，如 lifespan、连接池、i18n、统一 toast，本轮不做。

## 需求一：meal_companion_skill 向量缺失时不再固定兜底

### 场景与处理逻辑

当前 `meal_companion_skill.py` 中 `_safe_vector()` 如果读取到空向量或坏数据，会返回 `[]`。当 `len(vec_me) < 14 or len(vec_other) < 14` 时，直接返回固定的“火锅/烤鱼”。这会让老数据、手工插入用户或坏数据用户得到完全一样的饭搭子建议。

处理逻辑：

1. 查询用户时同时读取 `tags`、`occupation`、`city`。
2. 当向量不足时，根据双方 tags 推断共同食物：
   - 肉食/高蛋白 → 烤肉、牛肉饭、铜锅涮肉
   - 重口/辣 → 火锅、川味小炒、烤鱼
   - 甜口 → 甜品咖啡、下午茶
   - 控卡/健身 → 轻食饭、鸡胸肉沙拉
   - 无共同信号 → 返回空 shared_foods，并提示“先各自记录几餐”。
3. 不再固定返回同一套结果。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/meal_companion_skill.py`

## 需求二：city/trends 增加短期缓存

### 场景与处理逻辑

`/api/city/trends` 每次都读取 mock_city 并调用 `trend_skill`，如果 AI insight 慢，会让城市趋势页加载慢。复审建议加 5 分钟缓存。

处理逻辑：

1. 为 trends 添加模块级 TTL cache，key 为 `(city, dimension)`。
2. 缓存命中时直接返回数据。
3. 缓存未命中时计算 trends 并调用 `trend_skill`。
4. TTL 设置为 300 秒。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/city.py`

## 需求三：WeeklyReport highlight 使用真实 id

### 场景与处理逻辑

当前前端反馈按钮使用 `insight_id: h_${i}`，这个 id 是前端临时拼的，并不对应后端真实 highlight。后端只是把字符串写进 episodes，无法归因到具体洞察。

处理逻辑：

1. `report_skill` 返回 highlights 时为每条 highlight 增加稳定 id。
2. id 可基于 `user_id`、highlight title、index 生成，例如 `weekly_{index}_{hash}`。
3. 空周报也保持 highlights 为空。
4. `WeeklyReport.tsx` 使用 `h.id || h_${i}`，优先真实 id。
5. 反馈成功后给按钮区域一个轻量状态提示，避免用户不知道是否点击成功。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/report_skill.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/WeeklyReport.tsx`

## 需求四：首页 quick-actions 可点击

### 场景与处理逻辑

首页 quick-actions 四个按钮视觉上可点击，但没有任何行为。

处理逻辑：

1. 为每个 action 添加点击处理。
2. 点击后更新页面上的短提示文案，解释 Agent 接收到意图。
3. 不引入新 API，避免过度设计。
4. 根据 action 关键字给出不同反馈：想吃肉、清淡、新店、饭搭子。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`

## 需求五：MealHistory 图片批量加载，减少 N+1

### 场景与处理逻辑

当前历史记录页最多对 20 条记录发起 20 个 `/meals/:id/image` 请求。复审建议后端提供批量端点或列表返回缩略图。本轮选择最小侵入的批量端点。

处理逻辑：

1. 后端新增 `GET /api/meals/images?ids=a,b,c`。
2. 校验 ids 数量上限，例如最多 30 个。
3. 仅返回当前用户自己的图片。
4. 前端 `MealHistory.tsx` 收集待加载 id 后一次性请求批量端点。
5. 保留单图端点供其它页面使用。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealHistory.tsx`

## 需求六：SSE 服务端检测断开，前端限制重连

### 场景与处理逻辑

后端 SSE `event_generator` 当前无限循环，不检查 `request.is_disconnected()`。前端 EventSource 错误时默认无限自动重连，异常时可能造成连接和 CPU 资源浪费。

处理逻辑：

后端：

1. 在循环开始或 sleep 后检查 `await request.is_disconnected()`。
2. 断开后 `break`。
3. 可设置最多 heartbeat 次数或保持断开检查即可。

前端：

1. EventSource 原生自动重连不可细粒度控制，但可以在 `onerror` 中计数。
2. 连续错误达到阈值后调用 `es.close()`。
3. 避免后端异常时无限重连。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.tsx`

## 需求七：vision max_tokens 增加到 4000

### 场景与处理逻辑

视觉识别任务返回完整 JSON，包含菜名、菜系、食材、6 维口味、4 类营养等。当前 `max_tokens=2000` 偏小，可能被截断导致 JSON 解析失败。本轮仅提升 vision 调用 token，不影响普通 chat。

处理逻辑：

- `AIClient.vision()` 请求体中将 `max_tokens` 从 2000 改为 4000。
- `AIClient.chat()` 保持 2000。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/services/__init__.py`

## 需求八：上传失败后清空预览

### 场景与处理逻辑

当前 ImageUpload 内部管理 preview。上传非食物或服务不可用后，Home 只弹 alert，但预览图仍留在界面上，用户无法明显重新选择。

处理逻辑：

1. 将 ImageUpload 增加 `resetKey?: number` prop。
2. 当 resetKey 变化时清空 preview。
3. Home 上传失败、非食物、结果异常、网络异常时递增 resetKey。
4. 正常识别成功跳转时不需要清空。

### 影响文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/ImageUpload.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`

## 验证方案

- 后端编译：
  - `python3 -m py_compile backend/skills/meal_companion_skill.py backend/routers/city.py backend/skills/report_skill.py backend/routers/meals.py backend/routers/notifications.py backend/services/__init__.py`
- 前端构建：
  - `npm run build`
- API smoke：
  - `/api/city/trends` 连续请求返回成功。
  - `/api/meals/images?ids=...` 返回当前用户图片 map。
  - SSE stream 启动后不会因断开检查报错。
- 前端行为：
  - quick-actions 点击后有反馈。
  - 上传失败后 preview 清空。
  - WeeklyReport feedback 发送真实 highlight id。

## 预期结果

- 饭搭子兜底不再千篇一律。
- 城市趋势页重复访问更快。
- 周报反馈可以绑定真实 highlight id。
- 首页按钮不再是“假按钮”。
- 历史记录图片请求从 N 次降为 1 次批量请求。
- SSE 异常时不会无限消耗资源。
- 视觉识别 JSON 截断概率降低。
- 上传失败后用户可以自然重新选择图片。