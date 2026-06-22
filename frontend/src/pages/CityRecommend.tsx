import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../services/api'

const dimLabels: Record<string, string> = { spicy: '辣', sweet: '甜', sour: '酸', salty: '咸', umami: '鲜', bitter: '苦' }

export default function CityRecommend() {
  const [searchParams] = useSearchParams()
  const city = searchParams.get('city') || 'beijing'
  const [data, setData] = useState<any>(null)
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.allSettled([
      api.get(`/city/recommend?city=${city}`),
      api.get(`/city/live-summary?city=${city}`),
    ]).then(([recommendRes, summaryRes]) => {
      if (recommendRes.status === 'fulfilled') {
        setData(recommendRes.value.data.data)
      }
      if (summaryRes.status === 'fulfilled') {
        setSummary(summaryRes.value.data.data)
      }
    }).finally(() => setLoading(false))
  }, [city])

  if (loading) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--app-amber-soft)' }}>Agent 正在分析推荐...</div>

  const restaurants = data?.matched_restaurants?.length > 0 ? data.matched_restaurants : data?.restaurants || []
  const trends = Array.isArray(data?.trends) ? data.trends : []
  const sourceLabel = summary?.source === 'real' ? '真实餐食聚合' : '模拟数据兜底'
  const cityLabel = summary?.city_name || summary?.city || city

  return (
    <div>
      <h2 style={{ fontSize: 18, color: 'var(--app-porcelain)', margin: '0 0 4px' }}>个性化推荐</h2>
      <p style={{ fontSize: 12, color: 'var(--app-muted)', margin: '0 0 12px' }}>{cityLabel} · 基于你的味觉档案 × 城市趋势 × 餐厅画像</p>

      {summary && (
        <section style={{ background: 'linear-gradient(135deg, rgba(154,99,56,0.26), rgba(217,163,95,0.12))', border: '1px solid rgba(217,163,95,0.24)', borderRadius: 16, padding: 14, marginBottom: 14, color: 'var(--app-porcelain)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
            <div>
              <p style={{ margin: '0 0 4px', fontSize: 12, color: 'var(--app-amber-soft)' }}>城市实时信号 · {sourceLabel}</p>
              <h3 style={{ margin: 0, fontSize: 16 }}>{cityLabel} 正在这样吃</h3>
            </div>
            <span style={{ flexShrink: 0, fontSize: 11, padding: '4px 8px', borderRadius: 999, background: 'rgba(255,255,255,0.1)' }}>{summary.meal_count || 0} 餐</span>
          </div>
          <p style={{ margin: '8px 0 10px', fontSize: 13, lineHeight: 1.6, color: 'rgba(244,232,212,0.84)' }}>{summary.summary}</p>
          {summary.hot_cuisines?.length > 0 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
              {summary.hot_cuisines.map((item: any) => <span key={item.name} style={{ fontSize: 11, borderRadius: 999, padding: '3px 8px', background: 'rgba(255,255,255,0.1)' }}>{item.name} · {item.count}</span>)}
            </div>
          )}
          {summary.taste_trends && Object.keys(summary.taste_trends).length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              {Object.entries(summary.taste_trends).slice(0, 6).map(([key, value]) => (
                <div key={key} style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 10, padding: 8 }}>
                  <span style={{ display: 'block', fontSize: 11, color: 'var(--app-muted)' }}>{dimLabels[key] || key}</span>
                  <strong style={{ fontSize: 14 }}>{Math.round((Number(value) || 0) * 100)}%</strong>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 15, margin: '0 0 8px', color: 'var(--app-porcelain)' }}>推荐餐厅</h3>
        {restaurants.length > 0 ? restaurants.map((r: any) => (
          <article key={r.id || r.name} style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: 14, padding: 12, marginBottom: 10, color: 'var(--app-porcelain)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
              <div>
                <span style={{ fontSize: 15, fontWeight: 600 }}>{r.name}</span>
                <span style={{ marginLeft: 6, fontSize: 11, background: 'rgba(217,163,95,0.18)', color: 'var(--app-porcelain)', padding: '1px 6px', borderRadius: 6 }}>{r.cuisine_type}</span>
              </div>
              <span style={{ flexShrink: 0, fontSize: 13, fontWeight: 'bold', color: 'var(--app-amber-soft)' }}>{Math.round((r.match_score || 0) * 100)}% 匹配</span>
            </div>
            <div style={{ marginTop: 5, fontSize: 11, color: 'var(--app-muted)' }}>
              ⭐ {r.rating} · {'💰'.repeat(r.price_level || 0)} · {r.district} · {r.tags?.join(' · ')}
            </div>
            {r.reason && <p style={{ margin: '8px 0 0', fontSize: 13, lineHeight: 1.5, color: 'rgba(244,232,212,0.84)' }}>{r.reason}</p>}
            {r.recommended_dishes?.length > 0 && (
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                {r.recommended_dishes.map((dish: string) => <span key={dish} style={{ fontSize: 11, borderRadius: 999, padding: '3px 8px', background: 'rgba(217,163,95,0.16)' }}>{dish}</span>)}
              </div>
            )}
            {(r.best_for || r.tradeoff) && (
              <div style={{ marginTop: 8, fontSize: 12, color: 'var(--app-muted)', lineHeight: 1.6 }}>
                {r.best_for && <div>适合：{r.best_for}</div>}
                {r.tradeoff && <div>取舍：{r.tradeoff}</div>}
              </div>
            )}
          </article>
        )) : (
          <div style={{ textAlign: 'center', padding: 28, color: 'var(--app-muted)', background: 'rgba(244,232,212,0.08)', borderRadius: 12 }}>
            当前城市暂无餐厅推荐
          </div>
        )}
      </div>

      <div>
        <h3 style={{ fontSize: 15, margin: '0 0 8px', color: 'var(--app-porcelain)' }}>你可能感兴趣的趋势</h3>
        {trends.length > 0 ? trends.map((t: any, i: number) => (
          <div key={i} style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: 10, padding: 10, marginBottom: 6 }}>
            <span style={{ fontSize: 13, color: 'rgba(244,232,212,0.84)' }}>
              {t.city_name ? `${t.city_name} · ` : ''}{t.district} 的 {dimLabels[t.dimension] || t.dimension} 正在上升 (+{Math.round((Number(t.change) || 0) * 100)}%)
            </span>
            <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--app-muted)' }}>你的偏好: {Math.round((Number(t.your_preference) || 0) * 100)}%</span>
          </div>
        )) : (
          <div style={{ textAlign: 'center', padding: 24, color: 'var(--app-muted)', background: 'rgba(244,232,212,0.08)', borderRadius: 12 }}>
            当前城市暂无匹配趋势
          </div>
        )}
      </div>
    </div>
  )
}
