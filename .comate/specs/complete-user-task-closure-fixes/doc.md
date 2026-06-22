# 完成真实用户任务闭环修复说明

## 背景与目标

本轮修复继续处理 `项目修正总览.md` 中尚未落地、但直接影响真实用户完成任务的体验缺陷。当前应用已经具备登录、拍照识别、结果展示、历史记录、味觉匹配和城市模块，但仍存在几个关键断点：

1. AI 识别失败后只弹出 `alert`，且会清空用户已经选择的图片和描述，用户无法直接重试或手动补录。
2. MealResult 结果页无法纠错，识别错误会长期污染个人味觉档案、周报和匹配结果。
3. MealHistory 只能浏览列表，缺少进入详情、删除误记录等基础管理能力。
4. App 启动时仅根据 `currentUserId` 判断是否已登录，没有校验 `sessionId` 是否仍可用，容易进入页面后接口再 401。
5. 匹配卡片只解释相似度，缺少“为什么推荐”和“第一次吃什么”的行动建议，不符合“Agent 替人感知”的产品定位。

目标是补齐从“上传失败/识别错误/历史误记录/登录过期/匹配后行动”这些真实用户链路中的断点，使体验从 demo 展示更接近可用产品。

## 项目上下文

- 前端路径：`/Users/libowen/Desktop/one-bite-one-world/frontend`
- 后端路径：`/Users/libowen/Desktop/one-bite-one-world/backend`
- 前端技术栈：React 19、TypeScript、Vite、React Router、Axios
- 后端技术栈：FastAPI、SQLite、aiosqlite、Pydantic
- 当前会话标识：前端 `localStorage.sessionId`，请求头 `X-Session-Id`
- 当前用户标识：前端 `localStorage.currentUserId`
- 持久化表：`meals` 表包含 `dish_name`、`cuisine_type`、`ingredients`、`taste_tags`、`nutrition`、`image_url` 等字段
- 重要约束：保留 `backend/config.py` 中硬编码 AI API key fallback，不在本轮修改该配置
- 重要 demo 角色：保留 Bowen 用户，不删除或重命名

## 需求一：AI 识别失败兜底

### 场景与处理逻辑

用户选择图片并输入描述后点击“确认识别这一餐”。如果后端返回识别失败、非食物、网络异常或 AI 服务异常，当前页面不应只弹窗并清空选择，而应保留现场并给出可继续操作的路径：

- 重试当前图片和描述。
- 手动填写菜名、菜系、食材，保存为一餐。
- 更换图片。

### 技术方案

前端在 `Home.tsx` 中新增识别失败状态与手动录入状态：

```tsx
const [recognitionError, setRecognitionError] = useState('')
const [manualMeal, setManualMeal] = useState({ dish_name: '', cuisine_type: '', ingredients: '' })
```

调整 `handleConfirmRecognition`：

- 请求前清空旧错误。
- 请求失败时设置 `recognitionError`，不调用 `resetSelectedImage()`。
- `is_food === false` 时展示内联错误卡片，保留图片。
- 只有用户点击“更换图片”时才重置图片。

新增手动保存方法：

```tsx
await api.post('/meals/manual', {
  dish_name: manualMeal.dish_name,
  cuisine_type: manualMeal.cuisine_type,
  ingredients: manualMeal.ingredients.split(/[，,\n]/).map(x => x.trim()).filter(Boolean),
  description: foodDescription.trim(),
  image: pendingImage || undefined,
})
```

后端新增 `POST /api/meals/manual`，用于用户主动补录：

- 校验 `dish_name` 非空。
- `cuisine_type` 为空时给默认值 `家常/未分类`。
- `ingredients` 为空时保存空数组。
- `taste_tags`、`nutrition` 使用可解释的基础默认值，不调用视觉模型。
- 如带图片，复用现有 `_validate_image` 保存图片。
- 保存后调用 `vector_skill(user_id, {"action": "compute"})` 重算个人味觉向量。

### 受影响文件

- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`
  - 影响函数：`handleConfirmRecognition`、`resetSelectedImage` 相关上传 UI
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.css`
  - 新增识别失败卡片、手动补录表单样式
- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/models/schemas.py`
  - 新增手动创建餐食请求模型
- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
  - 新增 `POST /manual` 接口

### 边界条件与异常处理

- 图片仍按现有限制：JPG/PNG/WebP，最大 5MB。
- 手动补录不依赖 AI 服务，保证 AI 异常时用户仍能完成记录。
- 手动补录时如果图片非法，应返回业务错误而非 500。
- 手动补录保存后的返回结构尽量与上传识别保持一致，前端可跳转到 `/meal/{id}`。

### 数据流

```text
用户选择图片/输入描述
  -> 点击确认识别
  -> AI 识别失败
  -> Home 内联失败卡片
  -> 用户选择重试 / 更换图片 / 手动补录
  -> 手动补录 POST /api/meals/manual
  -> meals 表新增记录
  -> vector_skill 重算
  -> 跳转 MealResult
```

### 预期结果

AI 识别失败不再中断任务，用户可以在同一页面完成记录，减少重复上传和数据丢失。

## 需求二：MealResult 纠错

### 场景与处理逻辑

用户进入识别结果页后，如果菜名、菜系或食材识别不准确，应可直接点击“纠正这一餐”，修改核心字段并保存。保存后当前页面即时更新，并触发味觉向量重算，避免错误结果继续影响报告和匹配。

### 技术方案

后端新增 `PUT /api/meals/{meal_id}`：

- 查询餐食是否存在。
- 校验 `row.user_id == request.state.user_id`。
- 允许更新：
  - `dish_name`
  - `cuisine_type`
  - `ingredients`
  - `taste_tags`
  - `nutrition`
- 保存 JSON 字段时使用 `json.dumps(..., ensure_ascii=False)`。
- 更新后调用 `vector_skill` 重算。
- 返回更新后的 meal payload。

前端 `MealResult.tsx` 新增纠错面板：

- 默认折叠。
- 点击“纠正这一餐”展开表单。
- 表单字段：菜名、菜系、食材。
- 保存成功后更新本地 `meal` 状态。
- 保存失败时展示内联错误，不跳出页面。

### 受影响文件

- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/models/schemas.py`
  - 新增餐食更新请求模型
- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
  - 新增 `PUT /{meal_id}` 接口
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`
  - 新增纠错 UI、保存逻辑、状态更新
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.css`
  - 新增纠错面板样式

### 边界条件与异常处理

- 不能修改不属于当前用户的餐食。
- 菜名不能为空。
- 食材支持中文逗号、英文逗号、换行分隔。
- 如果用户从历史页直接进入详情，仍应能加载图片并纠错。
- 更新失败时不清空表单。

### 数据流

```text
MealResult 展示识别结果
  -> 用户点击纠正
  -> 修改菜名/菜系/食材
  -> PUT /api/meals/{meal_id}
  -> 权限校验
  -> 更新 meals 表
  -> vector_skill 重算
  -> 前端局部刷新 meal
```

### 预期结果

识别错误可被用户修正，味觉档案更可信，减少“AI 不准但无法改”的挫败感。

## 需求三：MealHistory 管理能力

### 场景与处理逻辑

用户查看历史记录时，应能：

- 点击某条记录进入详情页。
- 删除误上传或不想保留的记录。
- 看到删除过程和失败反馈。

### 技术方案

前端 `MealHistory.tsx`：

- 引入 `useNavigate`。
- 将历史项改为可点击卡片，点击跳转 `/meal/{id}`。
- 添加“删除”按钮，点击时 `stopPropagation()`，调用已有 `DELETE /api/meals/{meal_id}`。
- 删除成功后从列表和图片缓存中移除。
- 删除前使用浏览器确认，避免误删。

后端已有 `DELETE /api/meals/{meal_id}`，本轮复用，不新增删除接口。

### 受影响文件

- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealHistory.tsx`
  - 影响列表渲染、事件处理、删除状态
- 如存在样式文件则修改对应 CSS；若当前页面使用内联样式，则优先保持最小改动，不强行大规模重构

### 边界条件与异常处理

- 删除按钮不能触发跳转。
- 删除失败时保留列表项并显示错误。
- 空状态保持原有文案。
- 图片加载失败不影响进入详情和删除。

### 数据流

```text
MealHistory 拉取 /api/meals
  -> 用户点击卡片
  -> navigate('/meal/{id}')

用户点击删除
  -> DELETE /api/meals/{meal_id}
  -> 后端删除 DB 和本地图片
  -> 前端移除列表项
```

### 预期结果

历史记录从展示列表变成可管理入口，用户可以回看、纠错、清理误记录。

## 需求四：App 启动 session 恢复校验

### 场景与处理逻辑

当前 `ProtectedLayout` 只检查 `localStorage.currentUserId`。如果用户本地残留 `currentUserId` 但后端 `SESSION` 已因重启丢失，页面会进入应用内部，随后接口返回 401。应在进入受保护页面前校验 `sessionId` 是否可用。

### 技术方案

修改 `frontend/src/App.tsx` 的 `ProtectedLayout`：

- 同时读取 `currentUserId` 和 `sessionId`。
- 缺任意一个则重定向 `/login`。
- 首次渲染时调用 `/api/users/me`。
- 校验中展示轻量加载态。
- 校验成功后渲染 `<Layout />`。
- 校验失败或 401：清除 `currentUserId`、`sessionId`，跳转 `/login`。

伪代码：

```tsx
function ProtectedLayout() {
  const saved = localStorage.getItem('currentUserId')
  const sessionId = localStorage.getItem('sessionId')
  const [checking, setChecking] = useState(Boolean(saved && sessionId))
  const [valid, setValid] = useState(false)

  useEffect(() => {
    if (!saved || !sessionId) return
    api.get('/users/me')
      .then(res => setValid(Boolean(res.data.success)))
      .catch(() => {
        localStorage.removeItem('currentUserId')
        localStorage.removeItem('sessionId')
        setValid(false)
      })
      .finally(() => setChecking(false))
  }, [])

  if (!saved || !sessionId) return <Navigate to="/login" replace />
  if (checking) return <div className="app-shell-checking">正在恢复味觉档案...</div>
  if (!valid) return <Navigate to="/login" replace />
  return <Layout />
}
```

### 受影响文件

- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx`
  - 影响函数：`ProtectedLayout`
- 可能修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.css`
  - 新增加载态样式

### 边界条件与异常处理

- 后端服务未启动时应回到登录页，不停留空白屏。
- 校验期间不应闪现应用内部页面。
- 成功登录/注册后仍沿用现有 localStorage 写入逻辑。

### 数据流

```text
访问 /home 或内部路由
  -> ProtectedLayout 检查 currentUserId + sessionId
  -> GET /api/users/me
  -> 成功：渲染 Layout
  -> 失败：清理 localStorage，回到 /login
```

### 预期结果

后端重启或 session 失效后，用户会明确回到登录页，不再出现“看似登录但所有接口失败”的体验。

## 需求五：匹配推荐解释增强

### 场景与处理逻辑

匹配卡片目前只显示共同点、差异和一句泛化解释。用户需要知道：

- 为什么推荐这个人。
- 第一顿饭适合吃什么。
- 如何低压力开启交流。

### 技术方案

后端在 `GET /api/match/discover` 返回结果中为前几条 match 补充字段：

```py
m["why_recommended"] = ...
m["first_meal_suggestion"] = ...
m["conversation_starter"] = ...
```

字段生成基于已有 `common`、`diff`、`score`、用户标签，不新增大模型调用，保证响应速度。

示例：

```text
why_recommended: 你们都偏好重口味和中式热菜，但 TA 在清淡/探索维度上略高，可以帮你打开新菜系。
first_meal_suggestion: 第一次可以从川湘小馆、烧烤或热汤面开始，选择可分享的小份菜更容易交流。
conversation_starter: 可以问 TA 最近有没有吃到一道“看起来普通但很上头”的菜。
```

前端 `MatchCard.tsx` 扩展 props 并渲染三段 Agent 建议：

- 为什么推荐
- 第一餐建议
- 开场问题

### 受影响文件

- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/routers/match.py`
  - 影响函数：`_build_match_explanation`、`discover_matches`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/backend/models/schemas.py`
  - 扩展 `MatchResponse` 可选字段
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/MatchCard.tsx`
  - 扩展 props 和展示区域
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/MatchCard.css`
  - 新增 Agent 建议卡片样式

### 边界条件与异常处理

- `common` 为空时使用“饮食节奏/城市味觉信号”等兜底表达。
- `diff` 为空时不强行渲染差异。
- 后端新增字段为可选，前端兼容旧数据。

### 数据流

```text
SocialDiscover 请求 /api/match/discover
  -> match_skill 计算候选
  -> match router 补充 why/first meal/starter
  -> MatchCard 展示 Agent 解释
```

### 预期结果

匹配页从“看分数滑卡”变成“Agent 给出可执行社交建议”，更贴近 L2 味觉社交网络定位。

## 验证计划

### 前端构建验证

在 `/Users/libowen/Desktop/one-bite-one-world/frontend` 执行：

```bash
npm run build
```

确认 TypeScript 和 Vite 构建通过。

### 后端接口语法验证

在 `/Users/libowen/Desktop/one-bite-one-world/backend` 执行 Python 语法检查或启动服务验证：

```bash
python -m py_compile routers/meals.py routers/match.py models/schemas.py
```

### 手动功能验证

1. 登录后进入首页。
2. 选择图片和输入描述，模拟识别失败时：
   - 图片仍保留。
   - 错误以内联卡片展示。
   - 可重试。
   - 可手动补录并进入结果页。
3. 进入结果页：
   - 点击纠正这一餐。
   - 修改菜名/菜系/食材。
   - 保存后页面立即更新。
4. 进入历史记录：
   - 点击记录进入详情。
   - 删除记录后列表移除。
5. 清空或伪造 session：
   - 访问 `/home` 自动回到登录页。
6. 进入匹配页：
   - 卡片展示为什么推荐、第一餐建议、开场问题。

## 风险与控制

- 避免引入新表结构，减少数据库迁移风险。
- 手动补录和纠错只改 `meals` 现有字段。
- 删除复用现有接口，不新增后端风险面。
- 匹配解释使用规则生成，不增加 AI 调用成本和等待时间。
- session 校验只影响受保护页面，不改登录/注册接口。
- 不修改 `backend/config.py` 的 AI key fallback。

## 预期交付结果

完成后，应用会具备更完整的真实用户闭环：

- 识别失败能继续完成记录。
- 识别错误能纠正。
- 历史记录能进入详情和删除。
- session 失效能可靠回到登录。
- 匹配推荐能给出可行动的 Agent 建议。
