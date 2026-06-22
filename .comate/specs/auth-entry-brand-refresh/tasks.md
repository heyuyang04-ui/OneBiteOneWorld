# Auth Entry Brand Refresh — Task Plan

- [x] Task 1: Change root route into auth entry
    - 1.1: Update `/` route to render `Login`
    - 1.2: Keep `/login` route rendering `Login`
    - 1.3: Move authenticated home route from `/` to `/home`
    - 1.4: Keep protected routes under `ProtectedLayout`
    - 1.5: Update protected wildcard redirect to `/home`

- [x] Task 2: Update navigation paths for the new home route
    - 2.1: Change bottom tab home path from `/` to `/home`
    - 2.2: Preserve active-state behavior for the home tab
    - 2.3: Check existing navigation calls that should now target `/home`

- [x] Task 3: Refactor Login page into login/register entry
    - 3.1: Import and display `frontend/src/assets/hero.png`
    - 3.2: Remove automatic redirect when `currentUserId` already exists
    - 3.3: Add `登录` and `注册` entry mode choices
    - 3.4: Render role selection after choosing login or register mode
    - 3.5: Change successful entry navigation from `/` to `/home`
    - 3.6: Show saved identity hint when local login state exists

- [x] Task 4: Refresh global and shell colors to banner-inspired black-purple palette
    - 4.1: Update global CSS variables in `index.css`
    - 4.2: Update body/root background colors
    - 4.3: Update app header gradient in `Layout.css`
    - 4.4: Update tab bar colors and active state
    - 4.5: Preserve the unified 430px app width

- [x] Task 5: Rebuild Login page visual styles
    - 5.1: Rewrite `Login.css` with dark/purple background
    - 5.2: Style hero image, brand title, and product slogan
    - 5.3: Style login/register choice buttons
    - 5.4: Style role cards as consistent translucent surfaces
    - 5.5: Ensure small-screen layout remains usable

- [x] Task 6: Update Home hero accents to match refreshed brand
    - 6.1: Update `Home.css` hero gradient from gray/orange to black-purple
    - 6.2: Update signal and recommendation tag accents to purple palette
    - 6.3: Keep content card readability on existing warm/light surfaces

- [x] Task 7: Validate routing and rendering
    - 7.1: Run frontend production build
    - 7.2: Verify `http://localhost:5173/` returns the auth entry route
    - 7.3: Verify `http://localhost:5173/login` returns the auth entry route
    - 7.4: Verify protected `/home` remains accessible after selecting a role
    - 7.5: Verify unauthenticated `/home` redirects to `/login`
