# 第六轮循环优化：路由级 ErrorBoundary 与 chunk 加载失败恢复

## 背景与问题

第四轮已将页面改为 lazy route，第五轮进一步优化了图表 chunk。当前前端入口使用：

```tsx
<Suspense fallback={<PageFallback />}>
  <Routes>...</Routes>
</Suspense>
```

这能处理页面 chunk 加载中的状态，但如果出现以下情况：

- 网络中断导致 lazy route chunk 加载失败。
- 部署后用户浏览器缓存了旧 HTML，但新 chunk 文件名已变化。
- 某个页面运行时抛出未捕获错误。

React 默认会卸载整棵组件树或展示空白，不利于真实用户恢复。

本轮目标是在路由层补充 ErrorBoundary，让用户看到明确错误提示，并提供恢复入口。

## 目标

- 捕获 lazy route / 页面渲染错误。
- 展示符合“一食万象”主题的错误恢复卡片。
- 提供三个恢复动作：
    - 刷新页面
    - 返回登录页
    - 回到首页
- 保持现有路由、session 恢复、401 跳转逻辑不变。
- 不引入新依赖。

## 技术方案

### 1. 新增 RouteErrorBoundary 组件

新增文件：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/RouteErrorBoundary.tsx
```

使用 React class component 实现，因为 React ErrorBoundary 仍需 class 组件。

组件职责：

- `getDerivedStateFromError` 捕获错误。
- `componentDidCatch` 输出简短 console error，便于调试。
- 正常状态渲染 `children`。
- 错误状态渲染恢复 UI。

核心结构：

```tsx
import { Component, type ErrorInfo, type ReactNode } from 'react'
import './RouteErrorBoundary.css'

interface RouteErrorBoundaryProps {
  children: ReactNode
}

interface RouteErrorBoundaryState {
  hasError: boolean
}

export default class RouteErrorBoundary extends Component<RouteErrorBoundaryProps, RouteErrorBoundaryState> {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[RouteErrorBoundary]', error, info.componentStack)
  }

  private reload = () => window.location.reload()
  private goLogin = () => window.location.assign('/login')
  private goHome = () => window.location.assign('/home')

  render() {
    if (!this.state.hasError) return this.props.children
    return (...)
  }
}
```

### 2. 新增错误恢复样式

新增文件：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/RouteErrorBoundary.css
```

视觉要求：

- 深色城市夜景背景。
- 中央卡片，宽度适配移动端 `min(calc(100% - 32px), 380px)`。
- 文案清晰，不使用过度技术化错误堆栈。
- 按钮符合当前主题色：木色/琥珀主按钮，城市蓝次按钮。

示例文案：

```text
味觉世界加载失败
可能是网络波动或页面资源更新导致。你可以刷新页面，或返回首页重新进入。
```

### 3. App.tsx 接入 ErrorBoundary

修改文件：

```text
/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx
```

新增导入：

```tsx
import RouteErrorBoundary from './components/RouteErrorBoundary'
```

将：

```tsx
<Suspense fallback={<PageFallback />}>
  <Routes>...</Routes>
</Suspense>
```

改为：

```tsx
<RouteErrorBoundary>
  <Suspense fallback={<PageFallback />}>
    <Routes>...</Routes>
  </Suspense>
</RouteErrorBoundary>
```

保留：

- `sessionExpired` banner 在 ErrorBoundary 外层。
- `ProtectedLayout` 逻辑不变。
- `PageFallback` 不变。

### 4. 重置边界说明

本轮使用 `window.location.assign` 做恢复动作，不在 ErrorBoundary 内依赖 React Router hook，原因：

- class ErrorBoundary 无法直接使用 hook。
- chunk 加载失败时，强制刷新/跳转比尝试在已损坏的 React tree 中继续路由更可靠。

### 5. 验证方案

执行：

```bash
npm run build
```

检查：

- TypeScript 编译通过。
- Vite 构建通过。
- `RouteErrorBoundary` 被打包为正常组件。
- 主入口 chunk 不应显著变大。

轻量 API 验证：

- `PUT /api/users/me/switch` 返回 200。
- `GET /api/users/me` 带 session 返回 200。

代码复查：

- `App.tsx` 中 `Routes` 被 `RouteErrorBoundary` 包裹。
- `RouteErrorBoundary` 不包含敏感错误细节展示。
- 恢复按钮使用浏览器原生跳转，避免 chunk 错误时依赖路由运行状态。

## 受影响文件

- 新增：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/RouteErrorBoundary.tsx`
- 新增：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/components/RouteErrorBoundary.css`
- 修改：`/Users/libowen/Desktop/one-bite-one-world/frontend/src/App.tsx`

## 边界条件

- ErrorBoundary 不能捕获异步事件回调中的错误，这是 React 限制；本轮只覆盖渲染期和 lazy chunk 加载错误。
- 不新增 error reporting 服务。
- 不展示错误堆栈给用户，只在 console 输出简短调试信息。
- 不改后端、不改 AI 配置、不改 demo 用户。

## 预期结果

- lazy route 或页面渲染失败时不再空白。
- 用户可以刷新、回首页或回登录页恢复。
- 前端真实使用稳定性提升，尤其适合部署资源更新或网络波动场景。
