import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import BaseChart from '../components/BaseChart'

const dimLabels: Record<string, string> = { spicy: '辣度', sweet: '甜度', sour: '酸度', salty: '咸度', umami: '鲜度', bitter: '苦度' }

export default function CityMap() {
  const [cities, setCities] = useState<any[]>([])
  const [city, setCity] = useState('beijing')
  const [dimension, setDimension] = useState('spicy')
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/city/cities').then(res => setCities(res.data.data || []))
  }, [])

  useEffect(() => {
    setLoading(true)
    api.get(`/city/heatmap?city=${city}&dimension=${dimension}`).then(res => {
      setData(res.data.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [city, dimension])

  const selectedCityName = cities.find(c => c.id === city)?.name || data?.city_name || city
  const safeRegions = (data?.regions || []).filter((r: any) => (
    Array.isArray(r.center)
    && r.center.length >= 2
    && Number.isFinite(Number(r.center[0]))
    && Number.isFinite(Number(r.center[1]))
    && Number.isFinite(Number(r.value))
  ))
  const sortedRegions = [...safeRegions].sort((a: any, b: any) => Number(b.value) - Number(a.value))

  const chartOption = data ? {
    title: { text: `${data.city_name || city} - ${dimLabels[dimension]}热力图`, left: 'center', textStyle: { fontSize: 14, color: '#2C2118' } },
    tooltip: { trigger: 'item', formatter: (p: any) => {
      const value = p.data?.value?.[2]
      return `${p.name}: ${Math.round(Number(value || 0) * 100)}%`
    } },
    visualMap: { min: 0, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['#F4E8D4', '#D9A35F', '#5C3822'] } },
    series: [{
      type: 'scatter',
      coordinateSystem: 'cartesian2d',
      symbolSize: (val: any) => Math.max(20, Number(val?.[2] || 0) * 60),
      data: safeRegions.map((r: any) => ({ name: r.name, value: [Number(r.center[0]), Number(r.center[1]), Number(r.value)] })),
      label: { show: true, formatter: (p: any) => p.name, fontSize: 11 },
      itemStyle: { color: '#D9A35F' },
    }],
    xAxis: { show: false, min: 'dataMin', max: 'dataMax' },
    yAxis: { show: false, min: 'dataMin', max: 'dataMax' },
    grid: { top: 40, bottom: 50 },
  } : {}

  return (
    <div>
      <div style={{ marginBottom: 10 }}>
        <h2 style={{ margin: '0 0 4px', fontSize: 18, color: 'var(--app-porcelain)' }}>城市味觉地图</h2>
        <p style={{ margin: 0, fontSize: 12, color: 'var(--app-muted)' }}>当前城市：{selectedCityName} · {dimLabels[dimension]}</p>
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
        {cities.map(c => (
          <button key={c.id} onClick={() => setCity(c.id)}
            style={{ fontSize: 11, padding: '3px 8px', borderRadius: 10, border: 'none', cursor: 'pointer',
              background: city === c.id ? 'linear-gradient(135deg, var(--app-wood), var(--app-amber))' : 'rgba(244,232,212,0.16)', color: city === c.id ? '#1C120B' : 'var(--app-muted)' }}>
            {c.name}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
        {Object.entries(dimLabels).map(([k, v]) => (
          <button key={k} onClick={() => setDimension(k)}
            style={{ fontSize: 11, padding: '3px 8px', borderRadius: 10, border: 'none', cursor: 'pointer',
              background: dimension === k ? 'var(--app-city-blue)' : 'rgba(244,232,212,0.16)', color: dimension === k ? 'var(--app-porcelain)' : 'var(--app-muted)' }}>
            {v}
          </button>
        ))}
      </div>

      {loading ? <div style={{ textAlign: 'center', padding: 40, color: 'var(--app-amber-soft)' }}>加载中...</div> : (
        <div style={{ background: 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', borderRadius: 12, padding: 8, border: '1px solid rgba(154,99,56,0.14)' }}>
          {safeRegions.length > 0 ? (
            <BaseChart option={chartOption} style={{ height: 280 }} />
          ) : (
            <div style={{ textAlign: 'center', padding: 38, color: 'var(--app-muted-dark)', fontSize: 13 }}>当前城市暂无可展示的热力区县数据</div>
          )}
        </div>
      )}

      {sortedRegions.length > 0 && (
        <div style={{ marginTop: 12 }}>
          {sortedRegions.map((r: any) => (
            <Link to={`/city/district/${r.id}`} key={r.id} style={{ textDecoration: 'none' }}>
              <div style={{ background: 'linear-gradient(180deg, var(--app-card), var(--app-card-warm))', borderRadius: 8, padding: 10, marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid rgba(154,99,56,0.12)' }}>
                <div>
                  <span style={{ fontSize: 13, color: 'var(--app-text-dark)', fontWeight: 500 }}>{r.name}</span>
                  <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--app-muted-dark)' }}>{r.top_cuisines?.join('·')}</span>
                </div>
                <span style={{ fontSize: 14, fontWeight: 'bold', color: 'var(--app-wood-deep)' }}>{Math.round(Number(r.value) * 100)}%</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
        <Link to={`/city/trends?city=${city}`} style={{ flex: 1, textAlign: 'center', padding: 10, background: 'var(--app-city-blue)', color: 'var(--app-porcelain)', borderRadius: 10, textDecoration: 'none', fontSize: 13 }}>趋势分析</Link>
        <Link to={`/city/recommend?city=${city}`} style={{ flex: 1, textAlign: 'center', padding: 10, background: 'linear-gradient(135deg, var(--app-wood), var(--app-amber))', color: '#1C120B', borderRadius: 10, textDecoration: 'none', fontSize: 13, fontWeight: 800 }}>个性化推荐</Link>
      </div>
    </div>
  )
}
