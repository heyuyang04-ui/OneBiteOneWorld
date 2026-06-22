import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import api from '../services/api'
import ImageUpload from '../components/ImageUpload'
import './Home.css'

type RecommendationItem = {
  name: string
  reason: string
  tags: string[]
}

type RecommendationGroup = {
  type: string
  title: string
  items: RecommendationItem[]
}

type TodayRecommendation = {
  user: {
    id: string
    name: string
    city: string
    occupation: string
  }
  state: {
    title: string
    summary: string
    signals: string[]
  }
  recommendations: RecommendationGroup[]
  quick_actions: string[]
}

const fallbackRecommendation: TodayRecommendation = {
  user: { id: '', name: '你', city: '', occupation: '' },
  state: {
    title: '今日饮食待更新',
    summary: '先记录一餐，系统会根据你的口味画像给出更具体的下一餐建议。',
    signals: ['等待新的饮食记录'],
  },
  recommendations: [
    {
      type: 'preference',
      title: '贴合偏好',
      items: [{ name: '番茄牛腩饭', reason: '兼顾肉类满足感、主食稳定性和轻酸开胃感。', tags: ['均衡', '蛋白质', '日常'] }],
    },
    {
      type: 'balance',
      title: '平衡建议',
      items: [{ name: '鸡汤米线', reason: '鲜味明确，负担更轻，适合工作日快速恢复状态。', tags: ['清爽', '鲜味', '暖胃'] }],
    },
    {
      type: 'explore',
      title: '探索建议',
      items: [{ name: '本地招牌小吃', reason: '从所在城市开始扩展你的味觉地图。', tags: ['城市探索', '尝鲜'] }],
    },
    {
      type: 'social',
      title: '一起吃',
      items: [{ name: '找一个同频饭搭子', reason: '从共同喜欢的菜系开始，降低第一次约饭的决策成本。', tags: ['饭搭子', '共同口味'] }],
    },
  ],
  quick_actions: ['想吃肉', '想吃清淡', '想探索新店', '想找饭搭子'],
}

export default function Home() {
  const [loading, setLoading] = useState(false)
  const [recommendLoading, setRecommendLoading] = useState(true)
  const [recommendation, setRecommendation] = useState<TodayRecommendation>(fallbackRecommendation)
  const [notifications, setNotifications] = useState<any[]>([])
  const [actionFeedback, setActionFeedback] = useState('')
  const [uploadResetKey, setUploadResetKey] = useState(0)
  const [foodDescription, setFoodDescription] = useState('')
  const [pendingImage, setPendingImage] = useState('')
  const [recognitionError, setRecognitionError] = useState('')
  const [manualOpen, setManualOpen] = useState(false)
  const [manualSaving, setManualSaving] = useState(false)
  const [manualMeal, setManualMeal] = useState({ dish_name: '', cuisine_type: '', ingredients: '' })
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/recommend/today').then(res => {
      if (res.data.success && res.data.data) {
        setRecommendation(res.data.data)
      }
    }).catch(() => {
      setRecommendation(fallbackRecommendation)
    }).finally(() => {
      setRecommendLoading(false)
    })

    api.get('/notifications?unread_only=true').then(res => {
      setNotifications(res.data.data || [])
    }).catch(() => {})
  }, [])

  const handleQuickAction = (action: string) => {
    const feedbackMap: Record<string, string> = {
      '想吃肉': 'Agent 已收到：下一餐会优先考虑高满足感和蛋白质更充足的选择。',
      '想吃清淡': 'Agent 已收到：下一餐会降低油盐和重口信号，偏向清爽鲜味。',
      '想探索新店': 'Agent 已收到：会从你的城市味觉地图里寻找更有探索感的餐厅。',
      '想找饭搭子': 'Agent 已收到：可以去“发现”页看看与你口味同频的人。',
    }
    setActionFeedback(feedbackMap[action] || `Agent 已记录你的意图：${action}`)
  }

  const handleImageReady = (base64: string) => {
    setPendingImage(base64)
    setRecognitionError('')
  }

  const resetSelectedImage = () => {
    setPendingImage('')
    setRecognitionError('')
    setManualOpen(false)
    setUploadResetKey(prev => prev + 1)
  }

  const handleConfirmRecognition = async () => {
    if (!pendingImage || loading) return
    setLoading(true)
    setRecognitionError('')
    try {
      const res = await api.post('/meals', { image: pendingImage, description: foodDescription.trim() })
      if (!res.data.success) {
        setRecognitionError(res.data.error?.message || '上传失败，请重试，或手动补录这一餐。')
        return
      }
      if (res.data.data?.is_food === false) {
        setRecognitionError(res.data.data.message || '未识别到食物。你可以重试、换一张图，或手动补录这一餐。')
        setManualOpen(true)
        return
      }
      const meal = res.data.data?.meal
      if (!meal?.id) {
        setRecognitionError('识别结果异常，请重试，或手动补录这一餐。')
        return
      }
      navigate(`/meal/${meal.id}`, { state: res.data.data })
    } catch (e) {
      setRecognitionError('识别失败，请检查网络后重试，或手动补录这一餐。')
    } finally {
      setLoading(false)
    }
  }

  const handleManualSave = async () => {
    if (manualSaving) return
    const dishName = manualMeal.dish_name.trim()
    if (!dishName) {
      setRecognitionError('手动补录需要填写菜名。')
      return
    }

    setManualSaving(true)
    setRecognitionError('')
    try {
      const ingredients = manualMeal.ingredients
        .split(/[，,\n]/)
        .map(item => item.trim())
        .filter(Boolean)
      const res = await api.post('/meals/manual', {
        dish_name: dishName,
        cuisine_type: manualMeal.cuisine_type.trim(),
        ingredients,
        description: foodDescription.trim(),
        image: pendingImage || undefined,
      })
      if (!res.data.success) {
        setRecognitionError(res.data.error?.message || '手动保存失败，请检查填写内容。')
        return
      }
      const meal = res.data.data?.meal
      if (!meal?.id) {
        setRecognitionError('手动保存结果异常，请重试。')
        return
      }
      navigate(`/meal/${meal.id}`, { state: res.data.data })
    } catch (e) {
      setRecognitionError('手动保存失败，请稍后重试。')
    } finally {
      setManualSaving(false)
    }
  }

  return (
    <div className="home-page">
      <div className="taste-atmosphere" aria-hidden="true">
        <span className="taste-orbit taste-orbit-a" />
        <span className="taste-orbit taste-orbit-b" />
        <span className="taste-pulse" />
      </div>
      <motion.section
        className="today-hero"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      >
        <div>
          <p className="home-eyebrow">今日饮食状态</p>
          <h2>{recommendation.user.name}，今天适合这样吃</h2>
          <p className="hero-summary">{recommendLoading ? '正在读取你的口味状态...' : recommendation.state.summary}</p>
        </div>
        <div className="state-pill">{recommendation.state.title}</div>
      </motion.section>

      <motion.section
        className="signal-card"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="signal-title">系统看到的口味信号</div>
        <div className="signal-list">
          {recommendation.state.signals.map(signal => (
            <span key={signal}>{signal}</span>
          ))}
        </div>
      </motion.section>

      <motion.section
        className="quick-actions"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.42, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
      >
        {recommendation.quick_actions.map(action => (
          <button key={action} type="button" onClick={() => handleQuickAction(action)}>{action}</button>
        ))}
      </motion.section>
      <AnimatePresence>
        {actionFeedback && (
          <motion.p
            className="loading-text"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.22 }}
          >
            {actionFeedback}
          </motion.p>
        )}
      </AnimatePresence>

      <motion.section
        className="recommendations-panel"
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.48, delay: 0.16, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="section-heading">
          <p>今天吃什么</p>
          <span>不是只记录，也帮你做选择</span>
        </div>
        {(recommendation.recommendations || []).map((group, groupIndex) => (
          <motion.div
            className="recommend-group"
            key={group.type || group.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.36, delay: 0.2 + groupIndex * 0.05, ease: [0.22, 1, 0.36, 1] }}
          >
            <h3>{group.title || '推荐'}</h3>
            <div className="recommend-list">
              {(group.items || []).map(item => (
                <article className="recommend-card" key={`${group.type}-${item.name}`}>
                  <div>
                    <h4>{item.name}</h4>
                    <p>{item.reason || '基于你的口味画像生成的建议。'}</p>
                  </div>
                  <div className="recommend-tags">
                    {(item.tags || []).map(tag => <span key={tag}>{tag}</span>)}
                  </div>
                </article>
              ))}
            </div>
          </motion.div>
        ))}
      </motion.section>

      <section className="record-section">
        <div className="section-heading">
          <p>记录这一餐</p>
          <span>上传后系统会结合照片和你的描述更新味觉画像</span>
        </div>
        <div className="food-description-box">
          <label htmlFor="food-description">补充描述（可选）</label>
          <textarea
            id="food-description"
            value={foodDescription}
            onChange={(e) => setFoodDescription(e.target.value)}
            maxLength={200}
            placeholder="例如：黄焖鸡米饭，加了土豆和青椒；或番茄牛腩面，少辣，多肉"
            disabled={loading}
          />
          <span>{foodDescription.length}/200</span>
        </div>
        <ImageUpload onImageReady={handleImageReady} loading={loading} resetKey={uploadResetKey} />
        <div className="recognition-actions">
          <button
            type="button"
            className="confirm-recognition-btn"
            disabled={!pendingImage || loading || manualSaving}
            onClick={handleConfirmRecognition}
          >
            {loading ? 'Agent 正在识别...' : pendingImage ? '确认识别这一餐' : '请先选择照片'}
          </button>
          {pendingImage && !loading && <button type="button" className="change-photo-btn" onClick={resetSelectedImage}>重新选择照片</button>}
        </div>
        {loading && <p className="loading-text">Agent 正在结合照片和描述分析你的食物...</p>}
        {recognitionError && (
          <div className="recognition-fallback-card">
            <strong>这一餐还没有记录成功</strong>
            <p>{recognitionError}</p>
            <div className="fallback-actions">
              <button type="button" onClick={handleConfirmRecognition} disabled={!pendingImage || loading || manualSaving}>重试当前照片</button>
              <button type="button" onClick={() => setManualOpen(prev => !prev)} disabled={loading || manualSaving}>
                {manualOpen ? '收起手动补录' : '手动补录这一餐'}
              </button>
              <button type="button" onClick={resetSelectedImage} disabled={loading || manualSaving}>更换图片</button>
            </div>
          </div>
        )}
        {manualOpen && (
          <div className="manual-meal-form">
            <label>
              菜名
              <input
                value={manualMeal.dish_name}
                onChange={(e) => setManualMeal(prev => ({ ...prev, dish_name: e.target.value }))}
                placeholder="例如：番茄牛腩饭"
                disabled={manualSaving}
              />
            </label>
            <label>
              菜系/类型
              <input
                value={manualMeal.cuisine_type}
                onChange={(e) => setManualMeal(prev => ({ ...prev, cuisine_type: e.target.value }))}
                placeholder="例如：家常菜、川菜、日料"
                disabled={manualSaving}
              />
            </label>
            <label>
              主要食材
              <textarea
                value={manualMeal.ingredients}
                onChange={(e) => setManualMeal(prev => ({ ...prev, ingredients: e.target.value }))}
                placeholder="用逗号或换行分隔，例如：牛腩，番茄，米饭"
                disabled={manualSaving}
              />
            </label>
            <button type="button" className="manual-save-btn" onClick={handleManualSave} disabled={manualSaving || loading}>
              {manualSaving ? '正在保存...' : '保存为我的一餐'}
            </button>
          </div>
        )}
      </section>

      {notifications.length > 0 && (
        <div className="notifications-preview">
          <h3>Agent 消息</h3>
          {notifications.slice(0, 3).map(n => (
            <div key={n.id} className="notif-card">
              <span className="notif-type">{n.type === 'reasoning' ? '💡' : '📢'}</span>
              <div>
                <p className="notif-title">{n.title}</p>
                <p className="notif-content">{n.content?.slice(0, 60)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
