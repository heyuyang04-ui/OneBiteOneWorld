# fixpoint-experience-stability-batch 修复任务计划

- [x] Task 1: 修复 meal_companion_skill 固定兜底推荐
    - 1.1: 读取双方用户的 tags、occupation、city 作为向量不足时的上下文
    - 1.2: 基于共同标签推断 shared_foods 和 reason
    - 1.3: 无共同信号时返回引导记录更多餐食的建议，不再固定火锅/烤鱼
    - 1.4: 保持已有向量充足时的饭搭子推荐逻辑不变

- [x] Task 2: 为 city trends 增加短期缓存
    - 2.1: 在 `backend/routers/city.py` 增加模块级 TTL cache
    - 2.2: 用 `(city, dimension)` 作为缓存 key
    - 2.3: 命中缓存时直接返回趋势结果
    - 2.4: 缓存未命中时保持现有趋势计算和 skill 调用逻辑

- [x] Task 3: 修复 WeeklyReport feedback 的 highlight id
    - 3.1: 在 `backend/skills/report_skill.py` 为每条 highlight 增加稳定 id
    - 3.2: 解析失败 fallback 的 highlight 也保持结构安全
    - 3.3: 在 `frontend/src/pages/WeeklyReport.tsx` 中优先使用 `h.id` 提交反馈
    - 3.4: 点击反馈后显示轻量成功/失败状态

- [x] Task 4: 让首页 quick-actions 有明确点击反馈
    - 4.1: 在 `Home.tsx` 增加 action feedback 状态
    - 4.2: 为四个 quick-action 按钮绑定点击处理
    - 4.3: 根据按钮类型展示不同 Agent 意图反馈
    - 4.4: 不新增后端 API，保持最小改动

- [x] Task 5: 为 MealHistory 增加图片批量加载
    - 5.1: 在 `backend/routers/meals.py` 新增 `/meals/images` 批量图片接口
    - 5.2: 限制 ids 数量上限并只返回当前用户图片
    - 5.3: 修改 `MealHistory.tsx` 收集待加载图片 id 后批量请求
    - 5.4: 保留现有 `/meals/{meal_id}/image` 单图接口不变

- [x] Task 6: 修复 SSE 断开检测与前端无限重连
    - 6.1: 在 `backend/routers/notifications.py` 的 SSE loop 中检测 `request.is_disconnected()`
    - 6.2: 客户端断开时退出 generator
    - 6.3: 在 `Layout.tsx` 中为 EventSource 增加连续错误计数
    - 6.4: 连续错误达到阈值后关闭 EventSource

- [x] Task 7: 调整视觉识别 token 与上传失败预览清空
    - 7.1: 将 `AIClient.vision()` 的 `max_tokens` 调整为 4000
    - 7.2: 为 `ImageUpload.tsx` 增加 `resetKey` prop 并在变化时清空 preview
    - 7.3: 在 `Home.tsx` 上传失败、非食物、结果异常、网络异常时递增 resetKey
    - 7.4: 正常识别成功时保持跳转逻辑不变

- [x] Task 8: 运行验证并生成修复总结
    - 8.1: 执行后端 Python 编译检查
    - 8.2: 执行前端构建检查
    - 8.3: 执行关键 API smoke 验证 city trends 与批量图片接口
    - 8.4: 写入 `.comate/specs/fixpoint-experience-stability-batch/summary.md`
