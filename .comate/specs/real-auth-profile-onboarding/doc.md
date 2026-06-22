# Real Auth Profile Onboarding

## Requirement scenario and processing logic

The current auth entry is still too demo-like: login/register is only a wrapper around selecting preset roles. The user wants a more realistic product entry:

1. Login page can either:
   - select an existing/experience user;
   - log in with a phone number.
2. Register page should require users to fill their own information.
3. AI should match tags and initialize a taste profile based on the submitted information.

For this project iteration, “AI matches tags” should be implemented as deterministic backend profile inference rules instead of calling LLM. Reasons:

- Registration must be fast and reliable.
- Existing project already represents user taste as tags + 32-dimensional vector.
- This avoids adding fragile auth/AI dependencies at the entry point.
- The result can still be productized as “AI 初始画像生成”.

## Target user flows

### Flow A: Login by experience user

```text
/ or /login
  -> 登录
  -> 体验用户
  -> select 阿杰 / Bowen / 小雅 / 大鹏
  -> PUT /api/users/me/switch
  -> localStorage currentUserId + sessionId
  -> /home
```

### Flow B: Login by phone number

```text
/ or /login
  -> 登录
  -> 手机号登录
  -> input phone number
  -> POST /api/auth/phone-login
  -> if existing phone identity found: return user/session
  -> if not found: show structured error asking user to register first
  -> /home
```

Since the database currently has no account/password table, phone login will be backed by a lightweight `auth_accounts` table mapping phone numbers to user IDs.

### Flow C: Register with self-filled profile

```text
/ or /login
  -> 注册
  -> fill form:
      phone
      name
      city
      age
      occupation
      favorite foods / food preferences
      spice preference
      sweet preference
      meat preference
      dining scenario
  -> POST /api/auth/register
  -> backend validates minimal fields
  -> backend infers tags + initial taste_vector
  -> insert into users table
  -> insert into auth_accounts table
  -> return session + inferred profile
  -> localStorage currentUserId + sessionId
  -> /home
```

## Architecture and technical approach

### Backend

Add a new router:

```text
backend/routers/auth.py
```

Register under:

```text
/api/auth
```

Add database table in `database.py`:

```sql
CREATE TABLE IF NOT EXISTS auth_accounts (
    phone TEXT PRIMARY KEY,
    user_id TEXT,
    created_at TEXT
);
```

No passwords or verification codes in this iteration. Phone login is treated as a local demo account identifier. This is realistic enough for product flow without implementing insecure fake password storage.

### Backend endpoints

#### `POST /api/auth/phone-login`

Request:

```json
{
  "phone": "13800138000"
}
```

Response success:

```json
{
  "success": true,
  "data": {
    "session_id": "...",
    "user_id": "user_xxx",
    "user_name": "Bowen"
  }
}
```

Response if not registered:

```json
{
  "success": false,
  "error": {
    "message": "phone not registered"
  }
}
```

#### `POST /api/auth/register`

Request:

```json
{
  "phone": "13800138000",
  "name": "李博文",
  "city": "beijing",
  "age": 25,
  "occupation": "程序员",
  "favorite_foods": "烤肉、牛排、火锅",
  "spice_level": "medium",
  "sweet_level": "low",
  "meat_level": "high",
  "dining_scene": "work_overtime"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "session_id": "...",
    "user_id": "user_...",
    "user_name": "李博文",
    "tags": ["肉食爱好者", "咸鲜满足型", "加班晚餐型"],
    "taste_vector": [...]
  }
}
```

### Profile inference rules

Generate tags and taste vector from registration inputs.

Taste vector length must remain 32 to match existing vector logic.

Known vector sections:

- `[0:6]`: taste dimensions: spicy, sweet, sour, salty, umami, bitter
- `[6:14]`: cuisine dimensions: 川菜, 粤菜, 湘菜, 鲁菜, 日料, 韩餐, 西餐, 东南亚
- `[28:32]`: temporal pattern

Rule examples:

- `meat_level=high`:
  - tags: `肉食爱好者`, `高蛋白偏好`
  - high `umami`, high `salty`
  - raise 韩餐/西餐/鲁菜 scores
- `spice_level=high`:
  - tags: `重口探索型`
  - high `spicy`
  - raise 川菜/湘菜 scores
- `sweet_level=high`:
  - tags: `甜口治愈型`
  - high `sweet`
- `occupation=程序员` or `dining_scene=work_overtime`:
  - tags: `加班晚餐型`
  - raise dinner/late-night temporal dimensions
- `city=beijing`:
  - tags: `北京味觉探索者`
  - raise 鲁菜/西餐/韩餐 depending on food preferences

### Frontend

Refactor `Login.tsx` auth UI into these levels:

```text
entry
  - 登录
  - 注册

login
  - 体验用户登录
  - 手机号登录

login-demo
  - existing role cards

login-phone
  - phone input

register
  - registration form
  - AI生成标签说明
```

Registration form fields:

- phone
- name
- city
- age
- occupation
- favorite foods text
- spice level select
- sweet level select
- meat level select
- dining scene select

After registration succeeds:

- save `currentUserId`
- save `sessionId`
- navigate `/home`

If backend returns inferred tags, show them briefly in the register form area or save to state before navigating. To keep this iteration focused, navigate directly after success and rely on home/profile pages to show resulting tags later.

### Styling

Extend current black-purple login style:

- segmented auth method tabs;
- dark input fields;
- readable form labels;
- register form scroll support on small screens;
- consistent full-width controls.

## Affected files

### Backend

#### `/Users/libowen/Desktop/one-bite-one-world/backend/database.py`

Modification type: add `auth_accounts` table.

Affected function:

- `init_db`

#### `/Users/libowen/Desktop/one-bite-one-world/backend/routers/auth.py`

Modification type: new router.

Functions:

- `phone_login`
- `register`
- `_infer_profile`
- `_create_session`
- `_normalize_phone`

#### `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`

Modification type: import and register auth router.

### Frontend

#### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.tsx`

Modification type: substantial UI state refactor.

Affected logic:

- auth mode state;
- login method state;
- phone login state;
- register form state;
- handlers for demo login, phone login, register;
- current role selection remains for demo login.

#### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.css`

Modification type: extend styles for phone login and register form.

## Implementation details

### Backend auth router pseudo-code

```py
@router.post("/phone-login")
async def phone_login(body: dict):
    phone = _normalize_phone(body.get("phone", ""))
    if not phone:
        return {"success": False, "error": {"message": "phone is required"}}

    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        "SELECT users.id, users.name FROM auth_accounts JOIN users ON users.id=auth_accounts.user_id WHERE auth_accounts.phone=?",
        (phone,)
    )
    user = await cursor.fetchone()
    await db.close()

    if not user:
        return {"success": False, "error": {"message": "phone not registered"}}

    session_id = _create_session(user[0])
    return {"success": True, "data": {"session_id": session_id, "user_id": user[0], "user_name": user[1]}}
```

```py
@router.post("/register")
async def register(body: dict):
    phone = _normalize_phone(body.get("phone", ""))
    name = body.get("name", "").strip()
    if not phone or not name:
        return {"success": False, "error": {"message": "phone and name are required"}}

    tags, vector = _infer_profile(body)
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    await db.execute("INSERT INTO users ...")
    await db.execute("INSERT INTO auth_accounts ...")
    session_id = _create_session(user_id)
```

### Frontend submit handlers

```tsx
const handlePhoneLogin = async () => {
  const res = await api.post('/auth/phone-login', { phone })
  if (!res.data.success) {
    setError('该手机号还未注册，请先注册')
    return
  }
  persistSession(res.data.data)
}
```

```tsx
const handleRegister = async () => {
  const res = await api.post('/auth/register', registerForm)
  if (!res.data.success) {
    setError(res.data.error?.message || '注册失败')
    return
  }
  persistSession(res.data.data)
}
```

## Boundary conditions and exception handling

- Phone number is required for phone login and registration.
- Registration should reject duplicate phone numbers.
- Name is required.
- Age should be parsed as integer and clamped to a sensible range such as 12-100.
- Empty food preference text should still generate a neutral profile.
- Generated taste vector must always have exactly 32 values.
- Existing demo user switch flow must continue working.
- Do not implement password storage or SMS verification in this iteration.
- Do not alter the hardcoded AI key fallback per previous user instruction.
- If registration fails, do not navigate away; show inline error.

## Data flow paths

### Demo login

```text
Login.tsx demo user card
  -> PUT /api/users/me/switch
  -> SESSION[session_id] = user_id
  -> localStorage currentUserId/sessionId
  -> /home
```

### Phone login

```text
Login.tsx phone form
  -> POST /api/auth/phone-login
  -> auth_accounts lookup
  -> SESSION[session_id] = user_id
  -> /home
```

### Register

```text
Login.tsx register form
  -> POST /api/auth/register
  -> backend profile inference
  -> insert users
  -> insert auth_accounts
  -> SESSION[session_id] = new_user_id
  -> /home
```

## Expected outcomes

- Login page feels like a real app entry rather than only demo role selection.
- Users can still quickly enter through experience users.
- Users can log in by phone after registration.
- New users can register by filling personal info.
- Backend generates initial tags and taste vector from the submitted profile.
- The new user appears as a real user in the database and can use profile, recommendations, meals, and matching features.
