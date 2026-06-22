# 第五轮循环优化总结：ECharts 按需注册与图表 chunk 瘦身

## 本轮完成内容

- 新增轻量图表组件
    - 新增 `frontend/src/components/BaseChart.tsx`。
    - 改用 `echarts/core`。
    - 按需注册当前项目实际使用的图表：
        - `LineChart`
        - `RadarChart`
        - `ScatterChart`
    - 按需注册当前项目实际使用的组件：
        - `GridComponent`
        - `TooltipComponent`
        - `LegendComponent`
        - `TitleComponent`
        - `VisualMapComponent`
    - 使用 `CanvasRenderer` 保持原有渲染方式。
    - 实现 chart 初始化、`setOption` 更新、窗口 resize、卸载 dispose。

- 替换通用图表组件依赖
    - `frontend/src/components/TasteRadar.tsx` 从 `ReactECharts` 替换为 `BaseChart`。
    - `frontend/src/components/TrendChart.tsx` 从 `ReactECharts` 替换为 `BaseChart`。
    - 雷达图、趋势图 option 和高度保持不变。

- 替换城市图表页面依赖
    - `frontend/src/pages/CityMap.tsx` 从 `ReactECharts` 替换为 `BaseChart`。
    - `frontend/src/pages/CityTrends.tsx` 从 `ReactECharts` 替换为 `BaseChart`。
    - 城市热力散点图、城市趋势折线图 option 和高度保持不变。

- 调整 Vite charts chunk 规则
    - `frontend/vite.config.ts` 移除 `echarts-for-react` 的 manual chunk 判断。
    - 保留 `echarts` 进入 `charts` chunk。
    - `react`、`motion`、`vendor` chunk 规则保持不变。

## 构建结果

第一次构建遇到 TypeScript 类型问题：

```text
TasteRadar.tsx: animationEasing string is not assignable to AnimationEasing
```

处理方式：

- `BaseChart` 的 `option` 类型从严格 `EChartsCoreOption` 放宽为 `Record<string, unknown>`。
- 原因是当前项目的 option 对象来自多个页面，已有部分字段是普通字符串推断；本轮目标是替换图表封装和降低 chunk，不额外重写所有 option 类型。

最终执行 `npm run build` 通过。

第四轮图表 chunk：

```text
dist/assets/charts-BPKPLtvJ.js   1,144.31 kB │ gzip: 379.93 kB
```

第五轮图表 chunk：

```text
dist/assets/charts-DaeXGnul.js     571.21 kB │ gzip: 190.82 kB
```

效果：

- `charts` chunk 从 1.14MB 降到 571KB。
- gzip 后从 379.93KB 降到 190.82KB。
- 图表依赖体积约减少一半。
- 主入口 chunk 仍保持轻量：

```text
dist/assets/index-BrRqrOcB.js       8.12 kB │ gzip:   2.93 kB
```

Vite 仍提示存在 >500KB chunk，但已经从 1.14MB 降到 571KB，剩余主要是 ECharts core 及必要图表模块。

## 复查结果

- 业务代码中已无 `echarts-for-react` 或 `ReactECharts` 引用。
- 当前图表引用集中到 `BaseChart`：
    - `TasteRadar.tsx`
    - `TrendChart.tsx`
    - `CityMap.tsx`
    - `CityTrends.tsx`
- `BaseChart` 只注册当前需要的 ECharts 模块，没有引入完整 ECharts。
- `package.json` 中仍保留 `echarts-for-react` 依赖，本轮未删除依赖，避免引入 lockfile 或安装状态变更；后续可单独清理。

## 轻量 API 验证

验证通过：

- `PUT /api/users/me/switch` 返回 200，并返回 sessionId。
- 使用 sessionId 调用 `GET /api/users/me` 返回 200，用户为 `user_bowen`。

## 下一轮候选优化

- 清理 `echarts-for-react` 未使用依赖，并同步更新依赖锁文件。
- 增加路由级 ErrorBoundary，处理 lazy route 或 chunk 加载失败。
- 如果还要继续压缩图表体积，可进一步评估：
    - 单独将雷达、趋势、城市图表拆成更细粒度 chunk。
    - 将非核心图表页面延迟到用户交互后加载图表组件。
- 增加显式登出接口，使用第三轮新增的 `delete_session` 删除当前 session。
