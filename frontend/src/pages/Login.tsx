import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import heroImage from '../assets/hero.png'
import './Login.css'

const HERO_USERS = [
  { id: 'user_01', name: '尤若川', subtitle: '程序员 · 北京', desc: '外卖续命三年，想看看自己到底吃了什么', emoji: '💻' },
  { id: 'user_bowen', name: 'Bowen', subtitle: '程序员 · 北京', desc: '无肉不欢的代码诗人，用烤肉香气犒劳每一个加班夜', emoji: '🥩' },
  { id: 'user_02', name: '於书川', subtitle: '设计师 · 上海', desc: '刚搬到新城市，想找属于自己口味的餐厅', emoji: '🎨' },
  { id: 'user_03', name: '傅知遥', subtitle: '大学生 · 成都', desc: '把吃当作探索世界的入口', emoji: '🌶️' },
]

type AuthMode = 'entry' | 'login' | 'register'
type LoginMethod = 'demo' | 'phone'

type RegisterForm = {
  phone: string
  name: string
  city: string
  age: string
  occupation: string
  favorite_foods: string
  spice_level: string
  sweet_level: string
  meat_level: string
  dining_scene: string
}

const initialRegisterForm: RegisterForm = {
  phone: '',
  name: '',
  city: 'beijing',
  age: '25',
  occupation: '程序员',
  favorite_foods: '',
  spice_level: 'medium',
  sweet_level: 'medium',
  meat_level: 'medium',
  dining_scene: 'daily',
}

export default function Login() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState('')
  const [loading, setLoading] = useState(false)
  const users = HERO_USERS
  const [mode, setMode] = useState<AuthMode>('entry')
  const [loginMethod, setLoginMethod] = useState<LoginMethod>('demo')
  const [phone, setPhone] = useState('')
  const [registerForm, setRegisterForm] = useState<RegisterForm>(initialRegisterForm)
  const [error, setError] = useState('')
  const savedUserId = localStorage.getItem('currentUserId')
  const savedUser = HERO_USERS.find(user => user.id === savedUserId)


  const persistSession = (data: any) => {
    localStorage.setItem('currentUserId', data.user_id)
    if (data.session_id) {
      localStorage.setItem('sessionId', data.session_id)
    }
    navigate('/home', { replace: true })
  }

  const handleDemoLogin = async () => {
    if (!selected) return
    setLoading(true)
    setError('')
    try {
      const res = await api.put('/users/me/switch', { user_id: selected })
      if (!res.data.success) {
        setError(res.data.error?.message || '登录失败')
        return
      }
      persistSession(res.data.data)
    } catch {
      setError('登录失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handlePhoneLogin = async () => {
    if (!phone.trim()) {
      setError('请输入手机号码')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await api.post('/auth/phone-login', { phone })
      if (!res.data.success) {
        setError('该手机号还未注册，请先注册')
        return
      }
      persistSession(res.data.data)
    } catch {
      setError('手机号登录失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!registerForm.phone.trim() || !registerForm.name.trim()) {
      setError('请填写手机号和姓名')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await api.post('/auth/register', registerForm)
      if (!res.data.success) {
        setError(res.data.error?.message || '注册失败')
        return
      }
      persistSession(res.data.data)
    } catch {
      setError('注册失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const updateRegisterForm = (key: keyof RegisterForm, value: string) => {
    setRegisterForm(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="login-page">
      <section className="login-panel">
        <div className="hero-visual">
          <img src={heroImage} alt="一食万象品牌视觉" />
          <div className="hero-glow" />
        </div>

        <div className="login-logo">
          <p className="brand-kicker">Agent Taste Intelligence</p>
          <h1>一食万象</h1>
          <p>One Bite, One World</p>
        </div>

        <p className="login-slogan">
          一箪食中遇自己，一味之间找彼此，一城烟火见众生。
        </p>

        {savedUser && mode === 'entry' && (
          <div className="saved-identity">
            已保存上次身份：<strong>{savedUser.name}</strong>。你可以继续登录，也可以切换身份。
          </div>
        )}

        {error && <div className="form-error">{error}</div>}

        {mode === 'entry' && (
          <div className="auth-choice-grid">
            <button type="button" className="auth-choice primary" onClick={() => { setMode('login'); setError('') }}>
              <span>登录</span>
              <small>选择体验用户，或使用手机号登录</small>
            </button>
            <button type="button" className="auth-choice" onClick={() => { setMode('register'); setError('') }}>
              <span>注册</span>
              <small>填写信息，AI 生成你的初始味觉画像</small>
            </button>
          </div>
        )}

        {mode === 'login' && (
          <div className="role-section">
            <button type="button" className="back-entry" onClick={() => { setMode('entry'); setSelected(''); setError('') }}>
              ← 返回登录 / 注册
            </button>
            <p className="role-title">登录一食万象</p>
            <p className="role-subtitle">可以选择体验用户快速进入，也可以用已注册手机号登录。</p>

            <div className="method-tabs">
              <button className={loginMethod === 'demo' ? 'active' : ''} type="button" onClick={() => { setLoginMethod('demo'); setError('') }}>体验用户</button>
              <button className={loginMethod === 'phone' ? 'active' : ''} type="button" onClick={() => { setLoginMethod('phone'); setError('') }}>手机号登录</button>
            </div>

            {loginMethod === 'demo' ? (
              <>
                <div className="role-list">
                  {users.map(u => (
                    <button
                      key={u.id}
                      type="button"
                      onClick={() => setSelected(u.id)}
                      className={`role-card ${selected === u.id ? 'selected' : ''}`}
                    >
                      <span className="role-emoji">{u.emoji}</span>
                      <span className="role-content">
                        <strong>{u.name}</strong>
                        <small>{u.subtitle}</small>
                        <em>{u.desc}</em>
                      </span>
                      <span className="role-check">{selected === u.id ? '✓' : ''}</span>
                    </button>
                  ))}
                </div>
                <button onClick={handleDemoLogin} disabled={!selected || loading} className="login-submit">
                  {loading ? '正在进入...' : '登录并进入'}
                </button>
              </>
            ) : (
              <div className="auth-form">
                <label>
                  <span>手机号码</span>
                  <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="请输入注册手机号" inputMode="tel" />
                </label>
                <button onClick={handlePhoneLogin} disabled={loading} className="login-submit">
                  {loading ? '正在登录...' : '手机号登录'}
                </button>
              </div>
            )}
          </div>
        )}

        {mode === 'register' && (
          <div className="role-section register-section">
            <button type="button" className="back-entry" onClick={() => { setMode('entry'); setError('') }}>
              ← 返回登录 / 注册
            </button>
            <p className="role-title">创建你的味觉画像</p>
            <p className="role-subtitle">填写基础信息后，AI 会为你匹配初始标签和口味向量。</p>

            <div className="auth-form register-form">
              <label>
                <span>手机号码</span>
                <input value={registerForm.phone} onChange={e => updateRegisterForm('phone', e.target.value)} placeholder="用于下次登录" inputMode="tel" />
              </label>
              <label>
                <span>姓名</span>
                <input value={registerForm.name} onChange={e => updateRegisterForm('name', e.target.value)} placeholder="例如 Bowen" />
              </label>
              <label>
                <span>城市</span>
                <select value={registerForm.city} onChange={e => updateRegisterForm('city', e.target.value)}>
                  <option value="beijing">北京</option>
                  <option value="shanghai">上海</option>
                  <option value="chengdu">成都</option>
                  <option value="guangzhou">广州</option>
                </select>
              </label>
              <label>
                <span>年龄</span>
                <input value={registerForm.age} onChange={e => updateRegisterForm('age', e.target.value)} inputMode="numeric" />
              </label>
              <label>
                <span>职业</span>
                <input value={registerForm.occupation} onChange={e => updateRegisterForm('occupation', e.target.value)} placeholder="例如 程序员" />
              </label>
              <label>
                <span>爱吃什么</span>
                <textarea value={registerForm.favorite_foods} onChange={e => updateRegisterForm('favorite_foods', e.target.value)} placeholder="例如 烤肉、牛排、火锅、日料" />
              </label>
              <label>
                <span>吃辣程度</span>
                <select value={registerForm.spice_level} onChange={e => updateRegisterForm('spice_level', e.target.value)}>
                  <option value="low">不太能吃辣</option>
                  <option value="medium">中等</option>
                  <option value="high">很能吃辣</option>
                </select>
              </label>
              <label>
                <span>甜口偏好</span>
                <select value={registerForm.sweet_level} onChange={e => updateRegisterForm('sweet_level', e.target.value)}>
                  <option value="low">不爱甜</option>
                  <option value="medium">中等</option>
                  <option value="high">喜欢甜口</option>
                </select>
              </label>
              <label>
                <span>肉食偏好</span>
                <select value={registerForm.meat_level} onChange={e => updateRegisterForm('meat_level', e.target.value)}>
                  <option value="low">偏清淡少肉</option>
                  <option value="medium">正常</option>
                  <option value="high">无肉不欢</option>
                </select>
              </label>
              <label>
                <span>常见用餐场景</span>
                <select value={registerForm.dining_scene} onChange={e => updateRegisterForm('dining_scene', e.target.value)}>
                  <option value="daily">日常工作餐</option>
                  <option value="work_overtime">加班晚餐/夜宵</option>
                  <option value="social">朋友聚餐/探店</option>
                  <option value="fitness">控卡健身</option>
                </select>
              </label>
            </div>

            <button onClick={handleRegister} disabled={loading} className="login-submit">
              {loading ? 'AI 正在生成画像...' : '注册并生成画像'}
            </button>
          </div>
        )}

        <p className="login-footer">Agent 驱动的城市味觉感知系统</p>
      </section>
    </div>
  )
}
