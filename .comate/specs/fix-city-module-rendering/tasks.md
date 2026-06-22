# 城市模块点击 Bug 与渲染一致性修复任务

- [x] Task 1: 修复城市地图点击与热力图渲染兜底
    - 1.1: 在 `CityMap.tsx` 中构建安全区县数据数组，过滤缺失 center 或 value 异常的数据
    - 1.2: 使用复制数组排序，避免 `sort` 原地修改 state 数据
    - 1.3: 为 ECharts tooltip、symbolSize 和点位数据增加数字兜底
    - 1.4: 将趋势分析和个性化推荐入口改为携带当前 city query
    - 1.5: 为无区县数据场景增加当前主题下的空状态展示

- [x] Task 2: 新增城市区县详情页并注册路由
    - 2.1: 新增 `frontend/src/pages/CityDistrict.tsx`
    - 2.2: 在页面中读取 `:id` 参数并请求 `/city/district/{id}`
    - 2.3: 展示区县名称、餐食数量、口味维度、热门菜系和餐厅列表
    - 2.4: 使用一食万象 banner 对齐主题完成页面渲染
    - 2.5: 在 `App.tsx` 注册 `/city/district/:id` 路由

- [x] Task 3: 修复城市趋势页的城市参数与空状态
    - 3.1: 在 `CityTrends.tsx` 中通过 `useSearchParams` 读取 city
    - 3.2: 请求 `/city/trends` 时携带 city 和 dimension
    - 3.3: 使用安全 trends 数组生成图表配置
    - 3.4: 趋势为空时展示明确空状态，不渲染空图
    - 3.5: 保持页面视觉与当前主题一致

- [x] Task 4: 修复城市推荐页的城市参数传递
    - 4.1: 在 `CityRecommend.tsx` 中通过 `useSearchParams` 读取 city
    - 4.2: 请求 `/city/recommend` 和 `/city/live-summary` 时携带 city
    - 4.3: 在页面标题或城市实时信号中体现当前城市上下文
    - 4.4: 为无餐厅和无趋势推荐场景增加主题一致的空状态

- [x] Task 5: 修复后端城市趋势和推荐过滤逻辑
    - 5.1: 在 `routers/city.py` 的 `/trends` 洞察调用中传递当前 city
    - 5.2: 在 `routers/city.py` 的 `/recommend` 趋势推荐调用中传递当前 city
    - 5.3: 更新 `recommend_skill.py` 的 trends action，使其支持 city 参数
    - 5.4: 在 `_recommend_restaurants` 中按 city 过滤餐厅，并保留无数据回退
    - 5.5: 在 `_recommend_trends` 中仅遍历当前 city，并返回 city/city_name 信息

- [x] Task 6: 验证城市模块接口、构建和主题残留
    - 6.1: 运行前端构建，确保 TypeScript 和 Vite 构建通过
    - 6.2: 验证后端城市接口在当前服务上可正常返回
    - 6.3: 检查城市页面源码中是否仍存在明显旧主题硬编码
    - 6.4: 检查城市地图、区县详情、趋势页、推荐页的参数链路是否一致
    - 6.5: 记录修复结果到 summary.md
