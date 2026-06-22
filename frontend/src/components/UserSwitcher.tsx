import { useEffect, useState } from 'react'
import api from '../services/api'
import './UserSwitcher.css'

interface User {
  id: string
  name: string
  city: string
}

export default function UserSwitcher() {
  const [users, setUsers] = useState<User[]>([])
  const [current, setCurrent] = useState(localStorage.getItem('currentUserId') || 'user_01')
  const [open, setOpen] = useState(false)

  useEffect(() => {
    api.get('/users').then(res => setUsers(res.data.data || []))
  }, [])

  const switchUser = async (id: string) => {
    const res = await api.put('/users/me/switch', { user_id: id })
    if (res.data.success) {
      localStorage.setItem('currentUserId', id)
      localStorage.setItem('sessionId', res.data.data.session_id)
      setCurrent(id)
      setOpen(false)
      window.location.reload()
    }
  }

  const currentUser = users.find(u => u.id === current)

  return (
    <div className="user-switcher">
      <button className="switcher-btn" onClick={() => setOpen(!open)}>
        {currentUser ? `${currentUser.name}` : current}
        <span className="arrow">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="switcher-dropdown">
          {users.slice(0, 20).map(u => (
            <div key={u.id} className={`switcher-item ${u.id === current ? 'active' : ''}`}
                 onClick={() => switchUser(u.id)}>
              {u.name} <span className="city">{u.city}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
