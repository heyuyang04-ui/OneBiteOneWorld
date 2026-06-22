# Unify App Render Width — Task Plan

- [x] Task 1: Replace global template styles with app shell styles
    - 1.1: Remove Vite template variables and demo selectors from `index.css`
    - 1.2: Define `--app-max-width`, app background, text color, and font stack
    - 1.3: Reset `box-sizing`, body margin, minimum width, and root sizing
    - 1.4: Ensure global styles do not force wide `1126px` layout or centered text

- [x] Task 2: Align main app layout to shared width variable
    - 2.1: Update `.app-container` to use `width: min(100%, var(--app-max-width))`
    - 2.2: Update `.tab-bar` to use the same shared width rule
    - 2.3: Preserve existing fixed bottom navigation behavior and safe-area padding
    - 2.4: Keep main content spacing consistent across pages

- [x] Task 3: Refactor login page to the same app-width shell
    - 3.1: Import `Login.css` in `Login.tsx`
    - 3.2: Replace inline root/page styles with semantic class names
    - 3.3: Render logo, slogan, role list, submit button, and footer within one fixed-width login panel
    - 3.4: Keep role selection and login API logic unchanged
    - 3.5: Replace visually demo-like footer wording with product-style wording

- [x] Task 4: Add login page CSS for consistent card sizing
    - 4.1: Create `Login.css`
    - 4.2: Apply the same max-width as the authenticated app shell
    - 4.3: Make role cards and login button fill the same width
    - 4.4: Set consistent role-card min-height, spacing, and selected state
    - 4.5: Ensure small screens do not overflow horizontally

- [x] Task 5: Remove unused Vite App.css styles and validate rendering build
    - 5.1: Replace `App.css` template styles with a no-op app comment or minimal safe styles
    - 5.2: Run frontend production build
    - 5.3: Check frontend dev server is reachable
    - 5.4: Confirm `/login` and `/` use the same centered app width conceptually
