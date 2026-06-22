# 前后端循环优化第一轮总结

## 本轮目标

按“发现问题 -> 修正 -> 测试 -> 继续发现问题”的方式，对当前网页前后端逻辑进行第一轮循环优化。本轮聚焦真实用户最容易感知、且修复风险可控的问题。

## 已完成任务

### 1. 修复通知未读数闭环

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Notifications.tsx`

完成内容：

- 后端 SSE 从“仅未读数增加时推送”改为“未读数任意变化时推送”。
- SSE payload 从 `new_count` 改为更通用的 `delta`。
- Layout 监听 `notifications:unread-delta` 自定义事件。
- 通知页点击未读通知且后端标记成功后，派发 `delta: -1`。
- 已读通知重复点击不会继续扣减红点数字。

预期效果：

- 用户点击通知已读后，顶部铃铛数字会立即减少。
- SSE 仍作为服务端最终同步来源。

---

### 2. 修复图片 MIME 链路不闭环

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealHistory.tsx`

完成内容：

- 后端新增 `_image_mime_from_path`，根据图片扩展名推导 MIME。
- 餐食详情 payload 新增 `image_mime`。
- 单图接口 `/api/meals/{meal_id}/image` 返回 `image` 和 `mime_type`。
- 批量图片接口 `/api/meals/images` 返回 `{ image, mime_type }` 结构。
- 上传成功后的 meal payload 直接带 `image_mime`。
- MealResult 使用 `image_mime` / `mime_type` 生成 data URL。
- MealHistory 兼容新结构和旧字符串结构。

预期效果：

- JPG、PNG、WebP 均可在结果页和历史页正确渲染。
- 旧数据仍兼容默认 `image/jpeg`。

---

### 3. 统一手动补录与自动识别的 Agent 编排链路

修改文件：

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`

完成内容：

- 手动补录保存并重算向量后，也构造：

```python
AgentEvent(event_type="meal.uploaded", user_id=user_id, data=event_data)
```

- event data 中加入：

```python
source = "manual"
manual_created = True
```

- 使用 `orchestrator.process_event` 生成 micro insight。
- 如果 orchestrator 异常，保留本地兜底文案，避免手动补录失败。
- 保留 `proactive_notify_skill` 通知落库。

预期效果：

- 手动补录不再只是固定文案，能进入和图片识别类似的 Agent 洞察链路。

---

### 4. 修复启动脚本执行权限

修改文件/对象：

- `/Users/libowen/Desktop/one-bite-one-world/start.sh`

完成内容：

- 执行：

```bash
chmod +x start.sh
```

- 权限从：

```text
-rw-r--r-- start.sh
```

变为：

```text
-rwxr-xr-x start.sh
```

预期效果：

- 后续可以直接运行：

```bash
./start.sh
```

不会再出现 `permission denied`。

---

## 验证结果

### 后端语法检查

执行目录：

```text
/Users/libowen/Desktop/one-bite-one-world/backend
```

命令：

```bash
python3 -m py_compile routers/meals.py routers/notifications.py
```

结果：通过，无错误输出。

### 前端构建

执行目录：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend
```

命令：

```bash
npm run build
```

结果：通过。

构建提示：

```text
Some chunks are larger than 500 kB after minification.
```

这是 Vite 体积警告，不阻断构建。本轮不处理代码分割。

### 核心 API 验证

已验证：

1. 后端根接口：正常返回。
2. demo session：可通过 `PUT /api/users/me/switch` 获取。
3. 手动补录：`POST /api/meals/manual` 返回 `success: true`。
4. 餐食详情：`GET /api/meals/{meal_id}` 返回 `image_mime`。
5. 通知已读：`POST /api/notifications/{id}/read` 返回 `success: true`。

示例验证餐食：

```text
meal_747579d1
```

餐食详情中已返回：

```json
"image_mime": "image/jpeg"
```

### 复查结果

- 搜索前端固定 `data:image/jpeg;base64`，只剩 MealHistory 的旧数据兼容分支。
- 搜索后端旧 SSE 条件 `current_count > last_count` / `new_count`，无遗留。
- `start.sh` 权限已确认为可执行。

## 本轮完成状态

本轮 6 个任务全部完成：

1. 修复通知未读数闭环。
2. 修复图片 MIME 链路不闭环。
3. 统一手动补录与自动识别的 Agent 编排链路。
4. 修复启动脚本执行权限。
5. 执行构建、语法和核心 API 验证。
6. 复查并输出下一轮优化建议。

## 下一轮候选优化建议

下一轮建议处理以下问题，按优先级排序：

### P1：统一后端错误语义

当前很多业务失败返回：

```json
{"success": false}
```

但 HTTP 状态仍是 200。建议逐步统一为：

- 参数错误：400
- 未登录：401
- 无权限：403
- 未找到：404
- 业务冲突：409
- 服务异常：500

并在前端 axios 层统一处理错误提示。

### P1：改善 session 持久性

当前 session 存在内存 `SESSION = {}` 中，后端 reload 或重启会丢失登录态。建议下一轮评估：

- SQLite session 表
- Redis session
- JWT / signed token

短期可先做“登录失效提示 + 自动清理 + 返回登录页”。

### P2：增加 Agent trace 可视化

当前 Agent 编排已经有 `AgentEvent`、`orchestrator`、`skills`，但前端看不到一次事件触发了哪些 Agent 和 Skill。建议新增 debug/trace 数据，用于产品演示：

```text
meal.uploaded -> TasteAgent -> vector_skill/report_skill/notify_skill
```

### P2：减少核心页面内联样式

`Notifications.tsx`、`MealHistory.tsx` 等仍有大量内联样式。建议逐步抽为 CSS 文件，提升视觉一致性和维护性。

### P2：优化周报反馈学习逻辑

当前反馈学习粒度较粗，容易把 taste vector 多个维度一起微调。建议让反馈带上具体 insight 类型和相关维度，只调整相关向量。

### P3：处理前端 bundle 体积警告

Vite 构建提示 JS chunk 超过 500KB。后续可以考虑：

- 路由级 lazy loading
- ECharts 按需加载
- Framer Motion 局部加载

## 结论

第一轮循环优化已完成，当前项目在通知状态一致性、图片格式兼容、手动补录 Agent 闭环和运行脚本可用性上有所增强。下一轮应优先处理错误语义、session 持久化和 Agent trace 可视化等更偏架构稳定性的问题。
