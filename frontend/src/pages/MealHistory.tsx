import { useState, useEffect } from 'react'
import type { MouseEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

type MealImage = string | { image: string; mime_type?: string }

function imageDataUrl(item: MealImage) {
  if (typeof item === 'string') return `data:image/jpeg;base64,${item}`
  return `data:${item.mime_type || 'image/jpeg'};base64,${item.image}`
}

export default function MealHistory() {
  const [meals, setMeals] = useState<any[]>([])
  const [images, setImages] = useState<Record<string, MealImage>>({})
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/meals?limit=50').then(res => {
      setMeals(res.data.data?.meals || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  useEffect(() => {
    const ids = meals.filter(m => m.has_image && !images[m.id]).slice(0, 30).map(m => m.id)
    if (ids.length === 0) return
    api.get(`/meals/images?ids=${ids.join(',')}`).then(res => {
      const loaded = res.data.data?.images || {}
      if (Object.keys(loaded).length > 0) {
        setImages(prev => ({ ...prev, ...loaded }))
      }
    }).catch(() => {})
  }, [meals, images])

  const handleDelete = async (meal: any, event: MouseEvent) => {
    event.stopPropagation()
    if (deletingId) return
    if (!window.confirm(`确认删除“${meal.dish_name}”这条记录吗？删除后会同步更新味觉画像。`)) return

    setDeletingId(meal.id)
    setError('')
    try {
      const res = await api.delete(`/meals/${meal.id}`)
      if (!res.data.success) {
        setError(res.data.error?.message || '删除失败，请重试')
        return
      }
      setMeals(prev => prev.filter(item => item.id !== meal.id))
      setImages(prev => {
        const next = { ...prev }
        delete next[meal.id]
        return next
      })
    } catch (e) {
      setError('删除失败，请稍后重试')
    } finally {
      setDeletingId('')
    }
  }

  if (loading) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--app-amber-soft)' }}>加载中...</div>

  const grouped: Record<string, any[]> = {}
  meals.forEach(m => {
    const day = m.meal_time?.slice(0, 10) || 'unknown'
    if (!grouped[day]) grouped[day] = []
    grouped[day].push(m)
  })

  return (
    <div>
      <h2 style={{ fontSize: 18, color: 'var(--app-porcelain)', margin: '0 0 12px' }}>餐食记录</h2>
      {error && <p style={{ color: '#F1C987', fontSize: 13, textAlign: 'center', margin: '0 0 12px' }}>{error}</p>}
      {Object.entries(grouped).sort((a, b) => b[0].localeCompare(a[0])).map(([date, items]) => (
        <div key={date} style={{ marginBottom: 16 }}>
          <h4 style={{ fontSize: 13, color: 'var(--app-muted)', margin: '0 0 6px' }}>{date}</h4>
          {items.map(m => (
            <div
              key={m.id}
              role="button"
              tabIndex={0}
              onClick={() => navigate(`/meal/${m.id}`)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') navigate(`/meal/${m.id}`)
              }}
              style={{ background: 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', borderRadius: 10, padding: 10, marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, boxShadow: '0 10px 24px rgba(2,8,12,0.16)', border: '1px solid rgba(154,99,56,0.12)', cursor: 'pointer' }}
            >
              {images[m.id] ? (
                <img src={imageDataUrl(images[m.id])} alt={m.dish_name} style={{ width: 46, height: 46, borderRadius: 10, objectFit: 'cover', flexShrink: 0 }} />
              ) : (
                <div style={{ width: 46, height: 46, borderRadius: 10, background: 'rgba(217,163,95,0.18)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>🍽️</div>
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <span style={{ display: 'block', fontSize: 14, fontWeight: 600, color: 'var(--app-text-dark)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.dish_name}</span>
                <span style={{ fontSize: 11, color: 'var(--app-muted-dark)' }}>{m.cuisine_type}</span>
              </div>
              <span style={{ fontSize: 12, color: 'var(--app-muted-dark)' }}>{m.meal_time?.slice(11, 16)}</span>
              <button
                type="button"
                onClick={(event) => handleDelete(m, event)}
                disabled={deletingId === m.id}
                style={{ border: '1px solid rgba(154,99,56,0.18)', borderRadius: 999, padding: '6px 9px', background: 'rgba(255,251,245,0.72)', color: 'var(--app-wood-deep)', fontSize: 12, fontWeight: 800, cursor: deletingId === m.id ? 'not-allowed' : 'pointer', opacity: deletingId === m.id ? 0.55 : 1 }}
              >
                {deletingId === m.id ? '删除中' : '删除'}
              </button>
            </div>
          ))}
        </div>
      ))}
      {meals.length === 0 && <p style={{ color: 'var(--app-muted)', textAlign: 'center' }}>暂无记录</p>}
    </div>
  )
}
