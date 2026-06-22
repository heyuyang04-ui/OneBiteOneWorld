import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../services/api'
import BaseChart from '../components/BaseChart'

const dimLabels: Record<string, string> = { spicy: '辣度', sweet: '甜度', sour: '酸度', salty: '咸度', umami: '鲜度', bitter: '苦度' }

export default function CityTrends() {
  const [searchParams] = useSearchParams()
  const city = searchParams.get('city') || 'beijing'
  const [dimension, setDimension] = useState('spicy')
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.get(`/city/trends?city=${city}&dimension=${dimension}`).then(res => {
      setData(res.data.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [city, dimension])

  const trends = Array.isArray(data?.trends) ? data.trends : []
  const hasTrends = trends.length > 0
  const chartOption = hasTrends ? {
    tooltip: { trigger: 'axis' },
    legend: { data: trends.map((t: any) => t.district), bottom: 0, textStyle: { fontSize: 10 } },
    grid: { top: 20, right: 20, bottom: 50, left: 40 },
    xAxis: { type: 'category', data: trends[0]?.weeks || [] },
    yAxis: { type: 'value', min: 0, max: 1 },
    series: trends.map((t: any) => ({
      name: t.district,
      type: 'line',
      smooth: true,
      data: Array.isArray(t.values) ? t.values.map((v: any) => Number(v) || 0) : [],
    })),
  } : {}

  return (
    <div>
      <div style={{ marginBottom: 10 }}>
        <h2 style={{ fontSize: 18, color: 'var(--app-porcelain)', margin: '0 0 4px' }}>城市趋势</h2>
        <p style={{ margin: 0, fontSize: 12, color: 'var(--app-muted)' }}>当前城市：{data?.city_name || city} · {dimLabels[dimension]}</p>
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
        {Object.entries(dimLabels).map(([k, v]) => (
          <button key={k} onClick={() => setDimension(k)}
            style={{ fontSize: 11, padding: '3px 8px', borderRadius: 10, border: 'none', cursor: 'pointer',
              background: dimension === k ? 'var(--app-city-blue)' : 'rgba(244,232,212,0.16)', color: dimension === k ? 'var(--app-porcelain)' : 'var(--app-muted)' }}>
            {v}
          </button>
        ))}
      </div>

      {loading ? <p style={{ textAlign: 'center', color: 'var(--app-amber-soft)', padding: 40 }}>加载中...</p> : (
        <div style={{ background: 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', borderRadius: 12, padding: 10, border: '1px solid rgba(154,99,56,0.14)' }}>
          {hasTrends ? (
            <BaseChart option={chartOption} style={{ height: 240 }} />
          ) : (
            <div style={{ textAlign: 'center', padding: 36, color: 'var(--app-muted-dark)', fontSize: 13 }}>当前城市暂无趋势数据</div>
          )}
        </div>
      )}

      {data?.insights?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <h3 style={{ fontSize: 15, margin: '0 0 8px', color: 'var(--app-porcelain)' }}>Agent 趋势洞察</h3>
          {data.insights.map((ins: any, i: number) => (
            <div key={i} style={{ background: 'rgba(255,251,245,0.86)', border: '1px solid rgba(217,163,95,0.24)', borderRadius: 10, padding: 12, marginBottom: 8 }}>
              <h4 style={{ margin: '0 0 4px', fontSize: 13, color: 'var(--app-wood-deep)' }}>{ins.title}</h4>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--app-muted-dark)', lineHeight: 1.5 }}>{ins.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
