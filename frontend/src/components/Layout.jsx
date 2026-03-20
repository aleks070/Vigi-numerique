import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuth, AuthProvider } from '../hooks/useAuth'  // App.jsx
//import { useAuth } from '../hooks/useAuth'

const navItems = [
  { to: '/',       icon: '⬡', label: 'Supervision' },
  { to: '/events', icon: '◈', label: 'Événements'  },
  { to: '/map',    icon: '◎', label: 'Carte réseau' },
]

const pageTitles = {
  '/':       'Vue de supervision',
  '/events': 'Événements détectés',
  '/map':    'Carte du réseau',
}

export default function Layout() {
  const location = useLocation()
  const { agent, logout } = useAuth()
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const formatTime = (d) =>
    d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

  const formatDate = (d) =>
    d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })

  return (
    <div className="layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-badge">
            <div className="sidebar-logo-icon">🚦</div>
            <div>
              <div className="sidebar-logo-text">Vigi Numérique</div>
              <div className="sidebar-logo-sub">Supervision réseau IDF</div>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Navigation</div>
          {navItems.map(({ to, icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-link-icon">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          {/* Infos agent */}
          {agent && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>
                {agent.full_name}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>
                {agent.role}
              </div>
            </div>
          )}

          <div className="status-dot" style={{ marginBottom: 8 }}>
            <span className="dot" />
            Collecte active · 60s
          </div>

          {/* Bouton déconnexion */}
          <button
            onClick={logout}
            style={{
              width: '100%', padding: '6px 10px',
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 12, color: 'var(--text-secondary)',
              cursor: 'pointer', textAlign: 'left',
              fontFamily: 'DM Sans, sans-serif',
              transition: 'all 0.15s',
            }}
            onMouseOver={e => {
              e.target.style.background = 'var(--perturbe-bg)'
              e.target.style.color = 'var(--perturbe)'
              e.target.style.borderColor = 'var(--perturbe)'
            }}
            onMouseOut={e => {
              e.target.style.background = 'none'
              e.target.style.color = 'var(--text-secondary)'
              e.target.style.borderColor = 'var(--border)'
            }}
          >
            Déconnexion
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="main">
        <header className="topbar">
          <span className="topbar-title">
            {pageTitles[location.pathname] || 'Vigi Numérique'}
          </span>
          <div className="topbar-right">
            <span className="refresh-badge">● Live</span>
            <span className="topbar-time">
              {formatDate(time)} · {formatTime(time)}
            </span>
          </div>
        </header>

        <main className="page-content fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
