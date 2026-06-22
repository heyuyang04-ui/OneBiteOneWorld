import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import api from '../services/api'
import './MealResult.css'

const dimLabels: Record<string, string> = {
  spicy: '辣', sweet: '甜', sour: '酸', salty: '咸', umami: '鲜', bitter: '苦'
}

const dimDescriptions: Record<string, string> = {
  spicy: '提升你对辣味和刺激感的接受度',
  sweet: '强化甜口、柔和和愉悦感偏好',
  sour: '增加酸爽、开胃和清新感信号',
  salty: '强化咸香、下饭和重口满足感',
  umami: '强化肉类、汤底和鲜味满足感',
  bitter: '增加茶感、烘焙或复杂风味信号',
}

function toDisplayNumber(value: unknown) {
  const text = String(value ?? '')
  const match = text.match(/-?\d+(?:\.\d+)?/)
  return match ? Number(match[0]) : 0
}

function topTasteTags(tags: Record<string, number> = {}) {
  return Object.entries(tags)
    .map(([key, value]) => [key, Number(value) || 0] as [string, number])
    .filter(([, value]) => value > 0.05)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2)
}

function imageDataUrl(image: string, mime = 'image/jpeg') {
  return `data:${mime || 'image/jpeg'};base64,${image}`
}

export default function MealResult() {
  const { id } = useParams()
  const { state } = useLocation() as { state: any }
  const [meal, setMeal] = useState<any>(state?.meal || null)
  const [insight] = useState(state?.micro_insight || '')
  const [loading, setLoading] = useState(!state?.meal)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [savingEdit, setSavingEdit] = useState(false)
  const [editError, setEditError] = useState('')
  const [editMeal, setEditMeal] = useState({ dish_name: '', cuisine_type: '', ingredients: '' })

  useEffect(() => {
    if (meal || !id) return
    setLoading(true)
    api.get(`/meals/${id}`).then(res => {
      if (res.data.success) {
        setMeal(res.data.data)
      } else {
        setError('未找到这餐记录')
      }
    }).catch(() => {
      setError('加载餐食详情失败')
    }).finally(() => {
      setLoading(false)
    })
  }, [id, meal])

  useEffect(() => {
    if (!meal?.id || meal.image) return
    api.get(`/meals/${meal.id}/image`).then(res => {
      const image = res.data.data?.image
      const mimeType = res.data.data?.mime_type
      if (res.data.success && image) {
        setMeal((prev: any) => prev ? { ...prev, image, image_mime: mimeType || prev.image_mime } : prev)
      }
    }).catch(() => {})
  }, [meal?.id, meal?.image])

  useEffect(() => {
    if (!meal?.id) return
    setEditMeal({
      dish_name: meal.dish_name || '',
      cuisine_type: meal.cuisine_type || '',
      ingredients: (meal.ingredients || []).join('，'),
    })
  }, [meal?.id, meal?.dish_name, meal?.cuisine_type, meal?.ingredients])

  const visibleTasteTags = useMemo(() => Object.entries(meal?.taste_tags || {})
    .map(([key, value]) => [key, Number(value) || 0] as [string, number])
    .filter(([, value]) => value > 0.05), [meal])
  const impactTags = useMemo(() => topTasteTags(meal?.taste_tags), [meal])

  const handleSaveCorrection = async () => {
    if (!meal?.id || savingEdit) return
    const dishName = editMeal.dish_name.trim()
    if (!dishName) {
      setEditError('菜名不能为空')
      return
    }

    setSavingEdit(true)
    setEditError('')
    try {
      const ingredients = editMeal.ingredients
        .split(/[，,\n]/)
        .map(item => item.trim())
        .filter(Boolean)
      const res = await api.put(`/meals/${meal.id}`, {
        dish_name: dishName,
        cuisine_type: editMeal.cuisine_type.trim(),
        ingredients,
        taste_tags: meal.taste_tags || undefined,
        nutrition: meal.nutrition || undefined,
      })
      if (!res.data.success) {
        setEditError(res.data.error?.message || '保存失败，请重试')
        return
      }
      const updated = res.data.data?.meal
      if (updated) {
        setMeal((prev: any) => ({ ...prev, ...updated, image: updated.image || prev?.image }))
        setEditing(false)
      }
    } catch (e) {
      setEditError('保存失败，请稍后重试')
    } finally {
      setSavingEdit(false)
    }
  }

  const nextSuggestions = useMemo(() => {
    const tags = meal?.taste_tags || {}
    if ((tags.umami || 0) >= 0.65 || (tags.salty || 0) >= 0.65) {
      return [
        { title: '继续满足', text: '如果下一餐还想吃肉，可以选烤鱼、牛肉饭或铜锅涮肉。' },
        { title: '降低疲劳', text: '搭配蔬菜、汤品或酸爽小菜，减少连续重口带来的口味疲劳。' },
      ]
    }
    if ((tags.spicy || 0) >= 0.6) {
      return [
        { title: '延续重口', text: '下一餐可以选择香辣烤鱼或小火锅，延续辣味满足感。' },
        { title: '平衡一下', text: '如果感觉口腔负担较重，可以选番茄牛腩、鸡汤米线或清爽饭食。' },
      ]
    }
    return [
      { title: '稳定选择', text: '下一餐可以选择番茄牛腩饭、鸡汤米线或轻食饭，保持稳定能量。' },
      { title: '探索选择', text: '如果想增加变化，可以尝试一个与你常吃菜系相近的新风味。' },
    ]
  }, [meal])

  const agentTrace = Array.isArray(state?.agent_trace)
    ? state.agent_trace
    : Array.isArray(meal?.agent_trace)
      ? meal.agent_trace
      : []

  if (loading) return <div className="meal-result"><div className="result-state-card">正在加载这餐记录...</div></div>

  if (error || !meal?.dish_name) {
    return (
      <div className="meal-result">
        <div className="result-state-card">
          <h3>{error || '暂无数据'}</h3>
          <p>可以返回首页重新记录，或从历史记录中打开已有餐食。</p>
          <div className="result-actions">
            <Link to="/home">回到首页</Link>
            <Link to="/history">查看历史</Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="meal-result">
      <div className="result-card">
        {meal.image && <img className="meal-photo" src={imageDataUrl(meal.image, meal.image_mime || meal.mime_type)} alt={meal.dish_name} />}
        <div className="result-header">
          <div>
            <p className="result-eyebrow">本餐识别结果</p>
            <h2>{meal.dish_name}</h2>
          </div>
          <span className="cuisine-badge">{meal.cuisine_type}</span>
        </div>

        <div className="taste-tags">
          {visibleTasteTags.length > 0 ? visibleTasteTags.map(([k, v]) => (
            <div key={k} className="taste-item">
              <span className="taste-label">{dimLabels[k] || k}</span>
              <div className="taste-bar"><div className="taste-fill" style={{ width: `${v * 100}%` }} /></div>
              <span className="taste-value">{Math.round(v * 100)}%</span>
            </div>
          )) : <p className="muted-text">这餐口味信号较均衡，暂无突出维度。</p>}
        </div>

        {meal.nutrition && (
          <div className="nutrition">
            <h4>营养估算</h4>
            <div className="nutrition-grid">
              <div><span>{Math.round(toDisplayNumber(meal.nutrition.calories))}</span><small>千卡</small></div>
              <div><span>{Math.round(toDisplayNumber(meal.nutrition.protein))}g</span><small>蛋白质</small></div>
              <div><span>{Math.round(toDisplayNumber(meal.nutrition.carbs))}g</span><small>碳水</small></div>
              <div><span>{Math.round(toDisplayNumber(meal.nutrition.fat))}g</span><small>脂肪</small></div>
            </div>
          </div>
        )}

        {meal.ingredients?.length > 0 && (
          <div className="ingredients">
            <h4>食材</h4>
            <div className="ingredient-tags">
              {meal.ingredients.map((ing: string) => <span key={ing} className="ing-tag">{ing}</span>)}
            </div>
          </div>
        )}

        <div className="correction-entry">
          <button type="button" onClick={() => setEditing(prev => !prev)}>
            {editing ? '收起纠错' : '纠正这一餐'}
          </button>
          <p>如果识别结果不准确，纠正后会同步更新你的味觉画像。</p>
        </div>

        {editing && (
          <div className="correction-panel">
            <label>
              菜名
              <input
                value={editMeal.dish_name}
                onChange={(e) => setEditMeal(prev => ({ ...prev, dish_name: e.target.value }))}
                disabled={savingEdit}
              />
            </label>
            <label>
              菜系/类型
              <input
                value={editMeal.cuisine_type}
                onChange={(e) => setEditMeal(prev => ({ ...prev, cuisine_type: e.target.value }))}
                disabled={savingEdit}
              />
            </label>
            <label>
              食材
              <textarea
                value={editMeal.ingredients}
                onChange={(e) => setEditMeal(prev => ({ ...prev, ingredients: e.target.value }))}
                placeholder="用逗号或换行分隔"
                disabled={savingEdit}
              />
            </label>
            {editError && <p className="correction-error">{editError}</p>}
            <button type="button" className="save-correction-btn" onClick={handleSaveCorrection} disabled={savingEdit}>
              {savingEdit ? '正在保存...' : '保存纠正'}
            </button>
          </div>
        )}
      </div>

      <section className="impact-card">
        <h3>这餐如何影响你的口味画像</h3>
        {impactTags.length > 0 ? (
          <div className="impact-list">
            {impactTags.map(([key, value]) => (
              <div key={key} className="impact-item">
                <strong>{dimLabels[key] || key}味信号 +{Math.round(value * 100)}%</strong>
                <p>{dimDescriptions[key] || '这会成为系统理解你口味偏好的一个新信号。'}</p>
              </div>
            ))}
          </div>
        ) : <p className="muted-text">这餐会作为新的记录，参与后续画像更新。</p>}
      </section>

      <section className="next-card">
        <h3>下一餐建议</h3>
        <div className="next-grid">
          {nextSuggestions.map(item => (
            <div key={item.title} className="next-item">
              <strong>{item.title}</strong>
              <p>{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      {agentTrace.length > 0 && (
        <section className="agent-trace-card">
          <h3>Agent 本次做了什么</h3>
          <div className="agent-trace-list">
            {agentTrace.map((item: any, index: number) => {
              const skills = Array.isArray(item.skills) ? item.skills.filter(Boolean) : []
              return (
                <div className="agent-trace-item" key={`${item.event_type || 'event'}-${item.agent || 'agent'}-${index}`}>
                  <strong>{item.agent || 'agent'} · {item.event_type || 'event'}</strong>
                  <p>
                    调用能力：{skills.length > 0 ? skills.join('、') : '未调用额外 Skill'}
                    {typeof item.follow_up_count === 'number' ? `；后续事件 ${item.follow_up_count} 个` : ''}
                  </p>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {insight && <div className="micro-insight"><span>💡</span><p>{insight}</p></div>}
    </div>
  )
}
