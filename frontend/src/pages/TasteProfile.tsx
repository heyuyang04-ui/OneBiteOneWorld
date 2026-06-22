import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import TasteRadar from '../components/TasteRadar'
import TrendChart from '../components/TrendChart'

type TimelineChapter = {
  title: string
  period: string
  evidence: string[]
  meaning: string
}

export default function TasteProfile() {
  const [profile, setProfile] = useState<any>(null)
  const [timeline, setTimeline] = useState<TimelineChapter[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([
      api.get('/profile'),
      api.get('/profile/timeline'),
    ]).then(([profileRes, timelineRes]) => {
      if (profileRes.status === 'fulfilled') {
        setProfile(profileRes.value.data.data)
      }
      if (timelineRes.status === 'fulfilled') {
        setTimeline(timelineRes.value.data.data?.chapters || [])
      }
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
  if (!profile) return <div style={{ textAlign: 'center', padding: 40 }}>暂无数据，先去拍照记录吧</div>

  return (
    <div>
      <TasteRadar data={profile.radar_data} title="我的味觉画像" />

      {profile.trends?.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ fontSize: 15, margin: '0 0 8px' }}>口味趋势</h3>
          <TrendChart data={profile.trends} />
        </div>
      )}

      <section style={{ marginTop: 16, background: 'var(--app-surface)', border: '1px solid var(--app-border)', borderRadius: 16, padding: 14, color: 'var(--app-porcelain)' }}>
        <div style={{ marginBottom: 12 }}>
          <h3 style={{ margin: 0, fontSize: 16 }}>饮食自传</h3>
          <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--app-muted)', lineHeight: 1.5 }}>Agent 根据你的餐食记录，把近期饮食变化整理成可回看的生活章节。</p>
        </div>
        {timeline.length > 0 ? (
          <div style={{ display: 'grid', gap: 10 }}>
            {timeline.map((chapter, idx) => (
              <article key={`${chapter.title}-${idx}`} style={{ background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 14, padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
                  <h4 style={{ margin: 0, fontSize: 14 }}>{chapter.title}</h4>
                  <span style={{ flexShrink: 0, fontSize: 11, color: 'var(--app-amber-soft)', background: 'rgba(217,163,95,0.18)', borderRadius: 999, padding: '3px 8px' }}>{chapter.period}</span>
                </div>
                <p style={{ margin: '8px 0', color: 'rgba(244,232,212,0.84)', fontSize: 13, lineHeight: 1.6 }}>{chapter.meaning}</p>
                {chapter.evidence?.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {chapter.evidence.map((item) => (
                      <span key={item} style={{ fontSize: 11, color: 'var(--app-porcelain)', background: 'rgba(217,163,95,0.14)', border: '1px solid rgba(217,163,95,0.22)', borderRadius: 999, padding: '3px 8px' }}>{item}</span>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
        ) : (
          <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 12, padding: 12, color: 'var(--app-muted)', fontSize: 13, lineHeight: 1.6 }}>
            继续上传几餐后，系统会生成你的第一段饮食自传。
          </div>
        )}
      </section>

      {profile.predictions && (
        <div style={{ marginTop: 16, background: 'rgba(217,163,95,0.12)', borderRadius: 12, padding: 12, border: '1px solid rgba(217,163,95,0.24)', color: 'var(--app-porcelain)' }}>
          <h4 style={{ margin: '0 0 6px', fontSize: 14 }}>Agent 预测：下周你可能偏好</h4>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {Object.entries(profile.predictions).filter(([_, v]) => (v as number) > 0.3).map(([k, v]) => (
              <span key={k} style={{ fontSize: 12, background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: 8, color: 'rgba(244,232,212,0.84)' }}>
                {k}: {Math.round((v as number) * 100)}%
              </span>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
        <Link to="/report" style={{ flex: 1, background: 'linear-gradient(135deg, var(--app-wood), var(--app-amber))', color: '#1C120B', textAlign: 'center', padding: '10px', borderRadius: 10, textDecoration: 'none', fontSize: 14, fontWeight: 800 }}>
          查看味觉周报
        </Link>
        <Link to="/history" style={{ flex: 1, background: 'rgba(255,255,255,0.08)', color: 'var(--app-porcelain)', textAlign: 'center', padding: '10px', borderRadius: 10, textDecoration: 'none', fontSize: 14, border: '1px solid var(--app-border)' }}>
          历史记录
        </Link>
      </div>
    </div>
  )
}
