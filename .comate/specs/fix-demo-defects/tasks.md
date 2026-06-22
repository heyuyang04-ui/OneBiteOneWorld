# 一食万象 Demo 缺陷修复 — 任务计划

共 11 个任务，按优先级 P0 → P1 → P2 排列，每个任务独立可控。

---

- [x] Task 1: 修复匹配逻辑 Bug
    - 1.1: 分析 `match.py:25-55` 中 `match_action` 函数的参数语义，明确 `match_id` 路径参数实际含义是 `other_user_id`（对方用户 ID），而非匹配记录 ID
    - 1.2: 重写 `match_action` 函数逻辑：用 `other_user_id` 正确查询数据库中是否已存在该对方用户对当前用户的 like 记录
    - 1.3: 修复 `like` 操作时匹配记录的插入/更新逻辑，确保双向确认（mutual）能正确触发
    - 1.4: 修复 `match_detail` 函数中的类似混淆（`match.py:87-106`），明确 `match_id` 在详情接口中是匹配记录 ID

- [x] Task 2: 增加用户切换机制（后端）
    - 2.1: 在 `backend/routers/users.py` 中新增 `PUT /api/users/me/switch` 端点，接收 `{"user_id": "user_02"}` 并更新 session 中的当前用户
    - 2.2: 修改 `backend/main.py` 中的用户中间件，增加对 session 切换状态的支持，默认值为 `user_01`
    - 2.3: 在 `backend/routers/users.py` 中新增 `GET /api/users` 返回所有用户列表（已有），确保前端可获取用户列表用于下拉选择

- [x] Task 3: 增加用户切换机制（前端）
    - 3.1: 在 `frontend/src/components/Layout.tsx` 底部导航栏或顶部增加用户切换下拉框（select 组件）
    - 3.2: 调用 `GET /api/users` 获取用户列表填充下拉选项
    - 3.3: 切换时调用 `PUT /api/users/me/switch`，并通过 `X-User-Id` header 变更后续请求的用户身份
    - 3.4: 切换用户后刷新当前页面数据（味觉档案、周报、匹配列表等需重新加载）

- [x] Task 4: 实现 SSE 实时推送
    - 4.1: 在 `backend/routers/notifications.py` 中新增 `GET /api/notifications/stream` SSE 端点
    - 4.2: 实现 SSE 循环逻辑：每 5 秒检查当前用户是否有新的未读通知（insights 表），有则推送
    - 4.3: 在 `frontend/src/components/Layout.tsx` 中使用 `EventSource` 订阅 SSE 流
    - 4.4: 收到 SSE 推送后更新未读通知计数徽标

- [x] Task 5: 修复图片存储
    - 5.1: 在 `backend/config.py` 的 `AppConfig` 中增加 `image_dir` 配置项，指向 `backend/data/images/`
    - 5.2: 修改 `backend/routers/meals.py` 的 `upload_meal` 函数：解码 base64 图片、保存为文件（UUID 命名）、将文件路径写入 `image_url`
    - 5.3: 新增 `GET /api/meals/{meal_id}/image` 静态文件端点，或修改 `get_meal` 返回 base64 格式图片数据
    - 5.4: 在 `frontend/src/pages/MealResult.tsx` 和 `MealHistory.tsx` 中显示上传的餐食图片

- [x] Task 6: 隐私设置数据隔离
    - 6.1: 修改 `backend/routers/users.py` 中的 `update_privacy` 函数：当用户将隐私级别设为 `private` 时，清除该用户在 matches 表中的所有匹配记录
    - 6.2: 确认 `match_skill.py` 和 `vector_skill.py` 中已有的 `privacy_level` 检查逻辑完整覆盖所有匹配和发现路径

- [x] Task 7: CORS 策略收紧
    - 7.1: 修改 `backend/main.py` 的 CORS 中间件配置，移除 `"*"` 通配符
    - 7.2: 将 `allow_origins` 改为精确列表 `["http://localhost:5173", "http://localhost:3000"]`

- [x] Task 8: 全局异常处理器安全加固
    - 8.1: 修改 `backend/main.py` 的 `global_exception_handler`，将 `str(exc)` 替换为通用消息 `"An internal error occurred"`
    - 8.2: 保留 `print(traceback.format_exc())` 在控制台输出完整堆栈（仅开发环境可见），不暴露给前端

- [x] Task 9: 周报加入反思问题
    - 9.1: 修改 `backend/skills/report_skill.py` 的 Prompt，在 JSON 返回格式中要求 LLM 额外生成 `reflection` 字段（反思问题）

- [x] Task 10: 城市推荐 × 个人口味交叉
    - 10.1: 修改 `backend/skills/recommend_skill.py` 的 `_recommend_trends` 函数，增加交叉逻辑：筛选出用户偏好较高（>0.3）且城市中趋势上升（change > 0.03）的口味维度
    - 10.2: 对交叉结果按"个人偏好 × 趋势变化幅度"加权排序，返回 Top-N 交叉推荐

- [x] Task 11: 增加删除餐食 API
    - 11.1: 在 `backend/routers/meals.py` 中新增 `DELETE /api/meals/{meal_id}` 端点，执行软删除或硬删除
    - 11.2: 删除后触发 `vector_skill` 重新计算用户的味觉向量

- [x] Task 12: 统一文件读取路径
    - 12.1: 定义 `DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")` 或类似常量
    - 12.2: 修改 `backend/routers/city.py` 中所有 `open("data/...")` 为使用 `DATA_DIR` 的绝对路径
    - 12.3: 修改 `backend/skills/match_skill.py`、`recommend_skill.py`、`trend_skill.py` 中的相对路径为绝对路径
    - 12.4: 修改 `backend/database.py` 中的 `_import_mock_data` 函数，确保 `data_dir` 使用绝对路径
