# Auth Flow Smoke Fix

## Requirement scenario and processing logic

用户反馈当前登录/注册一直失败，需要先由系统实际运行一遍核心功能，修复登录/注册阻塞问题，并确保主要功能链路可以测试通过。

当前已观察到：

- 后端服务运行在 `http://localhost:8000`。
- 前端新启动时因为 `5173` 被占用，Vite 自动切换到 `http://localhost:5174`。
- `backend/main.py` 当前 CORS 只允许：
  - `http://localhost:5173`
  - `http://localhost:3000`
- 如果浏览器打开的是 `http://localhost:5174`，则登录/注册请求会被浏览器 CORS 拦截，表现为前端永远显示“登录失败/注册失败”。

修复目标：

1. 让本地开发端口 `5173/5174/3000` 都能正常访问后端。
2. 验证体验用户登录、注册、手机号登录链路。
3. 验证登录后核心功能 API 可用。
4. 验证前端构建通过。

## Architecture and technical approach

### Backend CORS 修复

修改 FastAPI CORS 配置，允许当前 Vite 实际运行端口 `5174`。

建议将 `backend/main.py` 中：

```py
allow_origins=["http://localhost:5173", "http://localhost:3000"],
```

改为：

```py
allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
],
```

这样不会放开到 `*`，仍保持本地开发可控范围。

### Auth API 验证

用 HTTP 请求验证：

- `PUT /api/users/me/switch`
  - 输入：`{"user_id":"user_bowen"}`
  - 期望：返回 `success: true`、`session_id`、`user_id`
- `POST /api/auth/register`
  - 使用随机手机号避免重复注册
  - 期望：返回 `success: true`、`session_id`、`user_id`、`tags`、`taste_vector`
- `POST /api/auth/phone-login`
  - 使用刚注册的手机号
  - 期望：返回 `success: true`、`session_id`、`user_id`

### Core smoke 验证

使用登录/注册返回的 `X-Session-Id` 或 `X-User-Id` 验证：

- `GET /api/users/me`
- `GET /api/profile`
- `GET /api/profile/timeline`
- `GET /api/recommend/today`
- `GET /api/city/live-summary`
- `GET /api/city/recommend`
- `GET /api/city/heatmap?city=beijing&dimension=spicy`
- `GET /api/match/user_01/detail`
- `GET /api/notifications`

### Frontend validation

运行：

```bash
npm run build
```

确保 TypeScript 和 Vite 构建通过。

## Affected files

### `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`

Modification type: update CORS configuration.

Affected function/config:

- `app.add_middleware(CORSMiddleware, ...)`

Change:

- Add `http://localhost:5174` to `allow_origins`.

### `/Users/libowen/Desktop/one-bite-one-world/.comate/specs/auth-flow-smoke-fix/tasks.md`

Modification type: create implementation checklist after this document is confirmed.

### `/Users/libowen/Desktop/one-bite-one-world/.comate/specs/auth-flow-smoke-fix/summary.md`

Modification type: create final validation summary after implementation.

## Implementation details

Expected backend change:

```py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Validation script should use Python `urllib.request` or equivalent non-interactive commands to verify the backend chain.

## Boundary conditions and exception handling

- If phone is already registered, validation should generate a unique phone number.
- If frontend is on `5173`, behavior remains unchanged.
- If frontend is on `5174`, browser CORS should stop blocking requests after backend reload.
- If existing saved `localStorage` has stale session data, user can still choose login/register because `/` renders the auth entry.
- Avoid full `/api/report/weekly` smoke test because it may wait on LLM; use deterministic endpoints instead.

## Data flow paths

### Demo login

`Login.tsx` → `api.put('/users/me/switch')` → `backend/routers/users.py` → `SESSION` → localStorage `currentUserId/sessionId` → `/home`

### Register

`Login.tsx` → `api.post('/auth/register')` → `backend/routers/auth.py` → `users/auth_accounts` tables → `SESSION` → localStorage → `/home`

### Phone login

`Login.tsx` → `api.post('/auth/phone-login')` → `auth_accounts JOIN users` → `SESSION` → localStorage → `/home`

### CORS

Browser origin `http://localhost:5174` → FastAPI CORS middleware → backend auth APIs

## Expected outcomes

- Browser on `http://localhost:5174` can call backend auth APIs successfully.
- Demo user login works.
- Register works with a new phone number.
- Phone login works with that registered phone number.
- Core backend API smoke checks pass.
- Frontend build passes.
