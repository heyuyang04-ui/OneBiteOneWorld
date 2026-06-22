# fixpoint-security-bug-batch 修复任务计划

- [x] Task 1: 补强后端会话鉴权边界
    - 1.1: 在 `backend/main.py` 中定义公共路径与公共接口判断逻辑
    - 1.2: 修改 `user_middleware`，除公开接口外必须校验有效 `X-Session-Id`
    - 1.3: 移除后端对 `X-User-Id` 与默认 `user_01` 的身份回退
    - 1.4: 保证登录、注册、演示用户切换、SSE query session 场景不被误拦截

- [x] Task 2: 限制用户列表与演示切换入口
    - 2.1: 在 `backend/routers/users.py` 中增加演示用户白名单
    - 2.2: 限制 `/users/me/switch` 只能切换到 `user_01`、`user_bowen`、`user_02`、`user_03`
    - 2.3: 调整 `/users` 依赖已登录 session，并仅返回脱敏字段
    - 2.4: 保持 Bowen 演示用户可正常登录

- [x] Task 3: 修复 match 与 notification 越权问题
    - 3.1: 删除 `/match/{match_id}/detail` 的 direct user_id demo fallback
    - 3.2: 校验当前用户必须是 match 参与者后才能读取详情
    - 3.3: 为 `/notifications/{notification_id}/read` 增加 `user_id` 归属条件
    - 3.4: 确保未授权或不存在资源返回明确错误

- [x] Task 4: 为 match like 写入增加事务兜底
    - 4.1: 在 `backend/routers/match.py` 的 like 分支写入段使用事务
    - 4.2: 在事务内重新检查已有正向/反向 match 记录
    - 4.3: 保留数据库唯一索引兜底和 `INSERT OR IGNORE` 行为
    - 4.4: 异常时回滚并关闭数据库连接

- [x] Task 5: 防止 LLM parse 失败内容进入用户可见 reasoning
    - 5.1: 检查 `backend/agents/base.py` 的解析失败处理
    - 5.2: 检查 `backend/agents/protocol.py` 的解析失败处理
    - 5.3: 将 parse 失败时的 `reasoning` 改为空字符串或安全短文本
    - 5.4: 避免原始 LLM Markdown/调试输出写入 insights

- [x] Task 6: 修复前端配置与明显 UX bug
    - 6.1: 将 `frontend/src/services/api.ts` 的 baseURL 改为 `import.meta.env.VITE_API_BASE` fallback
    - 6.2: 前端请求头不再默认发送 `X-User-Id: user_01`
    - 6.3: 修复 `frontend/src/pages/Settings.tsx` 隐私设置失败无提示与状态不回滚
    - 6.4: 修复 `frontend/src/pages/CityMap.tsx` tooltip 读取路径，避免 NaN

- [x] Task 7: 修复新用户空向量不写库
    - 7.1: 检查 `backend/skills/vector_skill.py` 当前空餐食处理逻辑
    - 7.2: 在无餐食时将 32 维 0 向量写入 `users.taste_vector`
    - 7.3: 保持已有餐食计算逻辑不变
    - 7.4: 确保新注册用户参与匹配时有稳定画像字段

- [x] Task 8: 运行验证并生成修复总结
    - 8.1: 执行后端 Python 编译检查
    - 8.2: 执行前端构建检查
    - 8.3: 执行关键 API smoke 验证鉴权和越权修复
    - 8.4: 写入 `.comate/specs/fixpoint-security-bug-batch/summary.md`
