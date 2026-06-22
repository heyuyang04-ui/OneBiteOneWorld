# Add Bowen Character

## Requirement

Add a new demo character "Bowen" to the "一食万象" project:
- **Name**: Bowen
- **Age**: 25
- **Occupation**: 程序员 (Programmer)
- **City**: Beijing
- **Food Preference**: 爱好各种肉食 (loves all kinds of meat)
- **Character ID**: `user_bowen`

## Scope

Three files need modification:
1. `frontend/src/pages/Login.tsx` — Update HERO_USERS entry for Bowen
2. `backend/data/mock_users.json` — Insert Bowen user entry
3. `backend/demo.db` — Delete so the database reinitializes with the new user on next startup

## Architecture & Technical Approach

### 1. Frontend — Login.tsx (HERO_USERS update)

Bowen already has a placeholder entry at index 1 in HERO_USERS. Need to update:
- Age display in subtitle: keep `'程序员 · 北京'` (no age shown in subtitle, consistent with other entries)
- Description: Change to reflect meat-loving personality
- Emoji: Change to a meat/food emoji more fitting than ⚡

### 2. Backend — mock_users.json

Insert a new user entry with `id: "user_bowen"` right after `user_01` (index 1 of the array).

#### Taste Vector Design (32-dimensional, 0-1 normalized)

Bowen is a meat lover. Key taste characteristics:
- **High umami** (index 4): Meat is rich in umami → `0.85`
- **High salty** (index 3): Meat dishes are savory/salty → `0.7`
- **Moderate spicy** (index 0): Beijing-style moderate spice → `0.45`
- **Low sweet** (index 1): Not a dessert person → `0.1`
- **Low-moderate sour** (index 2): → `0.15`
- **Moderate bitter** (index 5): Coffee/beer with meals → `0.3`

Cuisine preferences [6:14]:
- 川菜 (index 6): Sichuan meat dishes → `0.5`
- 粤菜 (index 7): Cantonese roast meats → `0.4`
- 湘菜 (index 8): Hunan spicy meats → `0.35`
- 鲁菜 (index 9): Northern/Beijing style → `0.55`
- 日料 (index 10): Yakiniku → `0.3`
- 韩餐 (index 11): Korean BBQ → `0.6`
- 西餐 (index 12): Steaks → `0.7`
- 东南亚 (index 13): Satay → `0.2`

Lifestyle/behavioral dimensions [14:28] (modeled as a young programmer):
- Late-night eating tendency
- Weekend feast tendency
- Quick-meal tendency (programmer stereotype)

Temporal [28:32]:
- dinner (index 30): → `0.7`
- late night (index 31): → `0.6`
- lunch (index 29): → `0.5`
- breakfast (index 28): → `0.1` (programmer sleep pattern)

#### Attributes
- `tags`: `["品质探店型", "肉食爱好者"]`
- `privacy_level`: `"match_only"`

### 3. Database Reset

Delete `demo.db` so `init_db()` re-imports all users from `mock_users.json` on next startup, picking up Bowen.

## Data Flow

1. Backend starts → `init_db()` → reads `mock_users.json` → inserts all users (including Bowen) → SQLite `users` table
2. Frontend Login.tsx → user selects Bowen → `handleLogin()` → `PUT /users/me/switch {user_id: "user_bowen"}` → SESSION maps session → user_id
3. Subsequent API calls carry `X-Session-Id` header → `user_middleware` resolves to `user_bowen`
4. Taste vector is used by match_skill, recommend_skill, vector_skill for similarity computation

## Boundary Conditions

- If `demo.db` does not exist, startup will simply create a fresh one — no error
- If Bowen entry already exists in mock_users.json from a previous edit, ensure the edit is idempotent (replace existing)
- Login.tsx HERO_USERS already has a `user_bowen` entry — this is an update, not an insertion
