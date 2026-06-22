# 前后端循环优化第一轮方案

## 背景

用户希望启动一个循环任务：不断优化网页前端和后端逻辑，顺序为：

```text
发现问题 -> 修正 -> 测试 -> 继续发现问题
```

由于“直到完美”没有客观停止条件，本轮采用可执行的收敛策略：

1. 先进行问题审查。
2. 按优先级修复高影响问题。
3. 执行构建和关键 API 验证。
4. 输出总结和下一轮待优化项。

本轮聚焦真实用户最容易感知、且代码风险可控的问题，不做大规模架构重写。

## 已发现的高优先级问题

经过代码审查，当前最值得先修的前后端问题包括：

### 问题一：通知未读数闭环不完整

#### 当前表现

用户进入通知中心并点击通知后，通知项本地变为已读，但顶部铃铛的未读数可能不会立即减少。

#### 相关文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Notifications.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`

#### 原因

当前 SSE 逻辑主要在未读数增加时推送，减少时不一定推送；前端通知页标记已读后也没有通知 Layout 更新铃铛数字。

#### 修复方案

- 后端 SSE 改为“未读数变化就推送”，包括增加和减少。
- 前端在通知页标记已读后派发自定义事件，例如 `notifications:unread-delta`。
- Layout 监听该事件，即时更新 `unreadCount`。
- 保留 SSE 作为最终同步来源。

#### 预期结果

用户点击已读后，铃铛数字立即减少，不需要刷新页面。

---

### 问题二：图片 MIME 链路不闭环

#### 当前表现

后端支持 JPG、PNG、WebP 上传和保存，但前端结果页、历史页图片渲染时固定使用：

```tsx
data:image/jpeg;base64,...
```

如果用户上传 PNG/WebP，可能出现显示异常。

#### 相关文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealHistory.tsx`

#### 修复方案

- 后端根据 `image_url` 扩展名推导 `image_mime`。
- `/api/meals/{meal_id}` 返回 `image_mime`。
- `/api/meals/{meal_id}/image` 返回 `image` 和 `mime_type`。
- `/api/meals/images` 批量接口返回每个 meal 的 `{ image, mime_type }`。
- 前端结果页和历史页按 mime_type 组装 data URL。
- 兼容旧格式：如果返回仍是字符串，则默认 `image/jpeg`。

#### 预期结果

JPG、PNG、WebP 在结果页、刷新后的详情页和历史页都能正常展示。

---

### 问题三：手动补录没有触发完整 Agent 编排

#### 当前表现

自动图片识别保存餐食后会触发：

```text
vector_skill -> AgentEvent(meal.uploaded) -> orchestrator -> proactive_notify_skill
```

但手动补录只触发向量更新和固定文案通知，没有走同等级 Agent 编排。

#### 相关文件

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/agents/orchestrator.py`

#### 修复方案

- 手动补录成功后也构造 `AgentEvent(event_type="meal.uploaded")`。
- event data 中增加 `source: "manual"`、`manual_created: True`。
- micro insight 由 orchestrator 返回，失败时再使用兜底固定文案。
- 继续保留 `proactive_notify_skill` 通知落库。

#### 预期结果

AI 识别失败后手动补录的用户，也能得到和自动识别路径一致的 Agent 洞察闭环。

---

### 问题四：启动脚本没有执行权限，运行体验不稳定

#### 当前表现

执行 `./start.sh` 时可能出现：

```text
permission denied: ./start.sh
```

之前只能改用 `bash ./start.sh`。

#### 相关文件

- `/Users/libowen/Desktop/one-bite-one-world/start.sh`

#### 修复方案

- 不修改脚本内容，使用系统命令设置执行权限：

```bash
chmod +x start.sh
```

#### 预期结果

后续可以直接执行：

```bash
./start.sh
```

---

## 本轮不处理但记录的问题

以下问题重要，但涉及范围更大，留到下一轮：

1. 业务失败大量返回 `200 + success:false`，需要统一 HTTP 错误语义。
2. session 只在内存中，后端 reload 会丢登录态，需要 SQLite/Redis/JWT 方案。
3. Agent trace 不可视化，难以对外展示每次事件触发了哪些 skills。
4. 页面样式仍有较多内联样式，长期需要统一 CSS 组件化。
5. 周报反馈学习逻辑过粗，容易把所有 taste vector 维度一起微调。

这些问题会进入后续循环优化轮次。

## 受影响文件

### 后端

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`
  - 修改 SSE 未读数变化推送逻辑。
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
  - 增加图片 MIME 推导和返回。
  - 手动补录触发 AgentEvent。

### 前端

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.tsx`
  - 监听通知已读事件并更新铃铛数字。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Notifications.tsx`
  - 标记已读成功后派发未读数变化事件。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`
  - 使用后端返回 MIME 渲染图片。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealHistory.tsx`
  - 兼容批量图片接口的新返回格式。

### 运行脚本

- `/Users/libowen/Desktop/one-bite-one-world/start.sh`
  - 设置执行权限，不改内容。

## 验证计划

### 后端语法验证

```bash
python -m py_compile routers/meals.py routers/notifications.py
```

### 前端构建验证

```bash
npm run build
```

### API 验证

1. 后端根接口：

```bash
curl http://localhost:8000/
```

2. demo session：

```bash
PUT /api/users/me/switch
```

3. 手动补录：

```bash
POST /api/meals/manual
```

4. 餐食详情：

```bash
GET /api/meals/{meal_id}
```

确认返回 `image_mime` 或兼容字段。

5. 通知已读：

```bash
POST /api/notifications/{id}/read
```

### 手动验证

1. 打开页面进入通知中心，点击未读通知，观察铃铛数字是否减少。
2. 上传或手动补录一餐，确认结果页仍正常显示。
3. 历史记录中图片仍正常显示。
4. 直接执行 `./start.sh` 不再 permission denied。

## 收敛标准

本轮完成标准：

- 上述 4 个高优先级问题完成修复。
- 前端构建通过。
- 后端语法检查通过。
- 核心 API 可访问。
- 生成本轮 `summary.md`，并列出下一轮优化建议。
