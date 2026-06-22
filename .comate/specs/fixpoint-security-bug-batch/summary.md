# fixpoint-security-bug-batch 修复总结

## 本轮处理范围

根据新版 `/Users/libowen/Desktop/one-bite-one-world/fixpoint.txt`，本轮优先修复安全越权链路与低风险明显 bug。

已处理：

- BUG-2：全局 user 识别无鉴权，默认 `user_01`。
- BUG-4：用户列表与切换用户无鉴权。
- BUG-5：`/match/{id}/detail` demo 兼容分支越权读取任意用户。
- BUG-6：`/notifications/{id}/read` 缺 `user_id` 校验。
- BUG-7：match like 写入缺少事务兜底。
- BUG-10：Decision parse 失败时原始 LLM 输出可能进入 reasoning。
- BUG-12：前端 API baseURL 硬编码。
- BUG-19：新用户空向量不写库。
- BUG-24：隐私设置失败无提示。
- BUG-25：CityMap tooltip 取值路径不稳。

未处理：

- BUG-1：硬编码 AI API Key。按此前约束保留 `backend/config.py` fallback，且 code-security skill 当前不开放硬编码凭证修复与托管。
- BUG-3：短信验证码/密码/JWT 属于认证产品方案变更，本轮先补 session 边界。
- 性能、SSE 重连、批量图片、SESSION Redis/TTL、P3 重构类问题留到后续批次。

## 修改文件

### 后端

- `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/users.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/match.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/notifications.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/agents/protocol.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/vector_skill.py`

### 前端

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/services/api.ts`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Settings.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx`

## 完成内容

### 1. 会话鉴权边界

- `/api/*` 默认必须携带有效 `X-Session-Id`。
- 不再使用 `X-User-Id` 或默认 `user_01` 作为后端身份 fallback。
- 登录、注册、演示用户切换、SSE stream 保留公开入口。
- SSE stream 只接受有效 `x_session_id`，不再接受 `x_user_id` 旁路。

### 2. 用户列表与演示切换限制

- `/users/me/switch` 仅允许切换：
  - `user_01`
  - `user_bowen`
  - `user_02`
  - `user_03`
- `/users` 仅返回演示用户脱敏字段。
- Bowen 演示用户保留。

### 3. match 与通知越权修复

- `/match/{match_id}/detail` 删除 direct user_id fallback。
- match detail 必须使用真实 match id。
- 当前用户必须是 match 参与者。
- 通知已读更新改为：`UPDATE insights SET is_read=1 WHERE id=? AND user_id=?`。

### 4. match like 事务保护

- like 写入段使用 `BEGIN IMMEDIATE`。
- 事务内再次检查正向和反向 match。
- 保留上一轮唯一索引和 `INSERT OR IGNORE` 兜底。
- 异常时 rollback 并关闭连接。

### 5. LLM parse 安全处理

- `Decision.parse()` 失败时不再把 raw LLM 输出放入 `reasoning`。
- 避免原始 Markdown/调试内容经 `AgentMemory` 进入用户可见通知链路。

### 6. 前端配置与 UX 修复

- `api.ts` 使用 `import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'`。
- 前端请求头不再发送 `X-User-Id`。
- `Layout.tsx` SSE 地址使用同一 API base，并只传 `x_session_id`。
- `Settings.tsx` 隐私设置失败时回滚状态并展示提示。
- `CityMap.tsx` tooltip 改为从 `p.data?.value?.[2]` 读取。

### 7. 新用户空向量写库

- `vector_skill.py` 在无餐食记录时，将 32 维 0 向量写入 `users.taste_vector`。
- 新用户也有稳定画像字段可参与后续匹配逻辑。

## 验证结果

### 后端编译

命令：

```bash
python3 -m py_compile backend/main.py backend/routers/users.py backend/routers/match.py backend/routers/notifications.py backend/agents/protocol.py backend/skills/vector_skill.py
```

结果：通过。

### 前端构建

命令：

```bash
npm run build
```

结果：通过。

说明：Vite 仍提示 chunk size warning，这是现有 bundle 体积提示，不影响构建结果。

### 静态检查

确认以下旧模式已移除：

- 后端未再出现 `X-User-Id` 身份 fallback。
- 后端未再出现 `other_id = match_id` direct user_id fallback。
- 后端未再出现 `reasoning=raw`。
- 前端未再出现 `X-User-Id` 请求头。
- 前端未再出现 `p.value?.[2]` tooltip 旧路径。

### API smoke

使用 FastAPI TestClient 验证：

```text
unauth_meals 401 UNAUTHORIZED
demo_switch 200 True
invalid_switch 200 False
users_me 200 True user_bowen
direct_match_detail 200 False match not found
notification_read 200 False
```

结论：

- 未登录访问 `/api/meals` 已返回 401。
- Bowen 演示用户切换正常。
- 非白名单用户不能通过 switch 直接冒充。
- 有效 session 能读取当前用户。
- direct user_id 方式访问 match detail 已失效。
- 非本人/不存在通知不能被标记已读。

## 任务状态

`.comate/specs/fixpoint-security-bug-batch/tasks.md` 中 8 个顶层任务均已完成。