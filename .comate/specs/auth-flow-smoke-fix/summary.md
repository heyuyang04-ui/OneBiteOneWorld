# Auth Flow Smoke Fix — Summary

## Root cause

登录/注册一直失败的主要原因是本地前端端口与后端 CORS 配置不一致。

- 后端只允许：
  - `http://localhost:5173`
  - `http://localhost:3000`
- 当前 Vite 因为 `5173` 被占用，自动启动到了：
  - `http://localhost:5174`
- 浏览器从 `5174` 调用 `8000` 后端时被 CORS 拦截，前端表现为登录/注册失败。

## Fix

Updated `/Users/libowen/Desktop/one-bite-one-world/backend/main.py` CORS configuration to allow the active local Vite port:

```py
allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
]
```

This keeps CORS limited to local development origins instead of using a broad wildcard.

## Auth validation passed

Validated via real backend requests:

- Demo login: `PUT /api/users/me/switch`
  - User: `user_bowen`
  - Result: success
- Registration: `POST /api/auth/register`
  - Phone: `13981682956`
  - Created user: `user_79bf86c9`
  - Generated tags:
    - `肉食爱好者`
    - `高蛋白偏好`
    - `北京味觉探索者`
    - `加班晚餐型`
- Phone login: `POST /api/auth/phone-login`
  - Result: success
- Session read: `GET /api/users/me`
  - Result: success

## Core smoke checks passed

Validated these endpoints after login:

- `GET /api/profile`
- `GET /api/profile/timeline`
- `GET /api/recommend/today`
- `GET /api/city/live-summary`
- `GET /api/city/recommend`
- `GET /api/city/heatmap?city=beijing&dimension=spicy`
- `GET /api/match/user_01/detail`
- `GET /api/notifications`

All returned HTTP 200 with `success: true`.

## Frontend validation passed

- Ran `npm run build`
- TypeScript and Vite build completed successfully
- Service availability checks:
  - `http://localhost:8000/docs` -> 200
  - `http://localhost:5173` -> 200
  - `http://localhost:5174` -> 200

## Current URLs

Backend:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

Frontend:

```text
http://localhost:5173
http://localhost:5174
```

Because both frontend ports currently respond, use the page you already opened. If login/register still shows an error, refresh the page once so the browser uses the latest backend CORS response.
