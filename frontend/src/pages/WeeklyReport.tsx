import { useState, useEffect } from 'react'
import api from '../services/api'
import './WeeklyReport.css'

const riskLabel: Record<string, string> = {
  low: '状态稳定',
  medium: '需要留意',
  high: '建议调整',
  unknown: '等待记录',
}

export default function WeeklyReport() {
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [displayed, setDisplayed] = useState('')
  const [feedbackStatus, setFeedbackStatus] = useState<Record<string, string>>({})

  useEffect(() => {
    api.get('/report/weekly').then(res => {
      setReport(res.data.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!report?.summary) return
    let i = 0
    const timer = setInterval(() => {
      setDisplayed(report.summary.slice(0, i + 1))
      i++
      if (i >= report.summary.length) clearInterval(timer)
    }, 30)
    return () => clearInterval(timer)
  }, [report?.summary])

  const submitFeedback = (insightId: string, accurate: boolean) => {
    setFeedbackStatus(prev => ({ ...prev, [insightId]: '提交中...' }))
    api.post('/report/feedback', { insight_id: insightId, accurate }).then(res => {
      setFeedbackStatus(prev => ({ ...prev, [insightId]: res.data.success ? '已记录反馈' : '反馈提交失败' }))
    }).catch(() => {
      setFeedbackStatus(prev => ({ ...prev, [insightId]: '反馈提交失败' }))
    })
  }

  if (loading) return <div className="weekly-loading">Agent 正在生成周报...</div>

  const health = report?.health_insight
  const mood = report?.mood_insight

  return (
    <div className="weekly-report">
      <h2>味觉周报</h2>

      {report?.summary && (
        <section className="report-summary-card">
          <p>{displayed}<span style={{ opacity: displayed.length < (report?.summary?.length || 0) ? 1 : 0 }}>|</span></p>
        </section>
      )}

      {health && (
        <section className="insight-card health-card">
          <div className="insight-header">
            <div>
              <p className="insight-kicker">健康 / 生活方式信号</p>
              <h3>本周饮食状态</h3>
            </div>
            <div className={`score-badge ${health.risk_level || 'unknown'}`}>
              <strong>{health.health_score}</strong>
              <span>{riskLabel[health.risk_level] || '状态观察'}</span>
            </div>
          </div>

          <div className="metric-grid">
            <div><strong>{health.metrics?.meal_count ?? 0}</strong><span>记录餐数</span></div>
            <div><strong>{health.metrics?.avg_calories ?? 0}</strong><span>平均千卡</span></div>
            <div><strong>{health.metrics?.late_night_count ?? 0}</strong><span>夜间餐</span></div>
            <div><strong>{health.metrics?.heavy_taste_count ?? 0}</strong><span>重口餐</span></div>
          </div>

          {health.signals?.length > 0 && (
            <div className="signal-list-report">
              {health.signals.map((signal: any) => (
                <div className="signal-report-item" key={signal.type}>
                  <strong>{signal.title}</strong>
                  <p>{signal.description}</p>
                </div>
              ))}
            </div>
          )}

          {health.suggestions?.length > 0 && (
            <div className="suggestion-list">
              <h4>下周可以这样调整</h4>
              {health.suggestions.map((item: string) => <p key={item}>{item}</p>)}
            </div>
          )}
        </section>
      )}

      {mood && (
        <section className="insight-card mood-card">
          <div className="insight-header">
            <div>
              <p className="insight-kicker">饮食自传线索</p>
              <h3>{mood.state}</h3>
            </div>
            <div className="confidence-badge">{Math.round((mood.confidence || 0) * 100)}%</div>
          </div>
          <p className="mood-reflection">{mood.reflection}</p>
          {mood.evidence?.length > 0 && (
            <div className="evidence-list">
              {mood.evidence.map((item: string) => <span key={item}>{item}</span>)}
            </div>
          )}
          {mood.question && <div className="reflection-question">{mood.question}</div>}
        </section>
      )}

      {report?.highlights?.map((h: any, i: number) => {
        const insightId = h.id || `h_${i}`
        return (
          <section key={insightId} className="highlight-card">
            <h4>💡 {h.title}</h4>
            <p>{h.content}</p>
            <div className="feedback-row">
              <button onClick={() => submitFeedback(insightId, true)}>准确 ✓</button>
              <button onClick={() => submitFeedback(insightId, false)}>不准确 ✗</button>
            </div>
            {feedbackStatus[insightId] && <p style={{ margin: '8px 0 0', fontSize: 12, color: 'var(--app-muted-dark)' }}>{feedbackStatus[insightId]}</p>}
          </section>
        )
      })}

      {report?.reflection && (
        <section className="final-reflection">
          <p>🌟 {report.reflection}</p>
        </section>
      )}
    </div>
  )
}
