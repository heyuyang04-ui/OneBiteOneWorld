# Real Auth Profile Onboarding — Task Plan

- [x] Task 1: Add lightweight phone account storage
    - 1.1: Add `auth_accounts` table to `database.py`
    - 1.2: Store `phone`, `user_id`, and `created_at`
    - 1.3: Keep existing `users` table unchanged for compatibility
    - 1.4: Ensure existing database initializes the new table without deleting data

- [x] Task 2: Create backend auth router
    - 2.1: Create `backend/routers/auth.py`
    - 2.2: Add phone normalization helper
    - 2.3: Add session creation helper using existing `SESSION`
    - 2.4: Add deterministic profile inference helper for tags and 32-dimensional taste vector
    - 2.5: Implement `POST /api/auth/phone-login`
    - 2.6: Implement `POST /api/auth/register`
    - 2.7: Handle missing fields, duplicate phone numbers, and unknown phone login

- [x] Task 3: Register auth router in FastAPI
    - 3.1: Import `auth` router in `main.py`
    - 3.2: Register router with prefix `/api/auth`
    - 3.3: Keep existing user switch endpoint unchanged for experience-user login

- [x] Task 4: Refactor Login.tsx state and handlers
    - 4.1: Add auth mode and login method state for entry, login, demo login, phone login, and register
    - 4.2: Add phone login form state and error handling
    - 4.3: Add registration form state for phone, name, city, age, occupation, food preferences, spice, sweet, meat, and dining scene
    - 4.4: Preserve existing experience-user selection logic
    - 4.5: Add submit handler for phone login
    - 4.6: Add submit handler for registration
    - 4.7: Persist returned `currentUserId` and `sessionId`, then navigate to `/home`

- [x] Task 5: Rebuild Login.tsx rendering for real auth entry
    - 5.1: Entry screen shows `登录` and `注册`
    - 5.2: Login screen shows `体验用户登录` and `手机号登录`
    - 5.3: Demo login renders existing role cards
    - 5.4: Phone login renders phone input and submit button
    - 5.5: Register renders full user information form
    - 5.6: Show inline errors instead of alert-only feedback
    - 5.7: Keep banner visual and black-purple brand tone

- [x] Task 6: Extend Login.css for phone login and register form
    - 6.1: Add segmented method buttons
    - 6.2: Style dark input/select/textarea controls
    - 6.3: Add form grid and field label styles
    - 6.4: Add inline error style
    - 6.5: Keep role cards, buttons, and forms consistent in width
    - 6.6: Ensure long register form scrolls cleanly on small screens

- [x] Task 7: Validate auth onboarding flow
    - 7.1: Run frontend production build
    - 7.2: Verify backend imports auth router successfully
    - 7.3: Verify phone login returns not-registered for unknown phone
    - 7.4: Verify registration creates user, auth account, tags, vector, and session
    - 7.5: Verify phone login works after registration
    - 7.6: Verify experience-user login still works
    - 7.7: Verify `/home` can load with a newly registered user
