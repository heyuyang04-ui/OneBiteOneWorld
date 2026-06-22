# Auth Entry Brand Refresh

## Requirement scenario and processing logic

The user reported two product-level UI problems:

1. Opening `http://localhost:5173` enters the app content directly when local login state exists. The product should first present a registration/login choice, then continue into the app.
2. The current color tone feels wrong. The user asked to reference the project banner. The available visual reference is `/Users/libowen/Desktop/one-bite-one-world/frontend/src/assets/hero.png`, which uses a black/deep-purple layered visual style rather than the current warm beige/orange tone.

Target first-run path:

```text
http://localhost:5173
  -> show auth entry page with brand banner and two actions: 登录 / 注册
  -> user chooses login or register mode
  -> selects/creates an experience identity
  -> enters app home
```

For the current project scope, “注册” should be implemented as a product-facing onboarding/register mode using the existing preset role system, not a full password-based account system. This keeps the app coherent while avoiding overbuilding backend auth in this iteration.

## Current behavior and root cause

### Current root route behavior

`/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx` defines `/` as the authenticated `Home` route:

```tsx
<Route element={<ProtectedLayout />}>
  <Route path="/" element={<Home />} />
```

`ProtectedLayout` only checks `localStorage.currentUserId`. If it exists, opening `/` goes straight to `Home`.

### Current login auto-skip behavior

`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.tsx` currently redirects immediately if `currentUserId` exists:

```tsx
const saved = localStorage.getItem('currentUserId')
if (saved) {
  navigate('/', { replace: true })
  return
}
```

This means the user cannot reliably see login/register entry again unless localStorage is cleared or they log out.

### Current color tone

Current global and page styles use warm beige/orange:

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/index.css`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.css`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.css`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.css`

The banner asset `frontend/src/assets/hero.png` suggests a different visual direction:

- black / near-black canvas;
- purple gradient accent;
- layered card/platform feeling;
- more “Agent / tech product” than “warm food diary”.

## Architecture and technical approach

### Entry strategy

Change the product entry so `/` is the auth entry page, not the app home.

Proposed routes:

```tsx
<Route path="/" element={<Login />} />
<Route path="/login" element={<Login />} />
<Route element={<ProtectedLayout />}>
  <Route path="/home" element={<Home />} />
  ...
</Route>
```

After successful login/register selection:

```tsx
navigate('/home', { replace: true })
```

Bottom tab home link should also point to `/home`.

This guarantees `http://localhost:5173` always starts with the auth entry experience.

### Login/register UX

Update `Login.tsx` to show an explicit entry choice first:

- Brand visual area using `hero.png`.
- Two mode buttons:
  - `登录`
  - `注册`
- Login mode:
  - Shows existing preset identities as “选择已有身份登录”.
- Register mode:
  - Shows the same identity cards as “选择一个初始饮食身份开始创建画像”.
  - The backend can still use existing role switch API for now.

This is intentionally not a full account system because backend auth, password storage, verification, and user creation are outside the focused visual/entry fix.

### Brand color refresh

Introduce a black-purple brand palette in global CSS:

```css
:root {
  --app-shell-bg: #08050F;
  --app-bg: #110B1D;
  --app-surface: rgba(255,255,255,0.08);
  --app-surface-strong: rgba(255,255,255,0.12);
  --app-text: #F8F3FF;
  --app-muted: #B8A9D9;
  --app-accent: #8B5CF6;
  --app-accent-2: #D946EF;
  --app-border: rgba(255,255,255,0.14);
}
```

Update visible shells:

- Login page background and cards.
- App header gradient.
- Tab bar background/active state.
- Home hero background.

Do not repaint every page in this iteration. The goal is to make the entry and main shell feel coherent first. Existing white cards on inner pages can remain if they are readable, but global shell and top-level surfaces should no longer feel beige/orange.

## Affected files

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx`

Modification type: route entry change.

Affected logic:

- Make `/` render `Login`.
- Move authenticated `Home` from `/` to `/home`.
- Update fallback route behavior if needed.

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.tsx`

Modification type: update bottom navigation home path.

Affected code:

```tsx
{ path: '/', icon: '📷', label: '首页' }
```

Change to:

```tsx
{ path: '/home', icon: '📷', label: '首页' }
```

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.tsx`

Modification type: auth entry refactor.

Affected functions:

- `Login` component render logic.
- Remove auto-redirect when saved `currentUserId` exists.
- Add mode state: `entry`, `login`, `register` or simpler `authMode`.
- Use `hero.png` asset.
- Navigate to `/home` after successful selection.

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.css`

Modification type: full brand refresh for auth entry page.

Expected visual changes:

- dark/purple background;
- hero image shown near top;
- login/register choice cards/buttons;
- role cards with translucent dark surfaces;
- consistent width with existing mobile shell.

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/index.css`

Modification type: update global CSS variables to black-purple brand palette.

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.css`

Modification type: update shell/header/tab colors to match black-purple palette.

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.css`

Modification type: update top hero and key accents to align with banner-inspired purple visual direction.

## Implementation details

### App route change

```tsx
<Routes>
  <Route path="/" element={<Login />} />
  <Route path="/login" element={<Login />} />
  <Route element={<ProtectedLayout />}>
    <Route path="/home" element={<Home />} />
    ...
    <Route path="*" element={<Navigate to="/home" />} />
  </Route>
</Routes>
```

### Login mode behavior

```tsx
const [mode, setMode] = useState<'entry' | 'login' | 'register'>('entry')
```

Entry screen shows:

```tsx
<button onClick={() => setMode('login')}>登录</button>
<button onClick={() => setMode('register')}>注册</button>
```

When selecting a role and entering:

```tsx
localStorage.setItem('currentUserId', selected)
await api.put('/users/me/switch', { user_id: selected })
navigate('/home', { replace: true })
```

### Existing login state handling

Do not auto-redirect from `/` just because `currentUserId` exists. Instead show entry page and optionally display:

```text
已保存上次身份，可继续登录或切换身份
```

This addresses the user's direct complaint that `localhost:5173` should first show login/register.

## Boundary conditions and exception handling

- Do not implement real password registration in this iteration.
- Do not change backend user schema.
- Do not delete existing role-switch behavior.
- If `/home` is opened without login state, `ProtectedLayout` still redirects to `/login`.
- If an existing user opens `/`, they should still see the auth entry page rather than being pushed into app content.
- Maintain the unified 430px shell from the previous width fix.
- Ensure text contrast is readable on dark backgrounds.
- Avoid changing the hardcoded AI key fallback because the user explicitly requested not to modify it earlier.

## Data flow paths

### New root entry flow

```text
GET http://localhost:5173
  -> React route `/`
  -> Login auth entry page
  -> choose 登录 or 注册
  -> select identity
  -> PUT /api/users/me/switch
  -> localStorage currentUserId/session if available
  -> navigate('/home')
```

### Direct protected route flow

```text
GET /home
  -> ProtectedLayout checks localStorage.currentUserId
  -> missing: redirect `/login`
  -> exists: render Layout + Home
```

## Expected outcomes

- `http://localhost:5173` no longer drops directly into app content.
- The first screen clearly offers `登录` and `注册`.
- Existing users can still choose/continue identity from the entry screen.
- The product visual tone references the existing banner asset: darker, purple, layered, more Agent/tech-forward.
- Login and authenticated app remain the same width and no longer feel like separate visual products.
