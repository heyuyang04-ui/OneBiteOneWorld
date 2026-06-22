import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'
import TasteRadar from '../components/TasteRadar'

export default function MatchDetail() {
  const { id } = useParams()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/match/${id}/detail`).then(res => {
      setData(res.data.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [id])

  if (loading) return <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
  if (!data) return <div style={{ textAlign: 'center', padding: 40 }}>未找到匹配信息</div>

  const companion = data.companion_plan

  return (
    <div>
      <div style={{ background: 'var(--app-surface)', border: '1px solid var(--app-border)', borderRadius: 16, padding: 16, marginBottom: 12, color: 'var(--app-porcelain)' }}>
        <h3 style={{ margin: '0 0 4px' }}>与 {data.other_user?.name} 的味觉对比</h3>
        <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
          {data.other_user?.tags?.map((t: string) => (
            <span key={t} style={{ fontSize: 11, background: 'rgba(217,163,95,0.18)', color: 'var(--app-porcelain)', padding: '2px 8px', borderRadius: 8 }}>{t}</span>
          ))}
        </div>
        <TasteRadar data={data.compare_radar?.me || {}} compareData={data.compare_radar?.other || {}} />
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, fontSize: 12 }}>
          <span style={{ color: 'var(--app-amber-soft)' }}>● 我</span>
          <span style={{ color: 'var(--app-city-blue)' }}>● {data.other_user?.name}</span>
        </div>
      </div>

      {companion && (
        <section style={{ background: 'linear-gradient(135deg, rgba(154,99,56,0.26), rgba(217,163,95,0.14))', border: '1px solid rgba(217,163,95,0.24)', borderRadius: 16, padding: 14, marginBottom: 12, color: 'var(--app-porcelain)' }}>
          <p style={{ margin: '0 0 4px', fontSize: 12, color: 'var(--app-amber-soft)' }}>饭搭子计划</p>
          <h4 style={{ margin: '0 0 8px', fontSize: 16 }}>{companion.restaurant_type || '共同口味餐厅'}</h4>
          {companion.invite_text && <p style={{ margin: '0 0 10px', fontSize: 13, lineHeight: 1.6, color: 'rgba(244,232,212,0.84)' }}>{companion.invite_text}</p>}
          <div style={{ display: 'grid', gap: 10 }}>
            {companion.best_scene && (
              <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 12, padding: 10 }}>
                <strong style={{ fontSize: 12 }}>最佳场景</strong>
                <p style={{ margin: '4px 0 0', fontSize: 13, color: 'rgba(244,232,212,0.84)' }}>{companion.best_scene}</p>
              </div>
            )}
            {companion.shared_foods?.length > 0 && (
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {companion.shared_foods.map((food: string) => <span key={food} style={{ fontSize: 12, borderRadius: 999, padding: '4px 9px', background: 'rgba(255,255,255,0.1)' }}>{food}</span>)}
              </div>
            )}
            {companion.avoid?.length > 0 && (
              <div style={{ fontSize: 12, color: 'var(--app-muted)', lineHeight: 1.6 }}>
                {companion.avoid.map((note: string) => <div key={note}>• {note}</div>)}
              </div>
            )}
          </div>
        </section>
      )}

      {data.explanation && (
        <div style={{ background: 'var(--app-surface)', border: '1px solid var(--app-border)', borderRadius: 12, padding: 14, marginBottom: 12, color: 'var(--app-porcelain)' }}>
          <h4 style={{ margin: '0 0 6px', fontSize: 14 }}>匹配解读</h4>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--app-muted)', lineHeight: 1.6 }}>{data.explanation}</p>
        </div>
      )}

      {data.agent_dialogue?.length > 0 && (
        <div style={{ background: 'var(--app-surface)', border: '1px solid var(--app-border)', borderRadius: 12, padding: 14, marginBottom: 12, color: 'var(--app-porcelain)' }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Agent 对话</h4>
          {data.agent_dialogue.map((msg: any, i: number) => (
            <div key={i} style={{ marginBottom: 8, padding: 8, background: msg.agent === 'A' ? 'rgba(217,163,95,0.14)' : 'rgba(36,70,87,0.18)', borderRadius: 8 }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: msg.agent === 'A' ? 'var(--app-amber-soft)' : 'var(--app-smoke)' }}>
                Agent {msg.agent}:
              </span>
              <p style={{ margin: '2px 0 0', fontSize: 12, color: 'rgba(244,232,212,0.84)' }}>{msg.content}</p>
            </div>
          ))}
        </div>
      )}

      {data.joint_recommendation?.length > 0 && (
        <div style={{ background: 'var(--app-surface)', border: '1px solid var(--app-border)', borderRadius: 12, padding: 14, color: 'var(--app-porcelain)' }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>联合推荐</h4>
          {data.joint_recommendation.map((r: any, i: number) => (
            <div key={i} style={{ padding: 8, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <span style={{ fontSize: 14, fontWeight: 500 }}>{r.restaurant}</span>
              <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--app-muted)' }}>{r.reason}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
