import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

export default function Settings() {
  const [user, setUser] = useState<any>(null)
  const [privacy, setPrivacy] = useState('match_only')
  const [message, setMessage] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/users/me').then(res => {
      setUser(res.data.data)
      setPrivacy(res.data.data?.privacy_level || 'match_only')
    })
  }, [])

  const updatePrivacy = (level: string) => {
    const previous = privacy
    setPrivacy(level)
    setMessage('')
    api.put('/settings/privacy', { level }).then(res => {
      if (!res.data.success) {
        setPrivacy(previous)
        setMessage(res.data.error?.message || '隐私设置保存失败')
        return
      }
      setMessage('隐私设置已保存')
    }).catch(() => {
      setPrivacy(previous)
      setMessage('隐私设置保存失败，请重试')
    })
  }

  const clearLocalSession = () => {
    localStorage.removeItem('currentUserId')
    localStorage.removeItem('sessionId')
    navigate('/login', { replace: true })
  }

  const handleLogout = async () => {
    if (loggingOut) return
    setLoggingOut(true)
    try {
      await api.post('/auth/logout')
    } finally {
      clearLocalSession()
    }
  }

  const privacyOptions = [
    { value: 'public', label: '公开', desc: '味觉档案对所有人可见' },
    { value: 'match_only', label: '仅匹配', desc: '仅在匹配系统中脱敏使用' },
    { value: 'private', label: '私密', desc: '完全不参与社交匹配' },
  ]

  return (
    <div>
      <h2 style={{ fontSize: 18, color: 'var(--app-porcelain)', margin: '0 0 16px' }}>设置</h2>

      {user && (
        <div style={{ background: 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', borderRadius: 12, padding: 16, marginBottom: 12, border: '1px solid rgba(154,99,56,0.14)' }}>
          <h3 style={{ margin: '0 0 8px', fontSize: 15 }}>用户信息</h3>
          <p style={{ margin: '4px 0', fontSize: 13, color: 'var(--app-muted-dark)' }}>姓名：{user.name}</p>
          <p style={{ margin: '4px 0', fontSize: 13, color: 'var(--app-muted-dark)' }}>城市：{user.city}</p>
          <p style={{ margin: '4px 0', fontSize: 13, color: 'var(--app-muted-dark)' }}>职业：{user.occupation}</p>
        </div>
      )}

      <div style={{ background: 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', borderRadius: 12, padding: 16, marginBottom: 12, border: '1px solid rgba(154,99,56,0.14)' }}>
        <h3 style={{ margin: '0 0 8px', fontSize: 15 }}>隐私设置</h3>
          <p style={{ fontSize: 12, color: 'var(--app-muted-dark)', margin: '0 0 12px' }}>控制你的味觉数据如何被使用</p>
        {message && <p style={{ fontSize: 12, color: message.includes('失败') ? '#B54708' : 'var(--app-wood-deep)', margin: '0 0 10px' }}>{message}</p>}
        {privacyOptions.map(opt => (
          <div key={opt.value} onClick={() => updatePrivacy(opt.value)}
            style={{ padding: 12, borderRadius: 8, marginBottom: 6, cursor: 'pointer',
              border: privacy === opt.value ? '2px solid var(--app-amber)' : '1px solid rgba(154,99,56,0.14)',
              background: privacy === opt.value ? 'rgba(217,163,95,0.18)' : 'rgba(255,251,245,0.66)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--app-text-dark)' }}>{opt.label}</span>
              {privacy === opt.value && <span style={{ color: 'var(--app-wood-deep)' }}>✓</span>}
            </div>
            <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--app-muted-dark)' }}>{opt.desc}</p>
          </div>
        ))}
      </div>

      <button
        onClick={handleLogout}
        disabled={loggingOut}
        style={{
          width: '100%', padding: '12px 0', background: 'rgba(244,232,212,0.14)', color: 'var(--app-muted)',
          border: '1px solid var(--app-border)', borderRadius: 12, fontSize: 14, cursor: loggingOut ? 'not-allowed' : 'pointer',
          opacity: loggingOut ? 0.62 : 1,
        }}
      >
        {loggingOut ? '正在退出...' : '退出登录'}
      </button>
    </div>
  )
}
