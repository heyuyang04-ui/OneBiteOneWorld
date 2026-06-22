# Productize Daily Food Hub

## Requirement scenario and processing logic

The current app can demonstrate the concept of “一食万象”, but the first-session experience still feels like a feature demo: the home page mainly asks the user to upload food, and the meal result page depends on route state. This iteration will make the app feel closer to a real consumer product by turning the home page into a daily food decision hub, adding a personalized “今天吃什么” recommendation API, and ensuring meal result pages remain usable after refresh or direct navigation.

Target user path:

1. User logs in as Bowen or another user.
2. Home page greets the current user and shows a daily taste state rather than only a static upload banner.
3. Home page shows actionable recommendations:
   - “贴合偏好”: directly satisfies current taste profile.
   - “平衡建议”: keeps satisfaction while reducing taste fatigue.
   - “探索建议”: city/local-flavor discovery.
4. User can still upload a meal photo from the home page.
5. After upload, the app navigates to `/meal/:id`.
6. If the result page is refreshed or opened directly, it loads meal details from `GET /api/meals/{meal_id}` instead of showing “暂无数据”.
7. Meal result explains how the meal affects the user’s taste profile and gives next-meal suggestions.

## Architecture and technical approach

### Frontend

The implementation will keep the current React + TypeScript + Vite structure and avoid introducing new dependencies.

`Home.tsx` will become a richer food hub:

- Fetch `/api/users/me` or current-user-related data if available, otherwise derive display name from local storage / fallback mapping.
- Fetch `GET /api/recommend/today`.
- Fetch notifications as before.
- Render:
  - personalized hero section;
  - daily taste state card;
  - “今天吃什么” recommendation cards;
  - quick intent chips;
  - existing `ImageUpload` as “记录这一餐”;
  - notification preview.

`MealResult.tsx` will no longer rely only on router state:

- Read `id` from route params.
- If `location.state` contains uploaded result data, use it immediately.
- Otherwise call `GET /api/meals/{id}`.
- Render loading and not-found states.
- Add practical sections:
  - “这餐如何影响你的口味画像”;
  - “下一餐建议”;
  - optional preserved micro insight if available from upload state.

### Backend

Add a recommendation endpoint without adding a new router file unless necessary. The smallest change is to expose it through an existing router module or create `routers/recommend.py` if cleaner. Since the app already has recommendation skills and city recommendation pages, creating a small dedicated router is acceptable if it keeps route ownership clear.

Proposed endpoint:

```http
GET /api/recommend/today
```

Response shape:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_bowen",
      "name": "Bowen",
      "city": "beijing",
      "occupation": "程序员"
    },
    "state": {
      "title": "肉食满足型",
      "summary": "今天更适合高蛋白、咸鲜、满足感强的晚餐选择。",
      "signals": ["肉食偏好高", "咸鲜偏好高", "晚餐满足感强"]
    },
    "recommendations": [
      {
        "type": "preference",
        "title": "贴合偏好",
        "items": [
          {
            "name": "炙子烤肉",
            "reason": "符合你的肉食、咸鲜和北京本地风味偏好。",
            "tags": ["肉食", "咸鲜", "北京"]
          }
        ]
      },
      {
        "type": "balance",
        "title": "平衡建议",
        "items": []
      },
      {
        "type": "explore",
        "title": "探索建议",
        "items": []
      }
    ],
    "quick_actions": ["想吃肉", "想吃清淡", "想探索新店", "想找饭搭子"]
  }
}
```

The backend recommendation logic should use existing user fields and taste vector:

- first 6 vector dimensions: spicy, sweet, sour, salty, umami, bitter;
- city and occupation from `users` table;
- for meat-loving users like Bowen, high umami/salty and city=beijing should produce meat-focused recommendations;
- for non-Bowen users, generate generic recommendations from taste vector thresholds.

This should be deterministic and fast. Do not call LLM for this endpoint to keep home page responsive and reliable.

## Affected files

### Frontend modifications

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.tsx`
  - Modification type: replace simple upload-first layout with daily food hub.
  - Affected functions: `Home` component, `useEffect`, `handleUpload`.
  - Add state for recommendation payload and load failure.

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/Home.css`
  - Modification type: extend styles for food hub cards, recommendation sections, quick action chips, personalized hero.

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.tsx`
  - Modification type: support route-param fetch fallback and richer result explanation.
  - Affected functions: `MealResult` component.
  - Add `useParams`, `useEffect`, local loading/error state.

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/MealResult.css`
  - Modification type: extend styles for loading/error state, impact section, next-meal suggestion cards.

### Backend modifications

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/recommend.py`
  - Modification type: new router if no existing recommendation router exists.
  - Affected functions: add `get_today_recommendation` and small internal helper functions.

- `/Users/libowen/Desktop/one-bite-one-world/backend/main.py`
  - Modification type: import and register recommendation router.
  - Affected functions/lines: router imports and `app.include_router` block.

- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/meals.py`
  - Modification type: tighten existing `GET /api/meals/{meal_id}` to respect current user ownership.
  - Affected function: `get_meal`.
  - Reason: direct result-page loading should not expose another user’s meal by ID.

## Implementation details

### `GET /api/recommend/today`

Pseudo implementation:

```py
@router.get("/today")
async def today_recommendation(request: Request):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute(
        "SELECT id, name, city, occupation, taste_vector FROM users WHERE id=?",
        (user_id,)
    )
    user = await cursor.fetchone()
    await db.close()

    if not user:
        return {"success": False, "error": {"message": "user not found"}}

    vector = json.loads(user["taste_vector"] or "[]")
    taste = {
        "spicy": vector[0] if len(vector) > 0 else 0,
        "sweet": vector[1] if len(vector) > 1 else 0,
        "sour": vector[2] if len(vector) > 2 else 0,
        "salty": vector[3] if len(vector) > 3 else 0,
        "umami": vector[4] if len(vector) > 4 else 0,
        "bitter": vector[5] if len(vector) > 5 else 0,
    }

    # build state + three recommendation groups from thresholds
    return {"success": True, "data": payload}
```

Recommendation mapping examples:

- High `umami` + high `salty`: recommend meat, grilled fish, beef rice, stewed beef.
- High `spicy`: recommend hot pot / spicy dishes, with balance options.
- High `sweet`: recommend light sweet/sour and cafe-style recommendations.
- City `beijing`: include Beijing-style options such as 炙子烤肉, 铜锅涮肉.

### Home page rendering

The home page should avoid feeling like a static marketing page. It should render concrete choices:

```tsx
<section className="today-hub">
  <p className="eyebrow">今日饮食状态</p>
  <h2>{userName}，今天适合这样吃</h2>
  <p>{recommendation.state.summary}</p>
</section>

<section className="recommend-section">
  {recommendation.recommendations.map(group => (
    <div className="recommend-group" key={group.type}>
      <h3>{group.title}</h3>
      {group.items.map(item => <RecommendationCard item={item} />)}
    </div>
  ))}
</section>
```

### Meal result fallback fetch

```tsx
const { id } = useParams()
const { state } = useLocation() as { state: any }
const [meal, setMeal] = useState(state?.meal || null)

useEffect(() => {
  if (meal || !id) return
  api.get(`/meals/${id}`).then(res => {
    if (res.data.success) setMeal(res.data.data)
  })
}, [id, meal])
```

## Boundary conditions and exception handling

- If `/api/recommend/today` fails, the home page should still allow upload and show a lightweight fallback state.
- If the current user is missing, the backend should return a structured failure instead of throwing.
- If `taste_vector` is missing or malformed, use default neutral values.
- If `/meal/:id` is opened directly and the meal does not exist, show “未找到这餐记录” with a button back to home or history.
- If `location.state` includes micro insight, preserve it; when loading from API later, do not invent a fake insight.
- `GET /api/meals/{meal_id}` should check `request.state.user_id` and only return the current user’s meal.
- Do not introduce login/auth redesign in this iteration; it is outside this focused change.
- Do not remove the API key fallback because the user explicitly requested not to modify it earlier.

## Data flow paths

### Home page recommendation flow

```text
Browser Home.tsx
  -> api.get('/recommend/today')
  -> FastAPI /api/recommend/today
  -> SQLite users table
  -> taste vector threshold mapping
  -> response
  -> Home renders daily state + recommendation groups
```

### Meal upload and result flow

```text
Home.tsx ImageUpload
  -> POST /api/meals
  -> vision_skill recognition
  -> SQLite meals insert
  -> vector_skill recompute
  -> orchestrator micro insight
  -> navigate('/meal/:id', { state })
  -> MealResult renders immediate state
```

### Direct result refresh flow

```text
Browser reloads /meal/:id
  -> MealResult has no route state
  -> api.get('/meals/:id')
  -> FastAPI checks meal_id + current user
  -> SQLite meals row
  -> MealResult renders stored detail
```

## Expected outcomes

- The first screen feels like a real food decision product rather than an upload-only demo.
- Users get immediate value before uploading: daily state and recommended food choices.
- Bowen’s character feels more real because the home page reflects meat-loving programmer behavior in Beijing.
- Meal result pages survive refresh and direct navigation.
- The app has a clearer daily-use loop: decide what to eat → record meal → understand impact → get next suggestion.
- The change remains small enough for the existing codebase and does not require new external services.
