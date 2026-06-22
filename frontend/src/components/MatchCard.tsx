import { motion, useMotionValue, useTransform } from 'framer-motion'
import './MatchCard.css'

interface MatchCardProps {
  user: { name: string; city: string; age: number; occupation: string; tags: string[] }
  score: number
  common: string[]
  diff: string[]
  explanation?: string
  why_recommended?: string
  first_meal_suggestion?: string
  conversation_starter?: string
  onLike: () => void
  onSkip: () => void
}

const dimLabels: Record<string, string> = {
  spicy: '辣', sweet: '甜', sour: '酸', salty: '咸', umami: '鲜', bitter: '苦'
}

export default function MatchCard({ user, score, common, diff, explanation, why_recommended, first_meal_suggestion, conversation_starter, onLike, onSkip }: MatchCardProps) {
  const x = useMotionValue(0)
  const rotate = useTransform(x, [-200, 200], [-15, 15])
  const likeOpacity = useTransform(x, [0, 100], [0, 1])
  const skipOpacity = useTransform(x, [-100, 0], [1, 0])

  const handleDragEnd = (_: any, info: any) => {
    if (info.offset.x > 100) onLike()
    else if (info.offset.x < -100) onSkip()
  }

  return (
    <motion.div
      className="match-card"
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      style={{ x, rotate }}
      onDragEnd={handleDragEnd}
      whileTap={{ scale: 1.02 }}
    >
      <motion.div className="like-indicator" style={{ opacity: likeOpacity }}>Match!</motion.div>
      <motion.div className="skip-indicator" style={{ opacity: skipOpacity }}>Skip</motion.div>

      <div className="card-header">
        <div className="avatar">{user.name[0]}</div>
        <div className="user-info">
          <h3>{user.name}</h3>
          <p>{user.age}岁 · {user.city} · {user.occupation}</p>
        </div>
        <div className="score">{Math.round(score * 100)}%</div>
      </div>

      <div className="card-tags">
        {user.tags.map(t => <span key={t} className="tag">{t}</span>)}
      </div>

      <div className="card-match-info">
        {common.length > 0 && (
          <div className="common">
            <span className="label">共同点</span>
            {common.map(c => <span key={c} className="dim-tag common-tag">{dimLabels[c] || c}</span>)}
          </div>
        )}
        {diff.length > 0 && (
          <div className="diff">
            <span className="label">差异</span>
            {diff.map(d => <span key={d} className="dim-tag diff-tag">{dimLabels[d] || d}</span>)}
          </div>
        )}
      </div>

      {explanation && <p className="explanation">{explanation}</p>}

      {(why_recommended || first_meal_suggestion || conversation_starter) && (
        <div className="agent-match-advice">
          {why_recommended && (
            <div>
              <span>为什么推荐</span>
              <p>{why_recommended}</p>
            </div>
          )}
          {first_meal_suggestion && (
            <div>
              <span>第一餐建议</span>
              <p>{first_meal_suggestion}</p>
            </div>
          )}
          {conversation_starter && (
            <div>
              <span>开场问题</span>
              <p>{conversation_starter}</p>
            </div>
          )}
        </div>
      )}
    </motion.div>
  )
}
