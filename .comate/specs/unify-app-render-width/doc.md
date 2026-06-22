# Unify App Render Width

## Requirement scenario and processing logic

The user reported that the current rendering feels inconsistent: some screens are wide while others are narrow, and the first transition is abrupt. The experience should start consistently from the login page, not only after entering the main app.

Current observed issue:

- `Login.tsx` uses inline full-screen layout (`minHeight: 100vh`, centered content, no app-width shell).
- `Layout.css` uses a mobile app container with `max-width: 430px`.
- `index.css` still contains Vite template styles where `#root` has `width: 1126px`, `text-align: center`, border styles, and dark-mode variables unrelated to this app.
- Result: login page looks like a full browser landing page, while the authenticated app suddenly becomes a narrow mobile shell.

Target behavior:

1. The app should use one consistent visual shell from `/login` onward.
2. Login page and all in-app pages should share the same maximum width.
3. On large screens, the app should remain centered like a mobile app preview.
4. On small screens, the app should fill available viewport width without horizontal jumps.
5. Remove old Vite template global styles that affect width, typography, background, and text alignment.

## Architecture and technical approach

### Global shell

Use a shared mobile-app viewport width:

- `--app-max-width: 430px`
- body background: warm neutral app background
- `#root`: full width, centered, no fixed `1126px`, no template border

This ensures all routes render inside the same visual boundary.

### Login page

Convert login from inline styles to class-based CSS and apply the same app width as the main container:

- Add `Login.css`.
- Wrap login content in `.login-page` and `.login-panel`.
- Set `.login-page` to max-width `var(--app-max-width)` and centered.
- Preserve current role-selection logic.
- Remove abrupt full-browser layout.
- Remove or soften the `Hackathon Demo` copy if it visually hurts real-product feel; in this task, prefer replacing it with a product-style tagline rather than deleting functional content.

### Main layout

Update `Layout.css` to use the same CSS variable instead of hard-coded `430px`.

### App template cleanup

Replace `index.css` with app-specific global styles:

- `box-sizing: border-box`
- body margin reset
- app font stack
- root centered shell
- consistent background
- remove template `h1`, `h2`, `code`, `.counter`, and Vite demo styles.

`App.css` currently contains unused Vite template styles and should be emptied or reduced to no-op styles if still imported. If not imported, it can remain but should not affect rendering. Since it may be imported elsewhere, remove template selectors to prevent accidental styling.

## Affected files

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/index.css`

Modification type: replace Vite template global CSS with app-specific global CSS.

Affected selectors:

- `:root`
- `body`
- `#root`
- universal box sizing

Expected key result:

```css
:root {
  --app-max-width: 430px;
  --app-bg: #F5F0EB;
  --app-page-bg: #FDF8F0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  min-width: 320px;
  background: #E9DED4;
}

#root {
  min-height: 100vh;
  width: 100%;
}
```

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/Layout.css`

Modification type: align `.app-container` and `.tab-bar` to global app width.

Affected selectors:

- `.app-container`
- `.tab-bar`
- `.app-main`

Expected key result:

```css
.app-container {
  width: min(100%, var(--app-max-width));
  margin: 0 auto;
}

.tab-bar {
  width: min(100%, var(--app-max-width));
}
```

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.tsx`

Modification type: remove inline layout styles and use semantic class names.

Affected functions:

- `Login` component render block only.

Expected changes:

- Import `./Login.css`.
- Replace inline root div with `<div className="login-page">`.
- Replace inline role cards/buttons with CSS classes.
- Keep existing `HERO_USERS`, selection logic, and API call unchanged.

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Login.css`

Modification type: new CSS file for login page.

Key styles:

- same max width as app container;
- consistent background;
- card sizing fixed to full container width;
- role card fixed/min heights to avoid inconsistent card size;
- enter button full width;
- product-style footer text.

### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.css`

Modification type: remove unused Vite template styles to avoid accidental render interference.

## Implementation details

### Login component structure

```tsx
return (
  <div className="login-page">
    <section className="login-panel">
      <div className="login-logo">...</div>
      <p className="login-slogan">...</p>
      <div className="role-list">...</div>
      <button className="login-submit">...</button>
      <p className="login-footer">Agent 驱动的城市味觉感知系统</p>
    </section>
  </div>
)
```

### Consistent size rule

All main route roots should be visually inside:

```css
width: min(100%, var(--app-max-width));
margin: 0 auto;
```

The main app layout already does this through `.app-container`; login should do the same.

## Boundary conditions and exception handling

- Do not change routing or login business logic.
- Do not change backend behavior.
- Do not make desktop layout wider in this task; the user explicitly asked for equal sizes.
- Role descriptions should not cause uneven card widths; cards should fill the same width and align consistently.
- On very small screens, the app should not overflow horizontally.
- Keep touch-friendly spacing for mobile.

## Data flow paths

No backend data flow changes.

UI flow after fix:

```text
/login
  -> centered app-width login shell
  -> select role
  -> navigate('/')
  -> same app-width authenticated shell
```

## Expected outcomes

- Login and main app have consistent width from the first screen.
- No sudden wide-to-narrow visual jump after login.
- Cards and buttons align to the same width.
- Old Vite template global CSS no longer affects rendering.
- The app feels more like a single real mobile product experience rather than separate demo pages.
