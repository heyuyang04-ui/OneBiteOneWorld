import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../services/api'

const dimLabels: Record<string, string> = { spicy: '辣', sweet: '甜', sour: '酸', salty: '咸', umami: '鲜', bitter: '苦' }

export default function CityDistrict() {
  const { id } = useParams()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api.get(`/city/district/${id}`).then(res => {
      setData(res.data.success ? res.data.data : null)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [id])

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 40, color: 'var(--app-amber-soft)' }}>Agent 正在读取区县味觉信号...</div>
  }

  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: 28, color: 'var(--app-porcelain)' }}>
        <p style={{ margin: '0 0 12px' }}>未找到区县信息</p>
        <Link to="/city" style={{ color: 'var(--app-amber-soft)', textDecoration: 'none' }}>返回城市地图</Link>
      </div>
    )
  }

  const tasteEntries = Object.entries(data.taste_profile || {})
  const restaurants = data.restaurants || []

  return (
    <div>
      <Link to="/city" style={{ display: 'inline-block', marginBottom: 12, color: 'var(--app-amber-soft)', textDecoration: 'none', fontSize: 13 }}>← 返回城市地图</Link>

      <section style={{ background: 'linear-gradient(135deg, rgba(154,99,56,0.26), rgba(217,163,95,0.12))', border: '1px solid rgba(217,163,95,0.24)', borderRadius: 16, padding: 16, marginBottom: 12, color: 'var(--app-porcelain)' }}>
        <p style={{ margin: '0 0 4px', fontSize: 12, color: 'var(--app-amber-soft)' }}>城市区县味觉信号</p>
        <h2 style={{ margin: '0 0 8px', fontSize: 22 }}>{data.district?.name || id}</h2>
        <p style={{ margin: 0, fontSize: 13, color: 'rgba(244,232,212,0.82)', lineHeight: 1.6 }}>
          汇聚 {data.meal_count || 0} 次餐桌记录，观察这里正在形成的味觉偏好。
        </p>
      </section>

      {tasteEntries.length > 0 && (
        <section style={{ background: 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', border: '1px solid rgba(154,99,56,0.14)', borderRadius: 14, padding: 14, marginBottom: 12 }}>
          <h3 style={{ margin: '0 0 10px', fontSize: 15, color: 'var(--app-text-dark)' }}>口味维度</h3>
          <div style={{ display: 'grid', gap: 8 }}>
            {tasteEntries.map(([key, value]) => {
              const score = Number(value) || 0
              return (
                <div key={key} style={{ display: 'grid', gridTemplateColumns: '34px 1fr 42px', alignItems: 'center', gap: 8 }}>
                  <span style={{ color: 'var(--app-muted-dark)', fontSize: 12 }}>{dimLabels[key] || key}</span>
                  <span style={{ height: 8, borderRadius: 999, background: 'rgba(92,56,34,0.12)', overflow: 'hidden' }}>
                    <span style={{ display: 'block', width: `${Math.round(score * 100)}%`, height: '100%', background: 'linear-gradient(90deg, var(--app-wood), var(--app-amber-soft))' }} />
                  </span>
                  <strong style={{ color: 'var(--app-wood-deep)', fontSize: 12, textAlign: 'right' }}>{Math.round(score * 100)}%</strong>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {data.top_cuisines?.length > 0 && (
        <section style={{ background: 'var(--app-surface)', border: '1px solid var(--app-border)', borderRadius: 14, padding: 14, marginBottom: 12, color: 'var(--app-porcelain)' }}>
          <h3 style={{ margin: '0 0 10px', fontSize: 15 }}>热门菜系</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {data.top_cuisines.map((cuisine: string) => (
              <span key={cuisine} style={{ fontSize: 12, borderRadius: 999, padding: '4px 9px', background: 'rgba(217,163,95,0.16)' }}>{cuisine}</span>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 style={{ margin: '0 0 10px', fontSize: 15, color: 'var(--app-porcelain)' }}>附近餐厅信号</h3>
        {restaurants.length > 0 ? restaurants.map((restaurant: any) => (
          <article key={restaurant.id || restaurant.name} style={{ background: 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', border: '1px solid rgba(154,99,56,0.14)', borderRadius: 12, padding: 12, marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
              <strong style={{ color: 'var(--app-text-dark)', fontSize: 14 }}>{restaurant.name}</strong>
              {restaurant.rating && <span style={{ color: 'var(--app-wood-deep)', fontSize: 12, fontWeight: 800 }}>⭐ {restaurant.rating}</span>}
            </div>
            <p style={{ margin: '6px 0 0', color: 'var(--app-muted-dark)', fontSize: 12 }}>
              {restaurant.cuisine_type || '餐厅'} · {'💰'.repeat(restaurant.price_level || 0)}
            </p>
          </article>
        )) : (
          <div style={{ textAlign: 'center', padding: 28, color: 'var(--app-muted)', background: 'rgba(244,232,212,0.08)', borderRadius: 12 }}>
            当前区县暂无餐厅推荐数据
          </div>
        )}
      </section>
    </div>
  )
}
