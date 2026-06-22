# 城市模块点击 Bug 与渲染一致性修复总结

## 修复内容

本次修复了城市模块点击异常、城市上下文丢失、推荐串城和城市页面渲染兜底问题。

## 已完成任务

### 1. 城市地图点击与热力图渲染兜底
修改文件：
- `frontend/src/pages/CityMap.tsx`

完成内容：
- 增加 `safeRegions`，过滤缺失 `center` 或 `value` 异常的数据。
- 使用 `[...safeRegions].sort(...)` 排序，避免直接修改 state 中的 `data.regions`。
- ECharts tooltip、symbolSize、点位坐标增加数字兜底。
- 无区县数据时展示主题一致的空状态。
- 趋势分析入口改为 `/city/trends?city=${city}`。
- 个性化推荐入口改为 `/city/recommend?city=${city}`。

### 2. 新增城市区县详情页并注册路由
修改文件：
- `frontend/src/pages/CityDistrict.tsx`
- `frontend/src/App.tsx`

完成内容：
- 新增 `/city/district/:id` 前端页面。
- 接入后端已有接口 `/api/city/district/{district_id}`。
- 展示区县名称、餐食数量、口味维度、热门菜系和餐厅列表。
- 点击城市区县卡片不再跳回首页。

### 3. 城市趋势页城市参数与空状态
修改文件：
- `frontend/src/pages/CityTrends.tsx`

完成内容：
- 通过 `useSearchParams` 读取 city。
- 请求 `/city/trends?city={city}&dimension={dimension}`。
- 使用安全 trends 数组生成图表配置。
- 当前城市无趋势时展示空状态，不渲染空图。
- 页面展示当前城市和维度上下文。

### 4. 城市推荐页城市参数传递
修改文件：
- `frontend/src/pages/CityRecommend.tsx`

完成内容：
- 通过 `useSearchParams` 读取 city。
- 请求 `/city/recommend?city={city}` 和 `/city/live-summary?city={city}`。
- 页面标题和实时信号展示当前城市上下文。
- 无餐厅推荐、无趋势推荐时展示主题一致的空状态。

### 5. 后端城市趋势和推荐过滤逻辑
修改文件：
- `backend/routers/city.py`
- `backend/skills/recommend_skill.py`

完成内容：
- `/api/city/trends` 调用趋势洞察时传递当前 city。
- `/api/city/recommend` 调用趋势推荐时传递当前 city。
- `recommend_skill` 的 trends action 支持 city 参数。
- `_recommend_restaurants` 按 city 过滤餐厅，并保留无数据回退。
- `_recommend_trends` 仅遍历当前 city，并返回 `city`、`city_name` 字段。

## 验证结果

### 前端构建
已运行：

```bash
npm run build
```

结果：成功。

```text
✓ 1117 modules transformed.
✓ built in 365ms
```

Vite 仍提示 bundle 大小超过 500kB，这是打包体积提示，不影响本次修复。

### 后端语法检查
已运行：

```bash
python -m py_compile routers/city.py skills/recommend_skill.py
```

结果：成功，无语法错误。

### 城市接口 smoke test
当前 8000 端口已有后端实例运行，验证接口：

- `/api/city/cities`：200，成功返回城市列表。
- `/api/city/heatmap?city=shanghai&dimension=spicy`：200，返回 city/city_name/dimension/regions。
- `/api/city/trends?city=shanghai&dimension=sweet`：200，返回 city/city_name/dimension/trends/insights。
- `/api/city/recommend?city=shanghai`：200，返回 restaurants/matched_restaurants/trends/cross。

### 主题残留检查
已检查城市相关页面的旧紫色/旧主题硬编码：未检出。

## 修复后的用户体验

- 在城市地图点击区县卡片，会进入区县详情页，不再跳回首页。
- 切换城市后进入趋势分析，会使用当前城市数据。
- 切换城市后进入个性化推荐，会使用当前城市摘要和推荐。
- 城市热力图和趋势图在异常/空数据下不会崩溃或显示空白图。
- 城市模块视觉继续保持一食万象 banner 对齐主题。
