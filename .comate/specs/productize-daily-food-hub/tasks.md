# Productize Daily Food Hub — Task Plan

- [x] Task 1: Add today recommendation backend API
    - 1.1: Create recommendation router for `GET /api/recommend/today`
    - 1.2: Load current user profile and taste vector from SQLite
    - 1.3: Generate deterministic daily taste state, signals, quick actions, and three recommendation groups
    - 1.4: Return structured success and failure responses without calling LLM
    - 1.5: Register the recommendation router in `main.py`

- [x] Task 2: Protect meal detail loading by current user
    - 2.1: Update `GET /api/meals/{meal_id}` to receive `Request`
    - 2.2: Query meal by both `id` and `request.state.user_id`
    - 2.3: Preserve existing response shape for valid current-user meals
    - 2.4: Return not-found response for missing or unauthorized meals

- [x] Task 3: Productize Home page into a daily food hub
    - 3.1: Fetch `/api/recommend/today` alongside notifications
    - 3.2: Add loading and fallback handling for recommendation data
    - 3.3: Replace upload-only banner with personalized daily state section
    - 3.4: Render recommendation groups for preference, balance, and exploration choices
    - 3.5: Render quick action chips and keep the existing meal upload flow
    - 3.6: Update Home page styles for hub cards, recommendation cards, and responsive spacing

- [x] Task 4: Make MealResult refresh-safe and more actionable
    - 4.1: Read `meal_id` from route params
    - 4.2: Use navigation state immediately when available
    - 4.3: Fetch `/api/meals/{meal_id}` when navigation state is missing
    - 4.4: Add loading, error, and not-found states
    - 4.5: Add meal impact explanation and next-meal suggestion sections
    - 4.6: Update MealResult styles for new sections

- [x] Task 5: Validate the productized user flow
    - 5.1: Run frontend build or TypeScript check
    - 5.2: Restart or rely on backend reload and verify `/api/recommend/today`
    - 5.3: Verify home page loads recommendation cards for Bowen
    - 5.4: Verify uploaded meal result page still renders immediately
    - 5.5: Verify refreshing `/meal/:id` reloads persisted meal details
