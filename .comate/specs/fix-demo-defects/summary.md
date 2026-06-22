# 一食万象 Demo 缺陷修复 — 完成总结

## 修复概览

共完成 **12 个任务**，涉及 **14 个文件** 的修改，覆盖 P0/P1/P2 所有优先级级别。

---

## 已完成的修改

### P0 — 阻塞 Demo 体验

| # | 任务 | 修改文件 | 关键变更 |
|---|------|---------|---------|
| 1 | 修复匹配逻辑 Bug | `backend/routers/match.py` | 重写 `match_action`：分离 `other_user_id` 与 `match_id` 语义，正确实现双向确认匹配；保存 similarity 和 dim_scores 到 DB |
| 2 | 用户切换机制（后端） | `backend/main.py`, `backend/routers/users.py` | 新增 SESSION 字典 + `PUT /api/users/me/switch` 接口 + X-Session-Id 中间件支持 |
| 3 | 用户切换机制（前端） | `UserSwitcher.tsx`, `api.ts`, `Layout.tsx` | UserSwitcher 调用 switch API 并存储 sessionId；api.ts 拦截器注入 X-Session-Id header |

### P1 — 影响核心价值展示

| # | 任务 | 修改文件 | 关键变更 |
|---|------|---------|---------|
| 4 | SSE 实时推送 | `backend/routers/notifications.py`, `frontend/Layout.tsx` | 后端新增 `GET /api/notifications/stream` SSE 端点（5秒轮询未读通知）；前端用 EventSource 订阅并更新铃铛徽标 |
| 5 | 修复图片存储 | `backend/config.py`, `backend/routers/meals.py` | 上传时 base64 解码保存到 `data/images/` 目录；列表/详情接口返回 base64 图片数据 |
| 6 | 隐私数据隔离 | `backend/routers/users.py` | 设为 private 时自动清除 matches 表中该用户的所有匹配记录 |
| 7 | CORS 收敛 | `backend/main.py` | 移除 `"*"` 通配符，改为精确列表 `["http://localhost:5173", "http://localhost:3000"]` |
| 8 | 异常处理器加固 | `backend/main.py` | `str(exc)` → 通用消息 `"An internal error occurred"`；完整堆栈仅 console print |

### P2 — 锦上添花

| # | 任务 | 修改文件 | 关键变更 |
|---|------|---------|---------|
| 9 | 周报反思问题 | `backend/skills/report_skill.py` | Prompt 中增加 reflection 字段要求，引导 LLM 生成反思问题 |
| 10 | 城市×口味交叉推荐 | `backend/skills/recommend_skill.py`, `backend/routers/city.py` | 新增 `_cross_recommend` 函数：偏好×趋势加权排序；`/api/city/recommend` 返回 cross 字段 |
| 11 | 删除餐食 API | `backend/routers/meals.py` | 新增 `DELETE /api/meals/{meal_id}`；校验归属权限；删除图片文件 + 重新计算味觉向量 |
| 12 | 统一文件读取路径 | `config.py`, `city.py`, `match_skill.py`, `recommend_skill.py`, `trend_skill.py` | 新增 `app_config.data_dir` 配置；所有 `open("data/...")` 改为 `open(os.path.join(app_config.data_dir, ...))` |

---

## 未修改项

- API Key 硬编码 — 按用户要求保留
- WebSocket — 用 SSE 轻量方案替代
- 用户登录/认证系统 — Demo 阶段保持 `X-User-Id` header 模式
