# 第五轮循环优化：ECharts 按需注册与图表 chunk 瘦身

## 背景与问题

第四轮已经将页面改为 lazy route，并配置 Vite manual chunks。构建结果显示首屏入口 JS 已从约 1.67MB 降到 8.12KB，但仍存在独立图表 chunk：

```text
dist/assets/charts-BPKPLtvJ.js   1,144.31 kB │ gzip: 379.93 kB
```

原因是当前多个图表组件直接使用：

```tsx
import ReactECharts from 'echarts-for-react'
```

受影响文件：

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/TasteRadar.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/TrendChart.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx`
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityTrends.tsx`

`echarts-for-react` 默认使用完整 ECharts，导致 `charts` chunk 仍较大。第五轮重点优化图表依赖体积，不改业务逻辑、不改接口、不改主题色。

## 目标

- 使用 ECharts core 按需注册图表模块。
- 替换 `echarts-for-react` 直接用法，避免完整 ECharts 被打进 chunk。
- 保持现有雷达图、折线图、散点热力图视觉和交互能力。
- 构建通过，并显著降低 `charts` chunk 体积。

## 技术方案

### 1. 新增轻量 ECharts 组件

新增文件：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/BaseChart.tsx
```

职责：

- 使用 `echarts/core`。
- 按需注册当前项目使用的图表和组件：
    - `LineChart`
    - `RadarChart`
    - `ScatterChart`
    - `GridComponent`
    - `TooltipComponent`
    - `LegendComponent`
    - `TitleComponent`
    - `VisualMapComponent`
    - `CanvasRenderer`
- 提供一个轻量 React wrapper：
    - 初始化 chart。
    - `setOption(option, true)` 更新配置。
    - 监听窗口 resize。
    - 卸载时 dispose。

核心实现示意：

```tsx
import { useEffect, useRef } from 'react'
import * as echarts from 'echarts/core'
import { LineChart, RadarChart, ScatterChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsCoreOption } from 'echarts/core'

echarts.use([
  LineChart,
  RadarChart,
  ScatterChart,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
])

interface BaseChartProps {
  option: EChartsCoreOption
  style?: React.CSSProperties
  className?: string
}

export default function BaseChart({ option, style, className }: BaseChartProps) {
  const ref = useRef<HTMLDivElement>(null)
  const chartRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!ref.current) return
    chartRef.current = echarts.init(ref.current)
    return () => {
      chartRef.current?.dispose()
      chartRef.current = null
    }
  }, [])

  useEffect(() => {
    chartRef.current?.setOption(option, true)
  }, [option])

  useEffect(() => {
    const resize = () => chartRef.current?.resize()
    window.addEventListener('resize', resize)
    return () => window.removeEventListener('resize', resize)
  }, [])

  return <div ref={ref} className={className} style={style} />
}
```

### 2. 替换现有图表组件依赖

修改：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/TasteRadar.tsx
/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/TrendChart.tsx
```

替换：

```tsx
import ReactECharts from 'echarts-for-react'
```

为：

```tsx
import BaseChart from './BaseChart'
```

渲染替换：

```tsx
return <BaseChart option={option} style={{ height: 260 }} />
```

和：

```tsx
return <BaseChart option={option} style={{ height: 220 }} />
```

### 3. 替换城市页面直接依赖

修改：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx
/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityTrends.tsx
```

替换：

```tsx
import ReactECharts from 'echarts-for-react'
```

为：

```tsx
import BaseChart from '../components/BaseChart'
```

渲染替换：

```tsx
<BaseChart option={chartOption} style={{ height: 280 }} />
<BaseChart option={chartOption} style={{ height: 240 }} />
```

### 4. 调整 Vite manual chunks

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/vite.config.ts
```

当前 charts chunk 判断包含：

```ts
id.includes('node_modules/echarts') || id.includes('node_modules/echarts-for-react')
```

按需注册后项目不应再引用 `echarts-for-react`。保留 `echarts` chunk 判断即可：

```ts
if (id.includes('node_modules/echarts')) {
  return 'charts'
}
```

`echarts-for-react` 依赖可暂时保留在 `package.json` 中，避免本轮变更涉及依赖安装和 lockfile；若后续确认不再使用，可单独移除依赖。

## 受影响文件

- 新增：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/BaseChart.tsx`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/TasteRadar.tsx`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/TrendChart.tsx`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityMap.tsx`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/pages/CityTrends.tsx`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/vite.config.ts`

## 验证方案

执行：

```bash
npm run build
```

检查：

- TypeScript 编译通过。
- Vite 构建通过。
- 搜索 `echarts-for-react`，确认业务代码不再引用。
- 对比 `charts` chunk 大小是否小于第四轮约 1.14MB。
- 确认主入口 chunk 仍保持小体积。

轻量 API 验证：

- `PUT /api/users/me/switch` 返回 200。
- 使用 sessionId 调用 `GET /api/users/me` 返回 200。

## 边界条件

- BaseChart 只注册当前使用到的 chart/component，避免过度引入。
- 保留 CanvasRenderer，避免切换 SVG 渲染带来的视觉差异。
- 不修改图表 option 业务含义。
- 不改后端、不改 AI 配置、不改 demo 用户。
- 本轮不删除 `echarts-for-react` 依赖，避免因 package lock 状态引入额外变更。

## 预期结果

- `charts` chunk 明显小于第四轮的 1.14MB。
- 图表页面仍能正常渲染雷达图、折线图和散点图。
- 首屏入口 chunk 保持轻量。
- 为后续进一步拆分图表页面或移除无用依赖打基础。
