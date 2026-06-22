# 第四轮前端路由懒加载与构建拆包任务清单

- [x] Task 1: 改造页面导入为 lazy route
    - 1.1: 修改 `frontend/src/App.tsx`，从 React 引入 `Suspense` 和 `lazy`
    - 1.2: 保留 `Layout`、`api`、`App.css` 的同步导入
    - 1.3: 将 `Login`、`Home`、`MealResult`、`MealHistory`、`TasteProfile` 改为 `lazy(() => import(...))`
    - 1.4: 将 `WeeklyReport`、`SocialDiscover`、`MatchDetail`、`MatchList` 改为 `lazy(() => import(...))`
    - 1.5: 将 `CityMap`、`CityDistrict`、`CityTrends`、`CityRecommend`、`Notifications`、`Settings` 改为 `lazy(() => import(...))`

- [x] Task 2: 增加统一页面加载占位
    - 2.1: 在 `App.tsx` 中新增 `PageFallback` 组件
    - 2.2: 在 `Routes` 外层增加 `Suspense fallback={<PageFallback />}`
    - 2.3: 保持 `sessionExpired` banner 在 Suspense 外层
    - 2.4: 保持 `ProtectedLayout` 的 session 恢复逻辑不变

- [x] Task 3: 补充加载占位样式
    - 3.1: 修改 `frontend/src/App.css`
    - 3.2: 新增 `.app-page-loading` 样式
    - 3.3: 复用当前深色城市夜景背景、瓷白文字和居中布局
    - 3.4: 确保移动端加载态宽度和主 app shell 不冲突

- [x] Task 4: 配置 Vite manual chunks
    - 4.1: 修改 `frontend/vite.config.ts`
    - 4.2: 增加 `build.rollupOptions.output.manualChunks`
    - 4.3: 拆出 `react` chunk：`react`、`react-dom`、`react-router-dom`
    - 4.4: 拆出 `charts` chunk：`echarts`、`echarts-for-react`
    - 4.5: 拆出 `motion` chunk：`framer-motion`
    - 4.6: 拆出 `vendor` chunk：`axios`、`browser-image-compression`

- [x] Task 5: 执行构建和产物检查
    - 5.1: 执行 `npm run build`
    - 5.2: 检查 TypeScript 构建是否通过
    - 5.3: 检查 Vite 输出是否拆分为多个 chunk
    - 5.4: 对比主入口 JS chunk 是否明显小于上一轮约 1.67MB
    - 5.5: 判断是否仍有 >500KB chunk，并区分是否为可接受的独立 charts chunk

- [x] Task 6: 执行轻量运行验证
    - 6.1: 验证 `PUT /api/users/me/switch` 返回 200
    - 6.2: 使用返回的 sessionId 验证 `GET /api/users/me` 返回 200
    - 6.3: 确认前端路由构建后没有破坏鉴权相关 TypeScript 类型

- [x] Task 7: 复查并生成第四轮总结
    - 7.1: 复查 `App.tsx` 是否仍同步导入页面组件
    - 7.2: 复查 `vite.config.ts` manual chunks 是否生效
    - 7.3: 记录构建产物变化和仍存在的问题
    - 7.4: 生成 `.comate/specs/frontend-lazy-loading-round-4/summary.md`
