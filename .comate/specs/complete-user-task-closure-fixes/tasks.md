# 完成真实用户任务闭环修复任务清单

- [x] Task 1: 增加后端餐食手动补录和纠错接口
    - 1.1: 在 `backend/models/schemas.py` 中新增手动补录和餐食更新请求模型
    - 1.2: 在 `backend/routers/meals.py` 中抽取或复用餐食 payload 构造逻辑
    - 1.3: 新增 `POST /api/meals/manual`，支持菜名、菜系、食材、描述和可选图片保存
    - 1.4: 新增 `PUT /api/meals/{meal_id}`，支持当前用户纠正菜名、菜系、食材、味觉标签和营养字段
    - 1.5: 在手动补录和纠错保存后调用 `vector_skill` 重算个人味觉向量
    - 1.6: 保持越权、缺失记录、非法图片和空菜名的业务错误返回

- [x] Task 2: 优化首页 AI 识别失败兜底体验
    - 2.1: 在 `Home.tsx` 中新增识别错误、手动补录表单和手动保存状态
    - 2.2: 调整 `handleConfirmRecognition`，失败时保留图片和描述，不再只使用 `alert` 或自动清空
    - 2.3: 增加重试当前图片、更换图片和展开手动补录三类操作
    - 2.4: 对接 `POST /api/meals/manual`，手动保存成功后跳转餐食结果页
    - 2.5: 在 `Home.css` 中补充识别失败卡片和手动补录表单样式

- [x] Task 3: 增加 MealResult 结果页纠错能力
    - 3.1: 在 `MealResult.tsx` 中新增纠错面板展开、表单状态、保存状态和错误状态
    - 3.2: 将当前餐食的菜名、菜系、食材同步到纠错表单
    - 3.3: 调用 `PUT /api/meals/{meal_id}` 保存纠错结果
    - 3.4: 保存成功后局部更新结果页展示，不刷新页面
    - 3.5: 在 `MealResult.css` 中补充纠错面板、输入框、按钮和错误提示样式

- [x] Task 4: 增强 MealHistory 历史记录管理
    - 4.1: 在 `MealHistory.tsx` 中引入路由跳转能力
    - 4.2: 将历史记录卡片改为点击进入 `/meal/{id}` 详情页
    - 4.3: 为每条记录增加删除按钮并阻止事件冒泡
    - 4.4: 调用已有 `DELETE /api/meals/{meal_id}` 删除误记录
    - 4.5: 删除成功后同步移除列表项和图片缓存，删除失败时展示错误反馈

- [x] Task 5: 增加 App 启动 session 恢复校验
    - 5.1: 修改 `App.tsx` 的 `ProtectedLayout`，同时检查 `currentUserId` 和 `sessionId`
    - 5.2: 进入受保护页面前调用 `/api/users/me` 校验 session 是否有效
    - 5.3: 校验中展示轻量恢复状态，避免内部页面闪现
    - 5.4: 校验失败时清理本地登录状态并跳转 `/login`
    - 5.5: 在 `App.css` 中补充恢复状态样式

- [x] Task 6: 增强匹配推荐解释和行动建议
    - 6.1: 在 `backend/models/schemas.py` 中扩展匹配响应的可选解释字段
    - 6.2: 在 `backend/routers/match.py` 中新增规则化推荐解释、第一餐建议和开场问题生成逻辑
    - 6.3: 在 `GET /api/match/discover` 返回数据中补充 `why_recommended`、`first_meal_suggestion`、`conversation_starter`
    - 6.4: 在 `MatchCard.tsx` 中扩展 props 并渲染 Agent 推荐理由和行动建议
    - 6.5: 在 `MatchCard.css` 中补充推荐解释卡片样式

- [x] Task 7: 执行构建和语法验证
    - 7.1: 执行后端 Python 语法检查，覆盖 `routers/meals.py`、`routers/match.py`、`models/schemas.py`
    - 7.2: 执行前端 `npm run build`，确认 TypeScript 与 Vite 构建通过
    - 7.3: 如验证失败，定位并修复阻断问题后重新验证
