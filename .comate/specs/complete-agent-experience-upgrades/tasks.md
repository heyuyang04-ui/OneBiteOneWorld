# Complete Agent Experience Upgrades — Task Plan

- [x] Task 1: Add feedback learning skill and integrate report feedback
    - 1.1: Create `backend/skills/feedback_learning_skill.py`
    - 1.2: Read recent feedback episodes and current user taste vector
    - 1.3: Generate deterministic learning summary and lightweight adjustments
    - 1.4: Update `POST /api/report/feedback` to call feedback learning after saving feedback
    - 1.5: Preserve existing feedback API compatibility

- [x] Task 2: Add memory timeline skill and profile timeline API
    - 2.1: Create `backend/skills/memory_timeline_skill.py`
    - 2.2: Analyze recent meals for timeline chapters such as late-night peak, meat-heavy period, sweet comfort, and repeated safe choices
    - 2.3: Return stable empty-state chapters when data is insufficient
    - 2.4: Add `GET /api/profile/timeline` endpoint in `profile.py`
    - 2.5: Keep existing `/api/profile` response unchanged

- [x] Task 3: Add next meal decision skill and refactor today recommendation
    - 3.1: Create `backend/skills/next_meal_skill.py`
    - 3.2: Load user profile and taste vector
    - 3.3: Incorporate `health_skill` and `mood_food_skill` signals
    - 3.4: Generate preference, balance, explore, and social recommendation groups
    - 3.5: Refactor `GET /api/recommend/today` to call `next_meal_skill`
    - 3.6: Keep frontend response shape compatible with current `Home.tsx`

- [x] Task 4: Add meal companion skill and enrich match detail API
    - 4.1: Create `backend/skills/meal_companion_skill.py`
    - 4.2: Load current and target user taste vectors
    - 4.3: Generate shared foods, avoid notes, best scene, restaurant type, and invite text
    - 4.4: Add `companion_plan` to match detail response
    - 4.5: Preserve existing match detail fields

- [x] Task 5: Add city aggregation skill and live city summary API
    - 5.1: Create `backend/skills/city_aggregation_skill.py`
    - 5.2: Aggregate real `meals` data by user city, cuisine, taste tags, and meal time
    - 5.3: Return mock fallback when real data is insufficient
    - 5.4: Add `GET /api/city/live-summary` endpoint
    - 5.5: Preserve existing city endpoints

- [x] Task 6: Add restaurant match skill and enrich city recommendations
    - 6.1: Create `backend/skills/restaurant_match_skill.py`
    - 6.2: Load user taste vector and mock restaurant data defensively
    - 6.3: Score restaurants by cuisine, city, taste profile, and scene
    - 6.4: Return match score, reasons, recommended dishes, best scenes, and tradeoffs
    - 6.5: Integrate richer restaurant matches into city recommendation endpoint if response shape allows

- [x] Task 7: Add proactive notification skill and trigger after meal upload
    - 7.1: Create `backend/skills/proactive_notify_skill.py`
    - 7.2: Use health and mood signals to detect notification-worthy patterns
    - 7.3: Insert notifications into existing notifications table
    - 7.4: Call proactive notification after meal upload/vector update
    - 7.5: Avoid duplicate notifications for the same upload event

- [x] Task 8: Register all new skills
    - 8.1: Import new skills in `backend/skills/__init__.py`
    - 8.2: Register personal skills under `TASTE_SKILLS`
    - 8.3: Register companion/social skill under `SOCIAL_SKILLS`
    - 8.4: Register city/restaurant skills under `CITY_SKILLS`
    - 8.5: Ensure existing skill registry behavior is unchanged

- [x] Task 9: Update TasteProfile frontend with food autobiography timeline
    - 9.1: Fetch `/api/profile/timeline` in `TasteProfile.tsx`
    - 9.2: Render timeline chapters with title, period, evidence, and meaning
    - 9.3: Add empty state when chapters are insufficient
    - 9.4: Add matching styles without breaking radar/trend charts

- [x] Task 10: Update Home frontend for richer next-meal groups
    - 10.1: Ensure `Home.tsx` handles the new `social` recommendation group
    - 10.2: Preserve existing preference, balance, and explore groups
    - 10.3: Add fallback for missing group fields
    - 10.4: Keep layout width and visual style consistent

- [x] Task 11: Update MatchDetail frontend with companion plan
    - 11.1: Render shared foods and best scene
    - 11.2: Render invite text
    - 11.3: Render avoid notes or tradeoffs
    - 11.4: Preserve existing match explanation and recommendation sections

- [x] Task 12: Update city frontend with live summary and richer restaurant recommendations
    - 12.1: Fetch `/api/city/live-summary` in a suitable city page
    - 12.2: Show whether the city signal source is real aggregation or mock fallback
    - 12.3: Render live cuisine/taste/late-night summary
    - 12.4: Render richer restaurant match fields if available in `CityRecommend.tsx`

- [x] Task 13: Validate backend APIs and frontend build
    - 13.1: Run frontend production build
    - 13.2: Verify `/api/profile/timeline`
    - 13.3: Verify `/api/recommend/today`
    - 13.4: Verify `/api/match/{id}` still responds with existing fields plus companion plan where possible
    - 13.5: Verify `/api/city/live-summary`
    - 13.6: Verify report feedback still works and returns learning info
    - 13.7: Verify meal upload still works or at least proactive notify skill imports and can run directly
    - 13.8: Verify major frontend routes return `200`

- [x] Task 14: Generate implementation summary
    - 14.1: Summarize all new skills and integrations
    - 14.2: Document which requirement gaps are now improved
    - 14.3: Document remaining limitations such as mock city/restaurant data and demo auth
