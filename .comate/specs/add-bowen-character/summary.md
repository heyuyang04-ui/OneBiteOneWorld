# Add Bowen Character — Summary

## Completed Tasks

### Task 1: Update Login.tsx HERO_USERS entry for Bowen
- **File**: `frontend/src/pages/Login.tsx:7`
- Changed emoji: ⚡ → 🥩
- Changed description: `"用代码改变世界，用美食犒劳自己"` → `"无肉不欢的代码诗人，用烤肉香气犒劳每一个加班夜"`

### Task 2: Insert Bowen user entry in mock_users.json
- **File**: `backend/data/mock_users.json`
- Inserted Bowen object at index 1 (right after user_01 阿杰)
- Taste vector designed for meat lover profile:
  - High umami (0.85), high salty (0.7), moderate spicy (0.45)
  - Cuisine preferences favor 西餐/steak (0.7), 韩餐/BBQ (0.6), 鲁菜 (0.55)
  - Late-night eating pattern (dinner 0.7, late night 0.6) fitting programmer lifestyle
- Tags: `["品质探店型", "肉食爱好者"]`
- Privacy: `match_only`

### Task 3: Delete demo.db
- **File**: `backend/demo.db` — deleted
- On next backend startup, `init_db()` will re-import all 501 users (original 500 + Bowen) from mock_users.json

## Verification

- Login.tsx: Bowen appears as the second hero card with meat emoji and updated description
- mock_users.json: Bowen entry verified at index 1 with correct attributes
- demo.db: Successfully removed, will be regenerated on next startup
