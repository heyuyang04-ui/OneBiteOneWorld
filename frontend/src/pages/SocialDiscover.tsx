import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import MatchCard from '../components/MatchCard'

export default function SocialDiscover() {
  const [matches, setMatches] = useState<any[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/match/discover?limit=20').then(res => {
      setMatches(res.data.data || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const handleLike = () => {
    if (actionLoading) return
    const m = matches[currentIdx]
    setActionLoading(true)
    api.post(`/match/${m.user.id}/action`, { action: 'like' }).then(res => {
      if (!res.data.success) {
        alert(res.data.error?.message || '匹配失败，请重试')
        return
      }
      if (res.data.data?.mutual) {
        alert(`恭喜！你和 ${m.user.name} 互相匹配了！`)
      }
      setCurrentIdx(prev => prev + 1)
    }).catch(() => {
      alert('网络异常，未完成匹配，请重试')
    }).finally(() => {
      setActionLoading(false)
    })
  }

  const handleSkip = () => {
    if (actionLoading) return
    setCurrentIdx(prev => prev + 1)
  }

  if (loading) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--app-amber-soft)' }}>Agent 正在为你寻找味觉伴侣...</div>

  if (currentIdx >= matches.length) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: 'var(--app-porcelain)' }}>
        <p style={{ fontSize: 40, marginBottom: 8 }}>🎉</p>
        <p style={{ color: 'var(--app-porcelain)' }}>今日推荐已看完</p>
        <button onClick={() => navigate('/matches')}
          style={{ marginTop: 12, background: 'linear-gradient(135deg, var(--app-wood), var(--app-amber))', color: '#1C120B', border: 'none', padding: '10px 20px', borderRadius: 10, cursor: 'pointer', fontWeight: 800 }}>
          查看我的匹配
        </button>
      </div>
    )
  }

  const current = matches[currentIdx]

  return (
    <div>
      <h2 style={{ fontSize: 18, color: 'var(--app-porcelain)', margin: '0 0 4px' }}>味觉发现</h2>
      <p style={{ fontSize: 12, color: 'var(--app-muted)', margin: '0 0 12px' }}>左滑跳过，右滑匹配</p>
      <MatchCard
        user={current.user}
        score={current.score}
        common={current.common}
        diff={current.diff}
        explanation={current.explanation}
        why_recommended={current.why_recommended}
        first_meal_suggestion={current.first_meal_suggestion}
        conversation_starter={current.conversation_starter}
        onLike={handleLike}
        onSkip={handleSkip}
      />
      <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--app-muted)', marginTop: 8 }}>
        {actionLoading ? '正在写入匹配...' : `${currentIdx + 1} / ${matches.length}`}
      </div>
    </div>
  )
}
