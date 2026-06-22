# Food Life Insight Skills

## Requirement scenario and processing logic

The product requirement document emphasizes that “each person’s food is an unread autobiography.” The current app already supports food upload, taste profile, weekly report, matching, and city exploration, but it still lacks the most distinctive experience promised by the concept: connecting dietary behavior to life state, health signals, and reflective insight.

This iteration will implement the first high-value enhancement:

- `health_skill`: analyzes recent meals and produces a lightweight health/lifestyle score, risk signals, and actionable suggestions.
- `mood_food_skill`: analyzes changes in meal timing, taste tags, calories, and repeated patterns to infer possible lifestyle/emotional eating signals.
- Integrate these insights into weekly report output and the frontend weekly report page so users can see not only “what I ate” but “what my eating pattern may be saying about me.”

Target user value:

```text
I uploaded meals for several days.
The app does not only show calories and taste charts.
It tells me: late-night meals increased, heavy savory/meat meals increased, sweet/high-satisfaction foods changed, and this may indicate overtime compensation, stress eating, or taste fatigue.
Then it gives me practical next-week suggestions.
```

## Current code context

Relevant existing implementation:

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/report_skill.py`
  - Generates weekly report from recent meals using LLM.
  - Currently summarizes meal_count, avg_calories, top_cuisines, taste_avg, late_night_meals.

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/report.py`
  - Exposes `/api/report/weekly` and feedback endpoint.

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/WeeklyReport.tsx`
  - Renders report summary, highlights, reflection, and feedback buttons.

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/__init__.py`
  - Registers current skills under `TASTE_SKILLS`, `SOCIAL_SKILLS`, and `CITY_SKILLS`.

- `/Users/libowen/Desktop/one-bite-one-world/backend/agents/agents.py`
  - Defines TasteAgent, SocialAgent, CityAgent.

- `/Users/libowen/Desktop/one-bite-one-world/backend/agents/orchestrator.py`
  - Routes events to existing agents.

## Architecture and technical approach

### Scope decision

Do not introduce a new full `HealthAgent` in this first step. Add the two new skills under existing `TasteAgent` scope because health and mood insights are derived from personal meal history and fit the current TasteAgent role.

This keeps the change controlled and immediately useful.

### New backend skills

#### `backend/skills/health_skill.py`

Purpose:

Analyze recent meal records and return structured health/lifestyle signals.

Input:

```py
health_skill(user_id: str, params: dict)
```

Params:

- `days`: default 14
- `limit`: default 50

Output shape:

```json
{
  "health_score": 72,
  "risk_level": "medium",
  "signals": [
    {
      "type": "late_night",
      "title": "夜间进食偏多",
      "description": "最近记录中有 4 餐发生在 21 点后。",
      "severity": "medium"
    }
  ],
  "suggestions": [
    "下周至少安排 2 次清爽型晚餐。",
    "如果继续吃肉，优先选择烤鱼、牛肉汤或鸡肉饭。"
  ],
  "metrics": {
    "meal_count": 12,
    "avg_calories": 762,
    "late_night_count": 4,
    "heavy_taste_count": 6,
    "high_calorie_count": 5
  }
}
```

Rule examples:

- Average calories > 850: subtract score and add `high_calorie` signal.
- late night meals >= 30%: add `late_night` signal.
- high salty/umami/spicy meals >= 50%: add `heavy_taste` signal.
- protein very low where nutrition exists: add `low_protein` suggestion.
- If no meals: return neutral empty-state insight.

#### `backend/skills/mood_food_skill.py`

Purpose:

Infer lifestyle/emotional eating patterns from recent meal behavior.

Output shape:

```json
{
  "state": "压力补偿型进食",
  "confidence": 0.68,
  "evidence": [
    "晚餐和夜宵记录占比偏高",
    "咸鲜/肉食满足感信号明显",
    "高热量餐食出现频率较高"
  ],
  "reflection": "你最近可能不是单纯想吃重口，而是在用高满足感食物对冲疲惫。",
  "question": "这周哪几顿饭更像是在犒劳自己，而不是因为真的饿？"
}
```

Rule examples:

- high late-night + heavy taste + high calorie: `压力补偿型进食`.
- sweet preference increase/high sweet meals: `甜口安慰型进食`.
- repeated same cuisine/dish: `安全感重复选择`.
- high sour/light meals after heavy meals: `口味疲劳修复`.
- Not enough meals: `记录积累期`.

### Report integration

Modify `report_skill.py`:

- Import `health_skill` and `mood_food_skill`.
- Call both skills when generating weekly report.
- Include structured insight in the LLM prompt.
- Add `health_insight` and `mood_insight` to returned payload.

Return shape extension:

```json
{
  "summary": "...",
  "highlights": [...],
  "reflection": "...",
  "data_summary": {...},
  "health_insight": {...},
  "mood_insight": {...}
}
```

### Frontend integration

Modify `WeeklyReport.tsx`:

- Render `health_insight` card if present:
  - score
  - risk level
  - signals
  - suggestions
- Render `mood_insight` card if present:
  - state
  - confidence
  - evidence
  - reflection question

Modify `WeeklyReport.css` or inline styles depending on existing styling. Prefer editing existing CSS file if present; otherwise add styles in existing page CSS only if it exists. First inspect actual file structure during tasks.

### Skills registration

Modify `backend/skills/__init__.py`:

- Import new skills.
- Add them to `TASTE_SKILLS`.

No orchestrator route changes are required for this iteration because weekly report directly calls `report_skill`, and report_skill will call the new skills.

## Affected files

### New files

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/health_skill.py`
  - New deterministic health/lifestyle analysis skill.

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/mood_food_skill.py`
  - New deterministic mood/lifestyle eating pattern analysis skill.

### Existing files to modify

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/report_skill.py`
  - Add health and mood insight generation.
  - Add insight context to LLM prompt.
  - Return structured insights.

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/__init__.py`
  - Register new skills under `TASTE_SKILLS`.

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/WeeklyReport.tsx`
  - Display health insight and mood food insight.

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/WeeklyReport.css`
  - If existing, add styles for insight cards.
  - If not existing, inspect imports and style according to existing page convention.

## Implementation details

### Shared meal loading helper approach

To avoid premature abstraction, each new skill can independently load recent meals from SQLite using the same query pattern. If duplicated code becomes too large, only then create a small local helper inside each skill. Do not create a shared utility in this iteration unless needed.

### Meal query

```sql
SELECT dish_name, cuisine_type, taste_tags, nutrition, meal_time
FROM meals
WHERE user_id=?
ORDER BY meal_time DESC
LIMIT ?
```

### Health score formula

Start at 86.

Subtract:

- `late_night_ratio >= 0.3`: -10
- `avg_calories >= 850`: -10
- `heavy_taste_ratio >= 0.5`: -8
- `high_calorie_ratio >= 0.4`: -8
- `meal_count < 3`: score neutral 70 with low-confidence message

Clamp to 40-95.

This score is not a medical diagnosis. It is a lifestyle reflection score.

### Mood inference formula

Use heuristic confidence:

- `late_night_ratio`
- `heavy_taste_ratio`
- `sweet_ratio`
- `repeat_ratio`
- `avg_calories`

Select state by strongest pattern.

## Boundary conditions and exception handling

- If there are no meals, both skills must return stable empty-state payloads.
- JSON parsing of `taste_tags` and `nutrition` must be guarded.
- Missing nutrition values should not crash analysis.
- Scores and confidence must be clamped.
- Do not present health insight as medical advice.
- Do not call LLM from health/mood skills; keep them deterministic and fast.
- Keep current weekly report API backward-compatible by preserving existing `summary`, `highlights`, and `reflection` fields.
- Do not modify auth/session logic in this iteration.

## Data flow paths

### Weekly report with new skills

```text
Frontend WeeklyReport.tsx
  -> GET /api/report/weekly
  -> report_skill(user_id)
  -> load recent meals
  -> health_skill(user_id)
  -> mood_food_skill(user_id)
  -> LLM report generation with health/mood context
  -> response includes summary/highlights/reflection/health_insight/mood_insight
  -> frontend renders report + health/mood cards
```

### Future extension path

These skills can later be called by:

- proactive notification generation;
- home page daily insight;
- profile page “饮食自传” timeline;
- HealthAgent if added later.

## Expected outcomes

- Weekly report becomes much closer to the requirement document’s “food as autobiography” concept.
- Users see practical health/lifestyle signals, not only LLM prose.
- Users receive reflective questions tied to their eating pattern.
- The project gains two meaningful skills that strengthen Agent experience without destabilizing existing flows.
