import { Outlet, NavLink } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Bell, Camera, Map, Radar, Settings, Users } from 'lucide-react'
import './Layout.css'

const tabs = [
  { path: '/home', icon: Camera, label: '首页' },
  { path: '/profile', icon: Radar, label: '味觉' },
  { path: '/discover', icon: Users, label: '发现' },
  { path: '/city', icon: Map, label: '城市' },
]

export default function Layout() {
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    const handleUnreadDelta = (event: Event) => {
      const detail = (event as CustomEvent<{ delta?: number; unread_count?: number }>).detail || {}
      if (typeof detail.unread_count === 'number') {
        setUnreadCount(Math.max(0, detail.unread_count))
        return
      }
      if (typeof detail.delta === 'number') {
        setUnreadCount(prev => Math.max(0, prev + detail.delta!))
      }
    }
    window.addEventListener('notifications:unread-delta', handleUnreadDelta)
    return () => window.removeEventListener('notifications:unread-delta', handleUnreadDelta)
  }, [])

  useEffect(() => {
    const sessionId = localStorage.getItem('sessionId') || ''
    if (!sessionId) return
    const params = new URLSearchParams()
    params.set('x_session_id', sessionId)
    const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

    const es = new EventSource(`${apiBase}/notifications/stream?${params.toString()}`)
    let errorCount = 0
    es.onmessage = (e) => {
      errorCount = 0
      try {
        const data = JSON.parse(e.data)
        if (data.unread_count !== undefined) {
          setUnreadCount(data.unread_count)
        }
      } catch {}
    }
    es.onerror = () => {
      errorCount += 1
      if (errorCount >= 5) {
        es.close()
      }
    }
    return () => es.close()
  }, [])

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="brand">
          <span className="brand-title">一食万象</span>
          <span className="brand-sub">One Bite, One World</span>
        </div>
        <div className="header-actions">
          <NavLink to="/notifications" className="icon-btn" aria-label="通知">
            <Bell size={18} strokeWidth={1.8} />
            {unreadCount > 0 && (
              <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
            )}
          </NavLink>
          <NavLink to="/settings" className="icon-btn" aria-label="设置">
            <Settings size={18} strokeWidth={1.8} />
          </NavLink>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <nav className="tab-bar">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <NavLink
              key={tab.path}
              to={tab.path}
              className={({ isActive }) => `tab-item ${isActive ? 'active' : ''}`}
              end={tab.path === '/home'}
            >
              <span className="tab-icon"><Icon size={20} strokeWidth={1.8} /></span>
              <span className="tab-label">{tab.label}</span>
            </NavLink>
          )
        })}
      </nav>
    </div>
  )
}
