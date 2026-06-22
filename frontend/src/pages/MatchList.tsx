import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

export default function MatchList() {
  const [tab, setTab] = useState<'mutual' | 'pending'>('mutual')
  const [matches, setMatches] = useState<any[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    api.get(`/match/list?status=${tab}`).then(res => setMatches(res.data.data || [])).catch(() => {})
  }, [tab])

  return (
    <div>
      <h2 style={{ fontSize: 18, color: 'var(--app-porcelain)', margin: '0 0 12px' }}>我的匹配</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button onClick={() => setTab('mutual')}
          style={{ flex: 1, padding: '8px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: tab === 'mutual' ? 'linear-gradient(135deg, var(--app-wood), var(--app-amber))' : 'rgba(244,232,212,0.16)', color: tab === 'mutual' ? '#1C120B' : 'var(--app-muted)', fontSize: 13, fontWeight: 700 }}>
          互相匹配
        </button>
        <button onClick={() => setTab('pending')}
          style={{ flex: 1, padding: '8px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: tab === 'pending' ? 'linear-gradient(135deg, var(--app-wood), var(--app-amber))' : 'rgba(244,232,212,0.16)', color: tab === 'pending' ? '#1C120B' : 'var(--app-muted)', fontSize: 13, fontWeight: 700 }}>
          待确认
        </button>
      </div>
      {matches.length === 0 && <p style={{ color: 'var(--app-muted)', textAlign: 'center', padding: 20 }}>暂无{tab === 'mutual' ? '匹配' : '待确认'}</p>}
      {matches.map(m => (
        <div key={m.match_id} onClick={() => navigate(`/match/${m.user.id}`)}
          style={{ background: 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', borderRadius: 10, padding: 12, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', boxShadow: '0 10px 24px rgba(2,8,12,0.16)', border: '1px solid rgba(154,99,56,0.14)' }}>
          <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg,var(--app-city-blue),var(--app-amber))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--app-porcelain)', fontSize: 14, fontWeight: 'bold' }}>
            {m.user.name[0]}
          </div>
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--app-text-dark)' }}>{m.user.name}</span>
            <span style={{ marginLeft: 6, fontSize: 11, color: 'var(--app-muted-dark)' }}>{m.user.city} · {m.user.occupation}</span>
            {tab === 'pending' && (
              <span style={{ display: 'block', marginTop: 3, fontSize: 11, color: 'var(--app-wood-deep)' }}>
                {m.direction === 'incoming' ? '待你确认' : '等待对方回应'}
              </span>
            )}
          </div>
          <span style={{ fontSize: 20 }}>→</span>
        </div>
      ))}
    </div>
  )
}
