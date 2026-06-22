# Auth Flow Smoke Fix — Task Plan

- [x] Task 1: Fix local development CORS for current frontend port
    - 1.1: Add `http://localhost:5174` to FastAPI CORS allow origins
    - 1.2: Keep existing `5173` and `3000` origins unchanged
    - 1.3: Avoid broad wildcard CORS because credentials/session headers are used

- [x] Task 2: Restart backend and verify auth endpoints
    - 2.1: Confirm backend reloads with the new CORS configuration
    - 2.2: Verify demo user login with `PUT /api/users/me/switch`
    - 2.3: Verify registration with a unique phone number
    - 2.4: Verify phone login with the registered phone number
    - 2.5: Verify returned session can read `GET /api/users/me`

- [x] Task 3: Run core backend smoke checks after login
    - 3.1: Verify `GET /api/profile`
    - 3.2: Verify `GET /api/profile/timeline`
    - 3.3: Verify `GET /api/recommend/today`
    - 3.4: Verify `GET /api/city/live-summary`
    - 3.5: Verify `GET /api/city/recommend`
    - 3.6: Verify `GET /api/city/heatmap?city=beijing&dimension=spicy`
    - 3.7: Verify `GET /api/match/user_01/detail`
    - 3.8: Verify `GET /api/notifications`

- [x] Task 4: Validate frontend build and service availability
    - 4.1: Run `npm run build`
    - 4.2: Verify frontend dev server is reachable on its active port
    - 4.3: Verify backend docs are reachable

- [x] Task 5: Generate final validation summary
    - 5.1: Summarize the bug root cause
    - 5.2: Summarize the fix
    - 5.3: Summarize all passed validation checks
    - 5.4: Document which URL the user should open
