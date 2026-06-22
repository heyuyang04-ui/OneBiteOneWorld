# fixpoint-experience-stability-batch 修复总结

## 本轮处理范围

根据新版 `/Users/libowen/Desktop/one-bite-one-world/fixpoint.txt`，本轮继续处理用户可见体验、性能与稳定性问题。

已处理：

- BUG-8：`meal_companion_skill` 向量缺失时固定返回“火锅/烤鱼”。
- BUG-9：`city/trends` 同步调用 AI 且无缓存。
- BUG-11：`WeeklyReport` feedback 的 highlight id 不真实。
- BUG-13：首页 quick-actions 按钮无反馈。
- BUG-14：`MealHistory` 图片 N+1 请求。
- BUG-21：notifications SSE 服务端无限循环，不检测客户端断开。
- BUG-22：vision `max_tokens=2000` 偏小。
- BUG-23：Layout SSE 前端无限自动重连。
- BUG-26：上传失败或非食物后预览图不清空。

未处理：

- BUG-1：硬编码 AI API Key。按此前约束保留 `backend/config.py` fallback。
- BUG-3：短信验证码/密码/JWT 属于认证产品方案变更。
- BUG-16：SESSION Redis/TTL 属于部署架构变更。
- BUG-17：match 方向规范化会改变已有有向匹配语义，需要单独评估。
- P3 大型重构类问题本轮不做。

## 修改文件

### 后端

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/meal_companion_skill.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/city.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/report_skill.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/services/__init__.py`

### 前端

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/WeeklyReport.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealHistory.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/ImageUpload.tsx`

## 完成内容

### 1. 饭搭子兜底推荐不再固定

- `meal_companion_skill.py` 在双方 taste_vector 缺失或不足时，读取 `tags`、`occupation`、`city`。
- 根据共同标签推断：
  - 肉食/蛋白质：烤肉、牛肉饭、铜锅涮肉。
  - 辣/重口：川味小炒、烤鱼、火锅。
  - 甜口：甜品咖啡、下午茶。
  - 轻食/控卡：轻食饭、鸡胸肉沙拉。
- 无共同信号时，不再编造固定菜单，而是提示先记录更多餐食。

### 2. city trends 增加 5 分钟缓存

- `city.py` 增加模块级 `_trends_cache`。
- 使用 `(city, dimension)` 作为 key。
- TTL 为 300 秒。
- 缓存命中时直接返回，不重复调用趋势 skill。

### 3. WeeklyReport feedback 使用真实 highlight id

- `report_skill.py` 为每条 highlight 增加稳定 id：`weekly_{index}_{hash}`。
- `WeeklyReport.tsx` 优先使用 `h.id` 提交反馈。
- 反馈点击后显示“提交中 / 已记录反馈 / 反馈提交失败”。

### 4. 首页 quick-actions 有反馈

- `Home.tsx` 为四个 quick-action 绑定点击处理。
- 点击后展示 Agent 已接收意图的文字反馈。
- 不新增后端 API，保持最小改动。

### 5. MealHistory 图片批量加载

- `meals.py` 新增：

```text
GET /api/meals/images?ids=a,b,c
```

- 最多处理 30 个 id。
- 只返回当前登录用户自己的图片。
- `MealHistory.tsx` 从最多 20 个单图请求改为一次批量请求。
- 保留原 `/meals/{meal_id}/image` 单图接口。

### 6. SSE 断开检测与重连限制

- `notifications.py` 的 SSE generator 在循环中检查：

```py
await request.is_disconnected()
```

- 客户端断开后退出循环。
- `Layout.tsx` 对 EventSource 增加连续错误计数。
- 连续 5 次错误后关闭 EventSource，避免无限自动重连。

### 7. 视觉识别 token 与上传失败预览

- `AIClient.vision()` 的 `max_tokens` 从 2000 提升到 4000。
- `ImageUpload.tsx` 增加 `resetKey` prop。
- `Home.tsx` 在以下场景递增 `resetKey` 清空预览：
  - 上传失败。
  - 非食物。
  - 识别结果异常。
  - 网络异常。

## 验证结果

### 后端编译

命令：

```bash
python3 -m py_compile backend/skills/meal_companion_skill.py backend/routers/city.py backend/skills/report_skill.py backend/routers/meals.py backend/routers/notifications.py backend/services/__init__.py
```

结果：通过。

### 前端构建

命令：

```bash
npm run build
```

结果：通过。

说明：Vite 仍有已有 chunk size warning，不影响构建成功。

### API smoke

后端重启后执行：

```text
/city/trends?city=beijing&dimension=spicy 200 True
/city/trends?city=beijing&dimension=spicy 200 True
/meals?limit=5 200 True
/meals/images 200 True ['meal_84e353d5']
```

结论：

- city trends 连续请求成功，缓存逻辑未破坏返回结构。
- 批量图片接口返回成功，并能返回当前用户图片 map。
- 前后端编译均通过。

## 当前服务

后端已重启，当前任务：

```text
xo7ft8
```

前端服务仍运行：

```text
http://localhost:5173/
```

当前前端 Vite 已热更新；如需确认完整运行态，可刷新页面。

## 任务状态

`.comate/specs/fixpoint-experience-stability-batch/tasks.md` 中 8 个顶层任务均已完成。