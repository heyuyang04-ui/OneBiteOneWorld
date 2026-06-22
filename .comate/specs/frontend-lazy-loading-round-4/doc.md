# 第四轮循环优化：前端路由懒加载与构建拆包

## 背景与问题

第二、三轮验证中，前端 `npm run build` 均通过，但持续出现 Vite 大 chunk 警告：

```text
Some chunks are larger than 500 kB after minification.
```

当前主 JS chunk 约 1.67MB。原因主要是 `frontend/src/App.tsx` 顶部同步导入了所有页面：

```tsx
import Login from './pages/Login'
import Home from './pages/Home'
import MealResult from './pages/MealResult'
import MealHistory from './pages/MealHistory'
import TasteProfile from './pages/TasteProfile'
import WeeklyReport from './pages/WeeklyReport'
import SocialDiscover from './pages/SocialDiscover'
import MatchDetail from './pages/MatchDetail'
import MatchList from './pages/MatchList'
import CityMap from './pages/CityMap'
import CityDistrict from './pages/CityDistrict'
import CityTrends from './pages/CityTrends'
import CityRecommend from './pages/CityRecommend'
import Notifications from './pages/Notifications'
import Settings from './pages/Settings'
```

其中多个页面或组件同步引入重型依赖：

- `echarts-for-react` / `echarts`
    - `components/TrendChart.tsx`
    - `components/TasteRadar.tsx`
    - `pages/CityMap.tsx`
    - `pages/CityTrends.tsx`
- `framer-motion`
    - `components/MatchCard.tsx`

这会导致用户打开登录页时，也下载城市图表、趋势图、匹配动效等暂时不需要的代码。

## 目标

- 将页面改为 React lazy route 级懒加载。
- 增加统一页面加载占位，不破坏当前移动端窄屏 shell 视觉。
- 配置 Vite manual chunks，将 React、图表库、动效库拆到独立 chunk。
- 保持现有路由路径和鉴权行为不变。
- 构建后不再出现单一主 chunk 过大的问题，或至少显著降低主入口 chunk 体积。

## 技术方案

### 1. App.tsx 改为 lazy imports

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx
```

保留同步导入：

```tsx
import { Suspense, lazy, useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import Layout from './components/Layout'
import api from './services/api'
import './App.css'
```

将页面同步导入替换为：

```tsx
const Login = lazy(() => import('./pages/Login'))
const Home = lazy(() => import('./pages/Home'))
const MealResult = lazy(() => import('./pages/MealResult'))
const MealHistory = lazy(() => import('./pages/MealHistory'))
const TasteProfile = lazy(() => import('./pages/TasteProfile'))
const WeeklyReport = lazy(() => import('./pages/WeeklyReport'))
const SocialDiscover = lazy(() => import('./pages/SocialDiscover'))
const MatchDetail = lazy(() => import('./pages/MatchDetail'))
const MatchList = lazy(() => import('./pages/MatchList'))
const CityMap = lazy(() => import('./pages/CityMap'))
const CityDistrict = lazy(() => import('./pages/CityDistrict'))
const CityTrends = lazy(() => import('./pages/CityTrends'))
const CityRecommend = lazy(() => import('./pages/CityRecommend'))
const Notifications = lazy(() => import('./pages/Notifications'))
const Settings = lazy(() => import('./pages/Settings'))
```

增加页面加载占位：

```tsx
function PageFallback() {
  return <div className="app-page-loading">正在加载味觉世界...</div>
}
```

在 `Routes` 外层包 `Suspense`：

```tsx
<Suspense fallback={<PageFallback />}>
  <Routes>...</Routes>
</Suspense>
```

### 2. App.css 增加加载占位样式

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.css
```

新增：

```css
.app-page-loading {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  box-sizing: border-box;
  color: var(--app-porcelain);
  background:
    radial-gradient(circle at 50% 20%, rgba(241, 201, 135, 0.18), transparent 34%),
    linear-gradient(180deg, var(--app-night), var(--app-night-soft));
  font-size: 15px;
  letter-spacing: 0.02em;
}
```

与 `app-shell-checking` 视觉一致，避免切页时突兀。

### 3. Vite manual chunks 拆包

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/vite.config.ts
```

增加 build 配置：

```ts
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          charts: ['echarts', 'echarts-for-react'],
          motion: ['framer-motion'],
          vendor: ['axios', 'browser-image-compression'],
        },
      },
    },
  },
})
```

说明：

- `react` 基础运行时拆出稳定缓存。
- `charts` 将 ECharts 从主业务 chunk 拆出。
- `motion` 将 Framer Motion 从主业务 chunk 拆出。
- `vendor` 放置 axios 和图片压缩库。

### 4. 保持鉴权与跳转逻辑

`ProtectedLayout`、`AppRoutes` 的 session 恢复、401 跳转 `/login` 逻辑不变。

需要注意：

- lazy route 不应改变 `/`、`/login`、`/home` 等路径。
- `Navigate` fallback 仍应工作。
- `sessionExpired` banner 仍在 Suspense 外层展示，确保 session 失效提示不受页面 chunk 加载影响。

## 受影响文件

- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx`
    - 页面导入改为 `lazy`。
    - 增加 `Suspense` 和 `PageFallback`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.css`
    - 增加 `.app-page-loading`。
- `/Users/libowen/Desktop/one-bite-one-world/frontend/vite.config.ts`
    - 增加 `build.rollupOptions.output.manualChunks`。

## 验证方案

执行：

```bash
npm run build
```

检查：

- TypeScript 构建通过。
- Vite 输出多个 chunk。
- 主入口 JS chunk 明显小于之前约 1.67MB。
- 如仍有单 chunk > 500KB，确认是否为 `charts` chunk；这类独立懒加载图表 chunk 可接受，但主入口不应继续过大。

后端不改动，但为确保整体可运行，可执行轻量 API 验证：

- `PUT /api/users/me/switch` 返回 200。
- `GET /api/users/me` 带 session 返回 200。

## 边界条件

- 页面懒加载失败时，当前不新增 ErrorBoundary，避免本轮改动过大；后续可单独补充路由错误边界。
- 不改动页面内部业务逻辑和 API 调用。
- 不改动后端和 AI 配置。
- 不修改 demo 用户数据。

## 预期结果

- 首屏登录页不再同步加载全部页面和图表代码。
- 构建产物从单一大业务 chunk 变成多个更清晰的路由/依赖 chunk。
- 用户首次打开页面更轻，城市地图、报告、趋势等重页面在访问时再加载。
- 现有功能路径保持不变。
