# Food Life Insight Skills — Task Plan

- [x] Task 1: Implement health insight skill
    - 1.1: Create `backend/skills/health_skill.py`
    - 1.2: Load recent meals for the current user from SQLite
    - 1.3: Safely parse `taste_tags`, `nutrition`, and `meal_time`
    - 1.4: Calculate health/lifestyle metrics such as meal count, average calories, late-night count, heavy-taste count, and high-calorie count
    - 1.5: Generate health score, risk level, structured signals, and actionable suggestions
    - 1.6: Return stable empty-state payload when meal data is insufficient

- [x] Task 2: Implement mood food insight skill
    - 2.1: Create `backend/skills/mood_food_skill.py`
    - 2.2: Load recent meals for the current user from SQLite
    - 2.3: Calculate late-night ratio, heavy-taste ratio, sweet ratio, high-calorie ratio, and repeated cuisine/dish ratio
    - 2.4: Infer strongest lifestyle/eating pattern state
    - 2.5: Generate confidence, evidence, reflection, and reflection question
    - 2.6: Return stable empty-state payload when meal data is insufficient

- [x] Task 3: Register new skills in the skill registry
    - 3.1: Import `health_skill` and `mood_food_skill` in `backend/skills/__init__.py`
    - 3.2: Add both skills to `TASTE_SKILLS`
    - 3.3: Keep existing skill registry behavior unchanged for social and city agents

- [x] Task 4: Integrate health and mood insights into weekly report backend
    - 4.1: Import new skills in `report_skill.py`
    - 4.2: Call `health_skill` and `mood_food_skill` during weekly report generation
    - 4.3: Add health and mood context to the LLM prompt
    - 4.4: Preserve existing `summary`, `highlights`, `reflection`, and `data_summary` fields
    - 4.5: Add `health_insight` and `mood_insight` fields to the response payload
    - 4.6: Ensure report still works when there are no meals or LLM output parsing fails

- [x] Task 5: Update WeeklyReport frontend rendering
    - 5.1: Inspect existing `WeeklyReport.tsx` and CSS conventions
    - 5.2: Render health insight score, risk level, signals, suggestions, and metrics
    - 5.3: Render mood insight state, confidence, evidence, reflection, and question
    - 5.4: Keep existing summary, highlights, reflection, and feedback interactions unchanged
    - 5.5: Add empty/fallback display where insight fields are missing

- [x] Task 6: Add WeeklyReport insight card styles
    - 6.1: Locate or create the weekly report CSS used by `WeeklyReport.tsx`
    - 6.2: Add styles for health card, score badge, signal list, suggestions, mood card, evidence list, and reflection question
    - 6.3: Match current black-purple brand direction while keeping report content readable
    - 6.4: Ensure mobile width and spacing remain consistent

- [ ] Task 7: Validate backend and frontend behavior
    - 7.1: Run frontend production build
    - 7.2: Verify `GET /api/report/weekly` returns `health_insight` and `mood_insight`
    - 7.3: Verify report endpoint remains stable for a user with no meals
    - 7.4: Verify WeeklyReport page route is reachable
    - 7.5: Verify existing upload, report, and feedback APIs still respond
