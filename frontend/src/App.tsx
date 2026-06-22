import { Suspense, lazy, useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import Layout from './components/Layout'
import RouteErrorBoundary from './components/RouteErrorBoundary'
import api from './services/api'
import './App.css'

const Login = lazy(() => import('./pages/Login'))
const Home = lazy(() => import('./pages/Home'))
const MealResult = lazy(() => import('./pages/MealResult'))
const MealHistory = lazy(() => import('./pages/MealHistory'))
const TasteProfile = lazy(() => import('./pages/TasteProfile'))
const WeeklyReport = lazy(() => import('./pages/WeeklyReport'))
const SocialDiscover = lazy(() => import('./pages/SocialDiscover'))
const MatchDetail = lazy(() => import('./pages/MatchDetail'))
const MatchList = lazy(() => import('./pages/MatchList'))
const CityMap = lazy(() => import('./pages/CityMap'))
const CityDistrict = lazy(() => import('./pages/CityDistrict'))
const CityTrends = lazy(() => import('./pages/CityTrends'))
const CityRecommend = lazy(() => import('./pages/CityRecommend'))
const Notifications = lazy(() => import('./pages/Notifications'))
const Settings = lazy(() => import('./pages/Settings'))

function TasteLoading({ text }: { text: string }) {
  return (
    <div className="taste-loading-page">
      <div className="taste-loading-card">
        <div className="taste-loading-orbit" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <p>{text}</p>
      </div>
    </div>
  )
}

function PageFallback() {
  return <TasteLoading text="正在加载味觉世界..." />
}

function ProtectedLayout() {
  const saved = localStorage.getItem('currentUserId')
  const sessionId = localStorage.getItem('sessionId')
  const [checking, setChecking] = useState(Boolean(saved && sessionId))
  const [valid, setValid] = useState(false)

  useEffect(() => {
    if (!saved || !sessionId) return
    let active = true
    api.get('/users/me').then(res => {
      if (!active) return
      setValid(Boolean(res.data.success && res.data.data?.id))
    }).catch(() => {
      if (!active) return
      localStorage.removeItem('currentUserId')
      localStorage.removeItem('sessionId')
      setValid(false)
    }).finally(() => {
      if (active) setChecking(false)
    })
    return () => {
      active = false
    }
  }, [saved, sessionId])

  if (!saved || !sessionId) {
    return <Navigate to="/login" replace />
  }
  if (checking) {
    return <TasteLoading text="正在恢复味觉档案..." />
  }
  if (!valid) {
    return <Navigate to="/login" replace />
  }
  return <Layout />
}

function AppRoutes() {
  const navigate = useNavigate()
  const [sessionExpired, setSessionExpired] = useState(false)

  useEffect(() => {
    const handleSessionExpired = () => {
      setSessionExpired(true)
      navigate('/login', { replace: true })
      window.setTimeout(() => setSessionExpired(false), 2600)
    }
    window.addEventListener('auth:session-expired', handleSessionExpired)
    return () => window.removeEventListener('auth:session-expired', handleSessionExpired)
  }, [navigate])

  return (
    <>
      {sessionExpired && <div className="session-expired-banner">登录已失效，请重新登录</div>}
      <RouteErrorBoundary>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/login" element={<Login />} />
            <Route element={<ProtectedLayout />}>
              <Route path="/home" element={<Home />} />
              <Route path="/meal/:id" element={<MealResult />} />
              <Route path="/history" element={<MealHistory />} />
              <Route path="/profile" element={<TasteProfile />} />
              <Route path="/report" element={<WeeklyReport />} />
              <Route path="/discover" element={<SocialDiscover />} />
              <Route path="/match/:id" element={<MatchDetail />} />
              <Route path="/matches" element={<MatchList />} />
              <Route path="/city" element={<CityMap />} />
              <Route path="/city/district/:id" element={<CityDistrict />} />
              <Route path="/city/trends" element={<CityTrends />} />
              <Route path="/city/recommend" element={<CityRecommend />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/home" />} />
            </Route>
          </Routes>
        </Suspense>
      </RouteErrorBoundary>
    </>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

export default App
