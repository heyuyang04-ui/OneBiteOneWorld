# 第八轮 session 过期时间与清理策略任务清单

- [x] Task 1: 增加 session TTL 配置
    - 1.1: 修改 `backend/config.py`
    - 1.2: 在 `AppConfig` 中新增 `session_ttl_hours`
    - 1.3: 默认值使用 `SESSION_TTL_HOURS` 环境变量或 168 小时
    - 1.4: 不改动 `AIConfig` 和 AI key fallback

- [x] Task 2: 扩展 sessions 表和迁移逻辑
    - 2.1: 修改 `backend/database.py` 中 sessions 表定义，新增 `expires_at TEXT`
    - 2.2: 新增 `idx_sessions_expires_at` 索引
    - 2.3: 新增 `_ensure_session_columns(db)` 迁移函数
    - 2.4: 对旧表缺失 `expires_at` 的情况执行 `ALTER TABLE`
    - 2.5: 将旧 session 的 `expires_at` 设置为当前时间 + TTL
    - 2.6: 在 `init_db()` 中调用迁移函数

- [x] Task 3: 改造 session_store 创建和解析逻辑
    - 3.1: 修改 `backend/services/session_store.py` 引入 `timedelta`
    - 3.2: 新增 `_expires_at()` 和 `_is_expired(expires_at)`
    - 3.3: `create_session` 写入 `expires_at`
    - 3.4: 内存 `SESSION` 缓存改为包含 `user_id` 和 `expires_at` 的 dict
    - 3.5: `resolve_session` 支持 dict 缓存并检查过期
    - 3.6: `resolve_session` 查询 DB 时读取 `user_id, expires_at`
    - 3.7: 过期 session 自动调用 `delete_session` 并返回空字符串
    - 3.8: 兼容旧字符串缓存值

- [x] Task 4: 增加过期 session 清理函数
    - 4.1: 在 `session_store.py` 新增 `cleanup_expired_sessions()`
    - 4.2: 删除 DB 中 `expires_at <= now` 的 session
    - 4.3: 同步清理内存中过期 dict 缓存
    - 4.4: 保持 `delete_session` 语义不变
    - 4.5: 修改 `delete_user_sessions` 兼容 dict 缓存格式

- [x] Task 5: 应用启动时清理过期 session
    - 5.1: 修改 `backend/main.py` 引入 `cleanup_expired_sessions`
    - 5.2: 在 startup 中 `await init_db()` 后调用 `await cleanup_expired_sessions()`
    - 5.3: 保持鉴权中间件和公开路径逻辑不变

- [x] Task 6: 执行语法、构建和 session 行为验证
    - 6.1: 执行 `python3 -m py_compile config.py database.py main.py services/session_store.py routers/auth.py`
    - 6.2: 执行 `npm run build`
    - 6.3: 验证 demo switch 创建 session
    - 6.4: 验证新 session 可访问 `/api/users/me`
    - 6.5: 手动将 session 的 `expires_at` 改为过去时间
    - 6.6: 验证过期 session 访问 `/api/users/me` 返回 401
    - 6.7: 调用 `cleanup_expired_sessions()` 并确认过期记录被清理

- [x] Task 7: 复查并生成第八轮总结
    - 7.1: 复查 `AIConfig` 未被修改
    - 7.2: 复查 session 创建、解析、删除、清理逻辑均兼容 dict 缓存
    - 7.3: 记录构建结果、API 验证结果和后续优化项
    - 7.4: 生成 `.comate/specs/session-expiration-round-8/summary.md`
