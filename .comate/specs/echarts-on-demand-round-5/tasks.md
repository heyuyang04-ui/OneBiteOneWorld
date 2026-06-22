# 第五轮 ECharts 按需注册与图表 chunk 瘦身任务清单

- [x] Task 1: 新增轻量 BaseChart 组件
    - 1.1: 新增 `frontend/src/components/BaseChart.tsx`
    - 1.2: 从 `echarts/core` 引入核心能力
    - 1.3: 按需注册 `LineChart`、`RadarChart`、`ScatterChart`
    - 1.4: 按需注册 `GridComponent`、`TooltipComponent`、`LegendComponent`、`TitleComponent`、`VisualMapComponent`
    - 1.5: 注册 `CanvasRenderer`
    - 1.6: 实现 chart 初始化、`setOption`、resize 监听和卸载 dispose

- [x] Task 2: 替换通用图表组件依赖
    - 2.1: 修改 `frontend/src/components/TasteRadar.tsx`
    - 2.2: 将 `ReactECharts` 替换为 `BaseChart`
    - 2.3: 保持雷达图 option 和高度不变
    - 2.4: 修改 `frontend/src/components/TrendChart.tsx`
    - 2.5: 将 `ReactECharts` 替换为 `BaseChart`
    - 2.6: 保持折线趋势图 option 和高度不变

- [x] Task 3: 替换城市图表页面依赖
    - 3.1: 修改 `frontend/src/pages/CityMap.tsx`
    - 3.2: 将 `ReactECharts` 替换为 `BaseChart`
    - 3.3: 保持城市热力散点图 option 和高度不变
    - 3.4: 修改 `frontend/src/pages/CityTrends.tsx`
    - 3.5: 将 `ReactECharts` 替换为 `BaseChart`
    - 3.6: 保持城市趋势折线图 option 和高度不变

- [x] Task 4: 调整 Vite charts chunk 规则
    - 4.1: 修改 `frontend/vite.config.ts`
    - 4.2: 移除 `echarts-for-react` 的 manual chunk 判断
    - 4.3: 保留 `echarts` 进入 `charts` chunk
    - 4.4: 保持 `react`、`motion`、`vendor` chunk 规则不变

- [x] Task 5: 执行构建和 chunk 体积检查
    - 5.1: 执行 `npm run build`
    - 5.2: 检查 TypeScript 编译是否通过
    - 5.3: 检查 Vite 构建是否通过
    - 5.4: 对比 `charts` chunk 是否小于第四轮约 1.14MB
    - 5.5: 检查主入口 chunk 是否仍保持轻量

- [x] Task 6: 复查业务代码依赖和轻量 API
    - 6.1: 搜索业务代码是否仍引用 `echarts-for-react`
    - 6.2: 验证 `PUT /api/users/me/switch` 返回 200
    - 6.3: 使用 sessionId 验证 `GET /api/users/me` 返回 200
    - 6.4: 记录是否保留 package.json 中未使用依赖作为后续清理项

- [x] Task 7: 复查并生成第五轮总结
    - 7.1: 复查 BaseChart 是否只注册当前需要的 ECharts 模块
    - 7.2: 复查图表组件是否保持原有 option 逻辑
    - 7.3: 记录构建产物变化和仍存在的问题
    - 7.4: 生成 `.comate/specs/echarts-on-demand-round-5/summary.md`
