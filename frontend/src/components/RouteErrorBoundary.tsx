import { Component, type ErrorInfo, type ReactNode } from 'react'
import './RouteErrorBoundary.css'

interface RouteErrorBoundaryProps {
  children: ReactNode
}

interface RouteErrorBoundaryState {
  hasError: boolean
}

export default class RouteErrorBoundary extends Component<RouteErrorBoundaryProps, RouteErrorBoundaryState> {
  state: RouteErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): RouteErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[RouteErrorBoundary]', error, info.componentStack)
  }

  private reload = () => {
    window.location.reload()
  }

  private goLogin = () => {
    window.location.assign('/login')
  }

  private goHome = () => {
    window.location.assign('/home')
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="route-error-page">
        <section className="route-error-card">
          <p className="route-error-eyebrow">一食万象</p>
          <h2>味觉世界加载失败</h2>
          <p className="route-error-copy">可能是网络波动或页面资源更新导致。你可以刷新页面，或返回首页重新进入。</p>
          <div className="route-error-actions">
            <button type="button" className="route-error-primary" onClick={this.reload}>刷新页面</button>
            <button type="button" onClick={this.goHome}>回到首页</button>
            <button type="button" onClick={this.goLogin}>返回登录</button>
          </div>
        </section>
      </div>
    )
  }
}
