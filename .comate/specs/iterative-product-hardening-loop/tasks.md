# 前后端循环优化第一轮任务清单

- [x] Task 1: 修复通知未读数闭环
    - 1.1: 读取 `backend/routers/notifications.py`，确认 SSE 与已读接口当前实现
    - 1.2: 修改后端 SSE 逻辑，在未读数增加或减少时都推送最新 `unread_count`
    - 1.3: 修改 `Layout.tsx`，监听通知已读自定义事件并即时更新铃铛数字
    - 1.4: 修改 `Notifications.tsx`，标记已读成功后派发未读数变化事件
    - 1.5: 保留 SSE 作为最终同步来源，避免本地状态和服务端长期不一致

- [x] Task 2: 修复图片 MIME 链路不闭环
    - 2.1: 在 `backend/routers/meals.py` 中根据图片路径扩展名推导 MIME 类型
    - 2.2: 调整餐食详情 payload，返回 `image_mime`
    - 2.3: 调整单图接口 `/api/meals/{meal_id}/image`，返回 `image` 和 `mime_type`
    - 2.4: 调整批量图片接口 `/api/meals/images`，返回每个餐食的图片内容和 MIME 类型
    - 2.5: 修改 `MealResult.tsx`，按 `image_mime` 或 `mime_type` 渲染 data URL，并兼容旧数据
    - 2.6: 修改 `MealHistory.tsx`，兼容批量图片接口的新旧返回结构

- [x] Task 3: 统一手动补录与自动识别的 Agent 编排链路
    - 3.1: 在 `POST /api/meals/manual` 成功保存并重算向量后构造 `AgentEvent(event_type="meal.uploaded")`
    - 3.2: 在事件数据中标记 `source: "manual"` 和 `manual_created: True`
    - 3.3: 调用 `orchestrator.process_event` 生成手动补录对应的 micro insight
    - 3.4: 保留 `proactive_notify_skill` 通知落库
    - 3.5: 为 orchestrator 异常增加本地兜底文案，避免手动补录失败

- [x] Task 4: 修复启动脚本执行权限
    - 4.1: 检查 `start.sh` 当前权限
    - 4.2: 执行 `chmod +x start.sh`
    - 4.3: 验证 `./start.sh` 不再因 permission denied 失败

- [x] Task 5: 执行构建、语法和核心 API 验证
    - 5.1: 执行后端语法检查：`python -m py_compile routers/meals.py routers/notifications.py`
    - 5.2: 执行前端构建：`npm run build`
    - 5.3: 验证后端根接口、demo session、手动补录、餐食详情接口
    - 5.4: 如验证失败，定位并修复阻断问题后重新验证

- [x] Task 6: 复查并输出下一轮优化建议
    - 6.1: 基于本轮修改结果重新扫描仍存在的问题
    - 6.2: 将下一轮建议按优先级归类
    - 6.3: 生成本轮 `summary.md`，记录修复内容、验证结果和下一轮候选任务
