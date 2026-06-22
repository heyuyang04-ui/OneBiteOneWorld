import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000/api',
  timeout: 60000,
})

let sessionExpiredDispatched = false

// Inject session ID header
api.interceptors.request.use((config) => {
  const sessionId = localStorage.getItem('sessionId')
  if (sessionId) {
    config.headers['X-Session-Id'] = sessionId
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('currentUserId')
      localStorage.removeItem('sessionId')
      if (!sessionExpiredDispatched) {
        sessionExpiredDispatched = true
        window.dispatchEvent(new CustomEvent('auth:session-expired'))
        window.setTimeout(() => {
          sessionExpiredDispatched = false
        }, 1500)
      }
    }
    return Promise.reject(error)
  }
)

export default api
