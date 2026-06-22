# 扩展并净化味觉匹配发现

## 需求场景与处理逻辑

用户在“味觉发现/推荐匹配”页面看到的候选用户过少，并且出现了“测试用户”“冒烟测试用户”等内部验证账号名称，导致产品体验像测试环境而不是一个真实社交应用。

本次改动聚焦于匹配发现链路：

1. 扩大推荐候选数量：从当前前后端多处固定 5 个候选，提升到默认 20 个候选，并允许接口按 `limit` 参数控制数量。
2. 净化匹配池：过滤掉内部测试/冒烟/验证账号，避免这些账号出现在发现列表和已有匹配列表中。
3. 保持现有匹配计算逻辑：继续使用味觉向量余弦相似度、口味维度、菜系维度、时间维度进行排序，不引入新的复杂推荐系统。
4. 保持响应性能：发现列表不再依赖逐个 LLM 解释，改为使用确定性匹配解释，避免候选变多后接口变慢。
5. 不修改登录注册链路，不修改 `backend/config.py` 中现有 API Key 配置。

## 架构与技术方案

### 后端匹配接口

当前链路：

- 前端 `SocialDiscover.tsx` 请求 `/match/discover?limit=5`
- 后端 `backend/routers/match.py:12` 的 `discover_matches` 默认 `limit=5`
- 后端 `backend/skills/match_skill.py:22` 的 `_discover_matches` 最后固定返回 `results[:5]`

改造后：

- 前端请求 `/match/discover?limit=20`
- 路由默认 `limit=20`，并设置安全上限，例如最多 50
- `match_skill` 接收 `limit` 参数，并由技能内部统一截断
- 技能内部过滤测试账号，再按分数排序
- 路由返回的前若干候选使用本地确定性解释文本，不逐个调用 LLM

### 测试账号过滤策略

新增一个轻量过滤函数，避免测试数据污染用户可见体验：

```py
def _is_internal_test_user(user_id: str, name: str) -> bool:
    text = f"{user_id} {name}".lower()
    blocked_keywords = ["测试", "冒烟", "test", "smoke", "validation"]
    return any(keyword in text for keyword in blocked_keywords)
```

过滤位置：

1. `match_skill._discover_matches`：过滤发现候选。
2. `routers/match.py` 的 `/match/list`：过滤已经存在的 pending/mutual 列表中测试账号。

说明：

- 该过滤只影响用户可见推荐/匹配展示，不删除用户真实注册数据。
- 如果后续需要物理清理数据库测试账号，可单独做数据维护；本次优先避免可见污染。

### 匹配解释性能优化

当前 `/match/discover` 会对前 3 个候选调用：

```py
exp = await match_skill(user_id, {"action": "explain", "other_user_id": m["user"]["id"]})
```

而 `match_skill` 的 explain 使用 LLM。候选数量变多后，如果继续同步调用 LLM，会拖慢发现页。改造为确定性解释：

```py
def _build_match_explanation(match: dict) -> str:
    common = match.get("common", [])
    taste_text = "、".join(common[:3]) if common else "基础口味"
    score = round(match.get("score", 0) * 100)
    return f"你们在{taste_text}上有相似信号，综合匹配度约 {score}%，适合从低压力约饭开始。"
```

## 受影响文件

### 后端

#### `/Users/libowen/Desktop/one-bite-one-world/backend/skills/match_skill.py`

修改类型：更新匹配发现技能。

受影响函数：

- `match_skill`
- `_discover_matches`
- 新增 `_is_internal_test_user`
- 可选新增 `_safe_json_loads`

预期修改：

```py
async def match_skill(user_id: str, params: dict) -> dict:
    action = params.get("action", "discover")
    if action == "discover":
        limit = int(params.get("limit", 20))
        return await _discover_matches(user_id, limit)
```

```py
async def _discover_matches(user_id: str, limit: int = 20) -> dict:
    limit = max(1, min(limit, 50))
    ...
    for other in others:
        if other[7] == "private":
            continue
        if _is_internal_test_user(other[0], other[1]):
            continue
        ...
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"matches": results[:limit]}
```

边界处理：

- `limit` 非法时使用默认值 20。
- `tags` 或 `taste_vector` 异常时跳过该候选，避免接口整体 500。
- `privacy_level == "private"` 继续不展示。

#### `/Users/libowen/Desktop/one-bite-one-world/backend/routers/match.py`

修改类型：更新匹配发现接口和匹配列表展示过滤。

受影响函数：

- `discover_matches`
- `match_list`
- 新增 `_bounded_limit`
- 新增 `_build_match_explanation`
- 新增 `_is_internal_test_user`（或从 skill 复用）

预期修改：

```py
@router.get("/discover")
async def discover_matches(request: Request, limit: int = 20):
    user_id = request.state.user_id
    bounded_limit = max(1, min(limit, 50))
    result = await match_skill(user_id, {"action": "discover", "limit": bounded_limit})
    matches = result.get("matches", [])

    for m in matches[:6]:
        m["explanation"] = _build_match_explanation(m)

    return {"success": True, "data": matches}
```

`match_list` 中对其他用户执行同样过滤，防止历史测试用户出现在“我的匹配”。

### 前端

#### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/SocialDiscover.tsx`

修改类型：扩大请求数量并优化空态文案。

当前：

```tsx
api.get('/match/discover?limit=5')
```

改为：

```tsx
api.get('/match/discover?limit=20')
```

同时将进度展示继续保留为 `{currentIdx + 1} / {matches.length}`，用户能明显看到候选数量增加。

## 数据流路径

1. 用户进入味觉发现页。
2. `SocialDiscover.tsx` 请求 `/api/match/discover?limit=20`。
3. `routers/match.py` 限制 `limit` 在 1 到 50 之间。
4. `match_skill.py` 读取当前用户 taste vector。
5. 读取其他用户，过滤：
   - 当前用户自己
   - `privacy_level == "private"`
   - 测试/冒烟/validation 用户
   - 向量或标签异常用户
6. 计算 cosine similarity 与维度分数。
7. 按匹配分排序，返回前 20 个。
8. 路由为前几个候选生成本地解释。
9. 前端按卡片流展示更多候选。

## 边界条件与异常处理

- 如果数据库用户不足 20 个，则返回实际可用数量。
- 如果过滤后为空，前端仍显示“今日推荐已看完”，不报错。
- 如果 `limit` 传入超过 50，则按 50 处理，避免过大请求影响性能。
- 如果某个候选用户的 `taste_vector` 或 `tags` 数据损坏，只跳过该候选。
- 不删除数据库记录，避免误删真实用户。

## 预期结果

1. 味觉发现页候选数量从最多 5 个提升到最多 20 个。
2. `/api/match/discover?limit=20` 返回结果中不再出现：
   - `测试用户`
   - `冒烟测试用户`
   - 其他包含 `test/smoke/validation` 的内部验证账号
3. “我的匹配”列表也不会展示测试账号。
4. 匹配发现接口不再因为 LLM 解释而变慢。
5. 前端构建通过。

## 验证方式

- 后端接口验证：
  - 请求 `/api/match/discover?limit=20`
  - 确认返回数量大于 5（如果数据库候选足够）
  - 确认返回用户名称不包含测试关键词
- 前端验证：
  - 打开味觉发现页，确认进度显示为更多候选，例如 `1 / 20`
- 构建验证：
  - 在 `frontend` 目录执行 `npm run build`
