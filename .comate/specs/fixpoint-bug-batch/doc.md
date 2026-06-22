# fixpoint.txt 问题批量修复说明

## 背景
用户提供 `/Users/libowen/Desktop/one-bite-one-world/fixpoint.txt`，其中列出前后端在路由、渲染、数据契约、登录会话、安全和健壮性方面的 20 个问题。需要基于现有项目状态进行修复。

当前项目已有部分问题在上一轮城市模块修复中完成：

- #1 城市地图点击区县跳转到首页：已通过新增 `CityDistrict.tsx` 和 `/city/district/:id` 路由修复。
- #10 heatmap 接口调用 `trend_skill` 但结果丢弃：尚未处理，可在本轮修复。
- #11 get_district 内层 break 未跳出外层循环：尚未处理，可在本轮修复。

## 修复范围分类

### 本轮计划修复的问题

#### P1：SSE 通知未读数用户错乱
对应 fixpoint：#2

问题：
- `frontend/src/components/Layout.tsx` 通过 `EventSource` 连接 `/api/notifications/stream`。
- 浏览器原生 `EventSource` 不能自定义 Header，所以前端把身份放到 query 参数 `x_user_id` / `x_session_id`。
- 后端 `backend/main.py` 中间件只读取 Header，不读取 query。
- `backend/routers/notifications.py` 的 `notification_stream` 使用 `request.state.user_id`，导致 SSE 流默认落到 `user_01`。

修复：
- 前端使用 `URLSearchParams` 拼接 SSE query，避免 `?&x_user_id=...`。
- 后端 `notification_stream` 显式解析 query：
  - 如果 `x_session_id` 在 `SESSION` 中，优先使用 session 对应用户。
  - 否则使用 `x_user_id`。
  - 最后回退 `request.state.user_id`。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`

#### P1：餐食图片保存但前端不展示，且列表接口内联 base64 导致 payload 过大
对应 fixpoint：#4

问题：
- `backend/routers/meals.py` 的列表接口 `list_meals` 会读取每张图片并 base64 返回。
- `MealResult.tsx` 和 `MealHistory.tsx` 没有渲染 image 字段。
- 造成用户看不到上传图片，同时列表接口 payload 过大。

修复：
- 后端新增单独取图接口：`GET /api/meals/{meal_id}/image`。
- `list_meals` 不再读取和返回 base64 图片，改为返回轻量字段：`image_url` 或 `has_image`。
- `get_meal` 保留 image base64，保证详情页可直接展示。
- `MealResult.tsx` 展示详情中的 `meal.image`。
- `MealHistory.tsx` 使用 `GET /api/meals/{id}/image` 按需加载缩略图地址，避免列表接口超大。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.css`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealHistory.tsx`

#### P2：MealResult 口味标签展示 0 值空进度条
对应 fixpoint：#5

问题：
- `MealResult.tsx` 直接 `Object.entries(meal.taste_tags).map(...)`。
- 0 或极小值也渲染进度条，视觉上出现一排空条。

修复：
- 过滤 `(Number(v) || 0) > 0.05` 的维度再展示。
- 若全部过滤后为空，显示一条弱提示文案。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`

#### P2：营养字段可能是字符串导致展示异常
对应 fixpoint：#6

问题：
- AI 可能返回 `"350kcal"`、`"20g"` 这样的字符串。
- 前端直接拼单位，可能出现 `350kcal千卡`。

修复：
- 后端保存前对 `nutrition` 做数字清洗，提取首个数字。
- 前端展示时也做 `Number` 兜底，避免异常值直接展示。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`

#### P1：重复点赞写入 matches 脏数据
对应 fixpoint：#7

问题：
- `matches` 表没有 `(user_a, user_b)` 唯一约束。
- `INSERT OR IGNORE` 不会触发 ignore。
- 同一用户反复 like 同一对象会插入多条 pending。

修复：
- 不直接改 SQLite 表结构，避免迁移风险。
- 在 `match_action` 写入前查询当前方向是否已有记录。
- 如果已有 pending/mutual，直接返回已有状态，不重复插入。
- 保留互相点赞时 pending → mutual 的逻辑。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/match.py`

#### P1：pending 列表语义混杂
对应 fixpoint：#8

问题：
- `/match/list?status=pending` 同时返回：
  - 我主动 like，对方未回应。
  - 对方 like 我，等我确认。
- 前端无法区分方向。

修复：
- 后端返回 `direction` 字段：
  - `outgoing`: 我发起，等待对方。
  - `incoming`: 对方发起，等待我。
- 前端 `MatchList.tsx` 展示方向提示。
- 保持原有 tab 结构，不做大规模交互改造。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/match.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MatchList.tsx`

#### P2：private 用户仍可被构造请求点赞
对应 fixpoint：#9

问题：
- discover 过滤 private 用户，但 `/match/{other_user_id}/action` 不校验对方 privacy。
- 如果客户端直接构造请求，仍能写入 matches。

修复：
- `match_action` 写库前查询对方 `privacy_level`。
- 如果对方是 private，返回 `success:false`，不写入。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/match.py`

#### P2：heatmap 接口死代码
对应 fixpoint：#10

问题：
- `backend/routers/city.py` 中 `get_heatmap` 调用 `trend_skill`，但结果未使用。

修复：
- 删除无用调用，降低接口开销。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/city.py`

#### P2：get_district 找到区县后未跳出外层循环
对应 fixpoint：#11

问题：
- 只 break 内层循环，外层 city 继续遍历。

修复：
- 找到区县后整体停止遍历。
- 同步记录所属 city/city_name，返回给前端详情页展示。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/city.py`

#### P2：Login 拉取 /users 后结果被忽略
对应 fixpoint：#13

问题：
- `Login.tsx` 请求 `/users`，但无论返回什么都 `setUsers(HERO_USERS)`。
- 该请求没有实际意义。

修复：
- 删除无用请求与相关 effect。
- 保持固定体验用户入口，避免把大量用户塞入登录页。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.tsx`

#### P2：SocialDiscover 点赞失败仍切下一张
对应 fixpoint：#17

问题：
- `handleLike` 发请求后立即 `setCurrentIdx + 1`。
- 请求失败时用户无感知且 like 丢失。

修复：
- 增加 action loading 状态。
- like 成功后再切下一张。
- 失败时展示 alert 或错误文案，不切换。

受影响文件：
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/SocialDiscover.tsx`

### 本轮不改或暂缓的问题

#### #1 城市区县死链
状态：已在上一轮城市模块修复中完成。

#### #3 MatchList 使用 user_id 进入详情
状态：当前项目已把后端按 user_id 兜底作为 demo 逻辑使用。该问题属于语义一致性，不影响功能。本轮在 #8 中补充 direction，不改 URL 语义，避免引入更大变更。

#### #12 SESSION 内存字典与 X-User-Id 可冒充
状态：架构级鉴权问题。正式修复需要 JWT 或持久化 session，会影响登录、注册、切换用户、请求拦截器等多个模块。本轮不做大改。

#### #14 硬编码 AI API Key
状态：不修改。
原因：
- 当前会话已有明确约束：不要移除 `backend/config.py` 中硬编码 API key fallback。
- 已触发安全能力，但硬编码凭证修复与托管当前未开放。
- 因此仅记录风险，不执行修改。

#### #15 错误响应规范统一
状态：全局接口规范重构，影响较大，本轮不改。

#### #16 上传图片服务端大小/类型校验
状态：安全增强项。可后续单独做完整边界校验。本轮聚焦用户可见 bug 和低风险修复。

#### #18 WeeklyReport 打字机性能
状态：非功能 bug，本轮不改。

#### #19 多处 catch 静默吞错
状态：全局体验优化，本轮不做全量改造。

#### #20 CityMap 经纬度 cartesian2d 非真实地图
状态：需要引入真实 geo/地图数据，超出本轮 bug 修复范围。

## 架构与技术方案

### 后端

#### notifications.py
- 新增 query 身份解析函数：
```py
def _resolve_stream_user_id(request: Request) -> str:
    session_id = request.query_params.get("x_session_id", "")
    if session_id and session_id in SESSION:
        return SESSION[session_id]
    return request.query_params.get("x_user_id") or request.state.user_id
```
- `notification_stream` 使用该 user_id。

#### meals.py
- 新增数字清洗 helper：
```py
def _to_number(value, default=0):
    ...
```
- 保存 recognition 前清洗 nutrition。
- `list_meals` 删除图片 base64 读取，只返回 `has_image`。
- 新增 `GET /{meal_id}/image` 返回图片 base64，仅按需读取。

#### match.py
- `match_action`：
  - 校验对方用户存在且不是 private。
  - 写入前查询同方向已存在记录。
  - 已存在则返回已有状态。
- `match_list`：
  - 返回 `direction` 字段。

#### city.py
- 删除 `get_heatmap` 未使用的 `trend_skill` 调用。
- 修复 `get_district` 查找逻辑，找到后停止，并返回 city 信息。

### 前端

#### Layout.tsx
- 用 `URLSearchParams` 拼接 SSE 参数。
- 保持 EventSource 机制不变。

#### MealResult.tsx / MealResult.css
- 显示上传图片。
- 过滤低值 taste tags。
- 营养字段数字兜底。

#### MealHistory.tsx
- 展示餐食缩略图。
- 图片按需用 `/meals/{id}/image` 获取，不依赖列表内联 base64。

#### MatchList.tsx
- 展示 pending 方向：等待对方 / 待你确认。

#### Login.tsx
- 删除无用 `/users` 请求。

#### SocialDiscover.tsx
- like 成功后再进入下一张。
- 请求失败时提示，不丢失当前卡片。

## 边界条件与异常处理

- 不修改 `backend/config.py` 中 API key fallback。
- 不修改 Bowen 用户。
- 不引入新依赖。
- 不改变主要接口路径，新增接口仅补充图片按需读取。
- 图片不存在时返回 `success:false` 或前端不显示缩略图。
- 重复 like 不产生重复记录。
- private 用户拒绝被直接 like。
- SSE 若 query 缺失仍回退 `request.state.user_id`。

## 数据流路径

### 通知未读数
`Layout.tsx` → `EventSource /api/notifications/stream?x_user_id=&x_session_id=` → `notifications.py` query/session 解析 → `_get_unread_count(user_id)`

### 餐食图片
上传：`ImageUpload` → `/api/meals` → 保存图片文件 → meal detail 返回 image
历史：`MealHistory` → `/api/meals?limit=50` → 轻量列表 → `/api/meals/{id}/image` 按需取图
详情：`MealResult` → `/api/meals/{id}` → 渲染 image

### 匹配
`SocialDiscover` → `/api/match/{other_user_id}/action` → 校验 privacy / 查重 / 写入或更新
`MatchList` → `/api/match/list?status=pending` → 返回 direction → 前端展示方向

## 预期结果

- 顶部通知未读数与当前登录用户一致。
- 餐食详情和历史记录能看到上传图片。
- 餐食列表接口 payload 明显变小，不再内联 50 张 base64 图片。
- MealResult 不再显示大量 0% 空口味条。
- 营养字段不会出现 `350kcal千卡` 之类重复单位。
- 重复点赞不再写入多条 pending。
- pending 匹配能看出方向。
- private 用户不能被构造请求直接点赞。
- 城市 heatmap 删除无用调用，district 查询更稳定。
- 前端构建通过，后端关键文件语法检查通过。
