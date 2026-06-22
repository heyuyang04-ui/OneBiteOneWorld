# Real Auth Profile Onboarding — Summary

## Completed tasks

- Added lightweight `auth_accounts` storage for phone-number login.
- Added backend auth router with:
  - `POST /api/auth/phone-login`
  - `POST /api/auth/register`
- Added deterministic profile inference for registration:
  - generated tags;
  - generated 32-dimensional taste vector;
  - generated user record;
  - generated auth account mapping;
  - generated session.
- Registered auth router in FastAPI.
- Refactored login page into real entry flows:
  - login by experience user;
  - login by phone number;
  - register by filling personal information.
- Added registration fields:
  - phone;
  - name;
  - city;
  - age;
  - occupation;
  - favorite foods;
  - spice preference;
  - sweet preference;
  - meat preference;
  - dining scene.
- Extended login page styles for segmented login methods, dark form fields, inline errors, and scrollable registration form.

## Modified files

- `/Users/libowen/Desktop/one-bite-one-world/backend/database.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/auth.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.css`

## Verification results

- Frontend build passed with `npm run build`.
- Backend docs endpoint returned `200`.
- Unknown phone login returns `phone not registered`.
- Registration creates a new user and returns session, tags, and 32-dimensional taste vector.
- Phone login works after registration.
- Experience-user login still works through `/api/users/me/switch`.
- New registered user can load `/api/recommend/today` and receive personalized recommendations.
- Frontend routes `/` and `/home` return `200`.

## Notes

- This iteration does not implement passwords or SMS verification. Phone login is a lightweight account identifier suitable for the current local prototype.
- Registration uses deterministic profile inference rather than an LLM call to keep the entry path fast and reliable.
