# Complete Agent Experience Upgrades

## Requirement scenario and processing logic

The user wants to address all remaining gaps identified from `/Users/libowen/Desktop/one-bite-one-world/一食万象.md` and add the proposed skills/agents to make the app closer to the full product vision.

Current major gaps:

1. User feedback is recorded but does not truly improve the user profile.
2. The product says “food is an autobiography,” but there is no timeline-style food-life narrative.
3. Today recommendation exists, but its logic lives in a router and does not use health/mood context deeply.
4. Taste matching exists, but it does not convert into a concrete meal companion / invite action.
5. City pages rely heavily on mock data and do not aggregate real user meal records.
6. Restaurant recommendation lacks explicit match scoring and tradeoff explanation.
7. Notifications exist, but the Agent is not proactive enough.

This iteration will add a complete set of skills and lightweight agent integrations:

- `feedback_learning_skill.py`
- `memory_timeline_skill.py`
- `next_meal_skill.py`
- `meal_companion_skill.py`
- `city_aggregation_skill.py`
- `restaurant_match_skill.py`
- `proactive_notify_skill.py`

It will also integrate these capabilities into existing pages/API endpoints with minimal product disruption.

## Architecture and technical approach

### Guiding principle

Keep the implementation deterministic, fast, and demo-stable. Do not introduce new external services. Use existing SQLite data, existing user taste vectors, existing meals, existing matches, existing notifications, and existing mock restaurant data where needed.

This improves user experience without overbuilding a production authentication, map, or data platform.

## Sub-requirement 1: FeedbackLearningSkill

### Scenario

Users can already give feedback on weekly report highlights, but that feedback is only stored and does not change future recommendations or profile behavior.

### Technical approach

Add:

```text
backend/skills/feedback_learning_skill.py
```

Responsibilities:

- Read feedback from `episodes`.
- Summarize positive/negative feedback signals.
- Apply small deterministic adjustments to `users.taste_vector` where possible.
- Return a learning summary for UI/API use.

Add feedback handling to existing report feedback route:

- After saving feedback, call `feedback_learning_skill` with the feedback event.
- Keep response backward-compatible.

### Expected output

```json
{
  "updated": true,
  "learning_summary": "Agent 已记录这次反馈，并会降低类似洞察的置信度。",
  "adjustments": ["降低周报洞察置信度", "记录用户不认可该模式"]
}
```

### Affected files

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/feedback_learning_skill.py` new
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/report.py` modify feedback endpoint
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/__init__.py` register skill
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/WeeklyReport.tsx` optionally show feedback learned toast/state

## Sub-requirement 2: MemoryTimelineSkill

### Scenario

The product concept says each person’s food is an unread autobiography. Users need a “饮食自传” narrative, not just charts.

### Technical approach

Add:

```text
backend/skills/memory_timeline_skill.py
```

Responsibilities:

- Analyze recent meals by time, cuisine, taste tags, calories, and meal hour.
- Generate timeline chapters using deterministic pattern rules.
- Reuse signals from health/mood style logic when possible without creating tight coupling.

Add endpoint:

```text
GET /api/profile/timeline
```

or add to existing profile router.

### Expected output

```json
{
  "chapters": [
    {
      "title": "加班夜里的烤肉高峰",
      "period": "最近 7 餐",
      "evidence": ["晚餐时间后移", "肉食频率上升", "鲜味指数上升"],
      "meaning": "这段时间你的饮食更像是一种犒劳和补偿。"
    }
  ]
}
```

### Frontend integration

Add timeline section to `TasteProfile.tsx` rather than creating a new page, to keep navigation simple.

### Affected files

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/memory_timeline_skill.py` new
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/profile.py` add endpoint
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/__init__.py` register skill
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/TasteProfile.tsx` render timeline
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/TasteProfile.css` or existing styles update

## Sub-requirement 3: NextMealDecisionSkill

### Scenario

Home page asks “今天吃什么,” but current recommendation logic is in `routers/recommend.py`. It should become a reusable skill that incorporates health and mood context.

### Technical approach

Add:

```text
backend/skills/next_meal_skill.py
```

Responsibilities:

- Load user taste vector and profile.
- Load recent meals.
- Use `health_skill` and `mood_food_skill` outputs.
- Return three recommendation groups:
  - `preference`: satisfy current taste preference.
  - `balance`: reduce risk/taste fatigue.
  - `explore`: city/local novelty.
  - `social`: optional meal-with-someone suggestion.

Refactor `/api/recommend/today` to call `next_meal_skill`.

### Affected files

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/next_meal_skill.py` new
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/recommend.py` refactor
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/__init__.py` register skill
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx` optionally render new social group if present

## Sub-requirement 4: MealCompanionSkill / Companion experience

### Scenario

The matching feature should not stop at “this user is similar.” It should answer: “What can we eat together, where, and how do I invite them?”

### Technical approach

Add:

```text
backend/skills/meal_companion_skill.py
```

Responsibilities:

- Load current user and other user taste vectors.
- Compute shared taste strengths and differences.
- Generate shared foods, avoid suggestions, restaurant type, and invite text.

Add to match detail endpoint:

- Return `companion_plan` in `GET /api/match/{id}`.

### Expected output

```json
{
  "shared_foods": ["烤肉", "火锅", "烤鱼"],
  "avoid": ["甜品店作为第一次约饭可能不是最佳选择"],
  "invite_text": "系统发现我们都喜欢咸鲜和肉食，要不要这周找一家烤肉店？",
  "best_scene": "周五晚餐 / 下班后"
}
```

### Frontend integration

Update `MatchDetail.tsx`:

- Add “一起吃什么” card.
- Add invite text copy block.
- Add not-suitable reminder.

### Affected files

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/meal_companion_skill.py` new
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/match.py` include companion plan
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/__init__.py` register skill
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MatchDetail.tsx` render plan
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MatchDetail.css` if existing, or page styling

## Sub-requirement 5: CityAggregationSkill

### Scenario

City pages should not rely only on mock JSON. Even in demo, they should aggregate real `meals` table data where available.

### Technical approach

Add:

```text
backend/skills/city_aggregation_skill.py
```

Responsibilities:

- Aggregate real meals by city, cuisine, taste tags, calories, and time.
- Return real summary if enough meals exist.
- Fall back to mock city data if not enough data.

Add endpoint or update existing city endpoint:

```text
GET /api/city/live-summary?city=beijing
```

### Expected output

```json
{
  "city": "beijing",
  "source": "real" | "mock_fallback",
  "meal_count": 18,
  "hot_cuisines": [...],
  "taste_trends": {...},
  "late_night_ratio": 0.32,
  "heavy_taste_ratio": 0.48
}
```

### Frontend integration

Update `CityMap.tsx` or `CityTrends.tsx` to show whether current city signal is real aggregation or mock fallback.

### Affected files

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/city_aggregation_skill.py` new
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/city.py` add/update endpoint
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/__init__.py` register skill
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx` or `CityTrends.tsx` show live summary

## Sub-requirement 6: RestaurantMatchSkill

### Scenario

Restaurant recommendations should explain why a restaurant is suitable for this user, what to order, and tradeoffs.

### Technical approach

Add:

```text
backend/skills/restaurant_match_skill.py
```

Responsibilities:

- Load user taste vector.
- Load restaurants from `mock_restaurants.json` for now.
- Score restaurants by cuisine, tags, city, user taste, health/mood signals.
- Return match score, reasons, recommended dishes, scene, and tradeoff.

Integrate into city recommend endpoint and/or match companion plan.

### Expected output

```json
{
  "restaurant": "聚点烤肉",
  "match_score": 0.91,
  "reason": "你的咸鲜、肉食、晚餐偏好与该餐厅高度匹配。",
  "recommended_dishes": ["牛五花", "调味牛排"],
  "best_for": ["下班后", "朋友聚餐"],
  "tradeoff": "油脂偏高，建议搭配蔬菜。"
}
```

### Affected files

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/restaurant_match_skill.py` new
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/city.py` or `recommend.py` integrate
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/__init__.py` register skill
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityRecommend.tsx` render richer recommendation cards

## Sub-requirement 7: ProactiveNotifySkill / proactive Agent experience

### Scenario

Notifications exist but are passive. The Agent should proactively surface insights when meaningful patterns occur.

### Technical approach

Add:

```text
backend/skills/proactive_notify_skill.py
```

Responsibilities:

- Call health/mood/next meal/match signals.
- Generate notifications when patterns are detected:
  - no meals for several days;
  - late-night ratio high;
  - heavy-taste ratio high;
  - new mutual match;
  - city live trend available;
  - weekly report ready.
- Write notifications into `notifications` table through existing notify logic or direct DB insert.

Integrate minimally:

- Call after meal upload in `meals.py`.
- Optionally call when weekly report is generated.

### Affected files

- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/proactive_notify_skill.py` new
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py` call after vector update
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/report_skill.py` optional call or skip if circular risk
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/__init__.py` register skill
- Existing notification frontend can remain unchanged

## Data flow paths

### Feedback learning

```text
WeeklyReport feedback button
  -> POST /api/report/feedback
  -> memory episode saved
  -> feedback_learning_skill updates learning signal / vector lightly
  -> response includes learning summary
```

### Food autobiography

```text
TasteProfile page
  -> GET /api/profile/timeline
  -> memory_timeline_skill analyzes meals
  -> timeline chapters rendered
```

### Next meal decision

```text
Home page
  -> GET /api/recommend/today
  -> next_meal_skill
  -> health_skill + mood_food_skill + user vector
  -> richer recommendation groups
```

### Companion plan

```text
Match detail page
  -> GET /api/match/{id}
  -> meal_companion_skill
  -> shared foods + invite text + avoid notes
```

### City real aggregation

```text
City page
  -> GET /api/city/live-summary
  -> city_aggregation_skill
  -> real meals aggregate or mock fallback
```

### Restaurant match

```text
City recommend page
  -> city/recommend or recommend endpoint
  -> restaurant_match_skill
  -> scored recommendation cards
```

### Proactive notification

```text
Meal upload
  -> vector update
  -> proactive_notify_skill
  -> notifications table
  -> frontend SSE/list shows insight
```

## Boundary conditions and exception handling

- All new skills must return stable empty states when no meals exist.
- Do not add external APIs.
- Do not change auth/session security model in this iteration.
- Avoid circular imports between skills.
- Keep LLM calls out of new deterministic skills unless existing code already calls LLM.
- Keep existing APIs backward-compatible.
- Do not break demo users.
- If mock restaurant/city data shape varies, parse defensively.
- Use minimal UI changes that add value without redesigning the whole app again.

## Expected outcomes

After implementation, the project should better satisfy the requirement document:

1. “看不见自己” improves through health/mood/timeline/feedback learning.
2. “找不到同类” improves through meal companion plan and invite text.
3. “读不懂城市” improves through real meal aggregation and richer restaurant matching.
4. Agent experience improves through proactive notifications and reusable skills.
5. The app feels less like static demo pages and more like a system that learns, explains, recommends, connects, and nudges.
