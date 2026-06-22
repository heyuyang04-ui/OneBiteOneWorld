# 城市模块点击 Bug 与渲染一致性修复说明

## 背景
用户反馈“点城市的那部分会出现 bug”，并要求继续检查渲染。经现有代码和城市模块链路分析，城市相关问题集中在：

1. 城市地图区县卡片点击到不存在的前端路由。
2. 在城市地图中切换城市后，趋势页和推荐页没有携带当前城市，导致页面内容仍默认北京。
3. 后端城市推荐中的部分推荐逻辑没有按 city 过滤，可能出现跨城推荐。
4. 城市热力图和趋势图对数据结构缺少渲染兜底，数据异常时可能出现空图、NaN 或运行时错误。
5. 部分城市页面渲染仍可继续统一为当前 banner 对齐主题，避免城市卡片、图表容器和空状态不一致。

## 需求场景与处理逻辑

### 场景 1：用户在城市地图点击区县卡片
当前问题：
- `CityMap.tsx` 中区县卡片链接到 `/city/district/${r.id}`。
- `App.tsx` 没有注册 `/city/district/:id` 路由。
- 用户点击后会命中 `*` 路由并跳回 `/home`，表现为点击城市部分异常或闪退。

处理逻辑：
- 新增前端城市区县详情页组件 `CityDistrict.tsx`。
- 在 `App.tsx` 注册 `/city/district/:id`。
- 页面请求后端已有接口 `/api/city/district/{district_id}`。
- 展示区县名称、餐食数量、口味维度、热门菜系、餐厅列表。
- 使用当前“夜色城市 + 琥珀灯光 + 暖瓷卡片”的主题。

### 场景 2：用户切换城市后点击趋势分析
当前问题：
- `CityMap.tsx` 内有 `city` state，但链接到 `/city/trends` 时没有传递城市。
- `CityTrends.tsx` 请求 `/city/trends?dimension=...`，没有 `city` 参数。
- 后端默认 `city=beijing`，导致用户切到上海/成都后趋势仍是北京。

处理逻辑：
- `CityMap.tsx` 的趋势入口改为 `/city/trends?city=${city}`。
- `CityTrends.tsx` 使用 `useSearchParams` 读取 city。
- 请求改为 `/city/trends?city=${city}&dimension=${dimension}`。
- 页面标题或副标题展示当前城市。
- 后端 `/city/trends` 调用 `trend_skill` 获取洞察时传入当前 `city`，避免洞察和图表城市不一致。

### 场景 3：用户切换城市后点击个性化推荐
当前问题：
- `CityMap.tsx` 链接到 `/city/recommend`，没有传递当前城市。
- `CityRecommend.tsx` 请求 `/city/recommend` 和 `/city/live-summary`，没有 city 参数。
- 后端默认北京，导致推荐和摘要串城。

处理逻辑：
- `CityMap.tsx` 推荐入口改为 `/city/recommend?city=${city}`。
- `CityRecommend.tsx` 使用 `useSearchParams` 读取 city。
- 请求改为：
  - `/city/recommend?city=${city}`
  - `/city/live-summary?city=${city}`
- 页面展示当前城市上下文。

### 场景 4：推荐餐厅和趋势推荐需要按城市过滤
当前问题：
- `recommend_skill._recommend_restaurants(user_id, city)` 接收 city 但没有实际过滤餐厅。
- `recommend_skill._recommend_trends(user_id)` 遍历所有城市，不符合当前城市上下文。
- `routers/city.py` 调用 `recommend_skill(user_id, {"action": "trends"})` 时也没有传 city。

处理逻辑：
- 更新 `recommend_skill`：
  - `action == "trends"` 时传递 `city`。
  - `_recommend_restaurants` 按餐厅 `city` 过滤；若该城市没有餐厅，再降级使用全量，避免空结果。
  - `_recommend_trends` 支持 `city` 参数，只遍历当前城市。
  - 返回趋势时补充 city/city_name 字段，前端展示更明确。
- 更新 `routers/city.py`：
  - `/recommend` 调用趋势推荐时传入当前 city。

### 场景 5：城市热力图和趋势图渲染兜底
当前问题：
- `CityMap.tsx` 中直接访问 `r.center[0]`、`r.center[1]`，如果后端数据缺 center 会抛错。
- `data.regions.sort(...)` 直接原地修改 state 数据，可能导致渲染不稳定。
- `CityTrends.tsx` 在空趋势时会显示空图，没有明确空状态。

处理逻辑：
- `CityMap.tsx`：
  - 使用 `safeRegions` 过滤 center/value 不完整的数据。
  - 使用 `[...safeRegions].sort(...)`，不原地修改 state。
  - tooltip/symbolSize 对 value 做数字兜底。
  - 无区县数据时展示空状态。
- `CityTrends.tsx`：
  - 使用 `trends` 安全数组。
  - 空数据时展示“当前城市暂无趋势数据”。
  - loading 和错误文案使用当前主题色。

## 架构与技术方案

### 前端修改

#### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx`
修改类型：新增路由。

新增：
```tsx
import CityDistrict from './pages/CityDistrict'
...
<Route path="/city/district/:id" element={<CityDistrict />} />
```

#### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx`
修改类型：城市选择、链接、渲染兜底。

关键修改：
- 使用安全区域数组：
```tsx
const safeRegions = (data?.regions || []).filter((r: any) =>
  Array.isArray(r.center) && r.center.length >= 2 && Number.isFinite(Number(r.value))
)
const sortedRegions = [...safeRegions].sort((a, b) => Number(b.value) - Number(a.value))
```
- 趋势/推荐链接携带城市：
```tsx
<Link to={`/city/trends?city=${city}`}>趋势分析</Link>
<Link to={`/city/recommend?city=${city}`}>个性化推荐</Link>
```

#### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityTrends.tsx`
修改类型：读取 query city、请求当前城市、空状态和渲染兜底。

关键修改：
```tsx
const [searchParams] = useSearchParams()
const city = searchParams.get('city') || 'beijing'
api.get(`/city/trends?city=${city}&dimension=${dimension}`)
```

#### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityRecommend.tsx`
修改类型：读取 query city、请求当前城市。

关键修改：
```tsx
const [searchParams] = useSearchParams()
const city = searchParams.get('city') || 'beijing'
api.get(`/city/recommend?city=${city}`)
api.get(`/city/live-summary?city=${city}`)
```

#### `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityDistrict.tsx`
修改类型：新增页面，补齐已有后端接口的前端展示。

展示内容：
- 区县名称
- 餐食数量
- 口味维度百分比
- 热门菜系标签
- 餐厅列表
- 返回城市地图入口

### 后端修改

#### `/Users/libowen/Desktop/one-bite-one-world/backend/routers/city.py`
修改类型：传递 city 参数。

- `/trends` 调用 `trend_skill` 时传 city：
```py
insight_result = await trend_skill(request.state.user_id, {"action": "insight", "city": city})
```
- `/recommend` 调用趋势推荐时传 city：
```py
trends = await recommend_skill(user_id, {"action": "trends", "city": city})
```

#### `/Users/libowen/Desktop/one-bite-one-world/backend/skills/recommend_skill.py`
修改类型：城市过滤与兜底。

- `recommend_skill` 的 `trends` action 传递 city。
- `_recommend_restaurants` 按 city 过滤；若过滤为空则回退全量。
- `_recommend_trends` 接收 city，仅使用当前城市数据。

## 受影响文件

### 必改文件
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityTrends.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityRecommend.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/backend/routers/city.py`
- `/Users/libowen/Desktop/one-bite-one-world/backend/skills/recommend_skill.py`

### 新增必要文件
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityDistrict.tsx`

新增该文件是必要的，因为后端已有 `/api/city/district/{district_id}` 接口，但前端缺少对应路由页面，当前点击区县会导航异常。

## 边界条件与异常处理

- 如果 city query 缺失，默认 `beijing`，保持现有行为。
- 如果城市没有趋势/区县数据，展示空状态，不渲染空图或崩溃。
- 如果餐厅数据没有当前城市，后端回退全量推荐，避免推荐区空白。
- 如果区县接口返回失败，前端展示“未找到区县信息”。
- 不修改登录、匹配、上传、周报等非城市模块逻辑。
- 不修改硬编码 API key 配置。
- 不改变 Bowen 用户。

## 数据流路径

### 城市地图
`CityMap.tsx` → `/api/city/cities` → city buttons → `/api/city/heatmap?city=&dimension=` → heatmap + district list

### 区县详情
`CityMap.tsx` → `/city/district/:id` → `CityDistrict.tsx` → `/api/city/district/{district_id}` → district detail

### 趋势分析
`CityMap.tsx` → `/city/trends?city={city}` → `CityTrends.tsx` → `/api/city/trends?city={city}&dimension={dimension}`

### 个性化推荐
`CityMap.tsx` → `/city/recommend?city={city}` → `CityRecommend.tsx` → `/api/city/recommend?city={city}` + `/api/city/live-summary?city={city}`

## 预期结果

- 点击城市区县卡片不再跳回首页或异常，而是进入区县详情页。
- 切换城市后进入趋势页和推荐页时，展示当前城市的数据。
- 后端推荐餐厅和趋势推荐与当前城市上下文一致。
- 城市热力图、趋势图对异常/空数据有兜底，不再出现空图、NaN 或运行时错误。
- 城市相关页面继续保持当前 banner 对齐主题风格。
- 前端构建通过。
