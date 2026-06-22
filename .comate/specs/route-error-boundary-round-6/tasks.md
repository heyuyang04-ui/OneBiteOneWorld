# 第六轮路由级 ErrorBoundary 与 chunk 加载失败恢复任务清单

- [x] Task 1: 新增 RouteErrorBoundary 组件
    - 1.1: 新增 `frontend/src/components/RouteErrorBoundary.tsx`
    - 1.2: 使用 class component 实现 React ErrorBoundary
    - 1.3: 实现 `getDerivedStateFromError`
    - 1.4: 实现 `componentDidCatch` 并仅向 console 输出调试信息
    - 1.5: 正常状态渲染 `children`
    - 1.6: 错误状态渲染恢复 UI

- [x] Task 2: 实现错误恢复动作
    - 2.1: 在 `RouteErrorBoundary` 中实现刷新页面动作
    - 2.2: 实现返回登录页动作
    - 2.3: 实现回到首页动作
    - 2.4: 使用 `window.location.reload` 和 `window.location.assign`，避免依赖可能已损坏的 Router 状态

- [x] Task 3: 新增错误恢复样式
    - 3.1: 新增 `frontend/src/components/RouteErrorBoundary.css`
    - 3.2: 实现深色城市夜景背景
    - 3.3: 实现移动端适配的中央恢复卡片
    - 3.4: 实现主按钮和次按钮主题色
    - 3.5: 确保不展示技术堆栈给普通用户

- [x] Task 4: 在 App.tsx 接入 ErrorBoundary
    - 4.1: 修改 `frontend/src/App.tsx` 引入 `RouteErrorBoundary`
    - 4.2: 使用 `RouteErrorBoundary` 包裹 `Suspense` 和 `Routes`
    - 4.3: 保持 `sessionExpired` banner 在 ErrorBoundary 外层
    - 4.4: 保持 `PageFallback` 和 `ProtectedLayout` 逻辑不变

- [x] Task 5: 执行构建验证
    - 5.1: 执行 `npm run build`
    - 5.2: 检查 TypeScript 编译是否通过
    - 5.3: 检查 Vite 构建是否通过
    - 5.4: 检查主入口 chunk 是否未显著增大

- [x] Task 6: 执行轻量 API 验证
    - 6.1: 验证 `PUT /api/users/me/switch` 返回 200
    - 6.2: 使用 sessionId 验证 `GET /api/users/me` 返回 200
    - 6.3: 确认前端错误边界改造未影响鉴权相关 TypeScript 类型

- [x] Task 7: 复查并生成第六轮总结
    - 7.1: 复查 `App.tsx` 中 `Routes` 是否被 `RouteErrorBoundary` 包裹
    - 7.2: 复查 `RouteErrorBoundary` 是否未向用户展示错误堆栈
    - 7.3: 记录构建结果和仍存在的问题
    - 7.4: 生成 `.comate/specs/route-error-boundary-round-6/summary.md`
