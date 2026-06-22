import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

export default function Notifications() {
  const [items, setItems] = useState<any[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/notifications').then(res => setItems(res.data.data || [])).catch(() => {})
  }, [])

  const markRead = (id: string) => {
    const target = items.find(n => n.id === id)
    if (!target || target.is_read) return
    api.post(`/notifications/${id}/read`).then(res => {
      if (!res.data.success) return
      setItems(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
      window.dispatchEvent(new CustomEvent('notifications:unread-delta', { detail: { delta: -1 } }))
    }).catch(() => {})
  }

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1)
      return
    }
    navigate('/home', { replace: true })
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, margin: '0 0 12px' }}>
        <button
          type="button"
          onClick={handleBack}
          style={{ border: '1px solid rgba(241,201,135,0.26)', borderRadius: 999, padding: '8px 12px', background: 'rgba(255,251,245,0.08)', color: 'var(--app-porcelain)', fontSize: 13, fontWeight: 800, cursor: 'pointer' }}
        >
          返回
        </button>
        <h2 style={{ flex: 1, fontSize: 18, color: 'var(--app-porcelain)', margin: 0, textAlign: 'center' }}>Agent 推送中心</h2>
        <button
          type="button"
          onClick={() => navigate('/home')}
          style={{ border: 'none', borderRadius: 999, padding: '8px 12px', background: 'linear-gradient(135deg, var(--app-wood), var(--app-amber))', color: '#1C120B', fontSize: 13, fontWeight: 800, cursor: 'pointer' }}
        >
          回首页
        </button>
      </div>
      {items.length === 0 && <p style={{ color: 'var(--app-muted)', textAlign: 'center', padding: 40 }}>暂无通知</p>}
      {items.map(n => (
        <div key={n.id} onClick={() => markRead(n.id)}
          style={{ background: n.is_read ? 'rgba(244,232,212,0.72)' : 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', borderRadius: 10, padding: 12, marginBottom: 8,
            borderLeft: n.is_read ? 'none' : '3px solid var(--app-amber)', boxShadow: '0 10px 24px rgba(2,8,12,0.16)', cursor: 'pointer' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--app-text-dark)' }}>{n.title || n.type}</span>
            <span style={{ fontSize: 10, color: 'var(--app-muted-dark)' }}>{n.created_at?.slice(5, 16)}</span>
          </div>
          <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--app-muted-dark)' }}>{n.content?.slice(0, 100)}</p>
        </div>
      ))}
    </div>
  )
}
