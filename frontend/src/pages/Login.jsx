import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erreur de connexion'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{ width: 380 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 48, height: 48,
            background: 'var(--blue)',
            borderRadius: 12,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 12px',
            fontSize: 24,
          }}>🚦</div>
          <div style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>
            Vigi Numérique
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
            Supervision réseau Île-de-France
          </div>
        </div>

        {/* Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Connexion agent</span>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit}>

              {/* Email */}
              <div style={{ marginBottom: 16 }}>
                <label style={{
                  display: 'block', fontSize: 12, fontWeight: 600,
                  color: 'var(--text-secondary)', marginBottom: 6,
                  textTransform: 'uppercase', letterSpacing: '0.5px',
                }}>
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="agent@sncf.fr"
                  required
                  style={{
                    width: '100%', padding: '9px 12px',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 14, color: 'var(--text-primary)',
                    background: 'var(--surface)',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                  onFocus={e => e.target.style.borderColor = 'var(--blue)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border)'}
                />
              </div>

              {/* Mot de passe */}
              <div style={{ marginBottom: 24 }}>
                <label style={{
                  display: 'block', fontSize: 12, fontWeight: 600,
                  color: 'var(--text-secondary)', marginBottom: 6,
                  textTransform: 'uppercase', letterSpacing: '0.5px',
                }}>
                  Mot de passe
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{
                    width: '100%', padding: '9px 12px',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 14, color: 'var(--text-primary)',
                    background: 'var(--surface)',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                  onFocus={e => e.target.style.borderColor = 'var(--blue)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border)'}
                />
              </div>

              {/* Erreur */}
              {error && (
                <div style={{
                  background: 'var(--perturbe-bg)', color: 'var(--perturbe)',
                  border: '1px solid var(--perturbe)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '8px 12px', fontSize: 13,
                  marginBottom: 16,
                }}>
                  {error}
                </div>
              )}

              {/* Bouton */}
              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%', padding: '10px',
                  background: loading ? 'var(--border)' : 'var(--blue)',
                  color: 'white', border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 14, fontWeight: 500,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  transition: 'background 0.15s',
                  fontFamily: 'DM Sans, sans-serif',
                }}
              >
                {loading ? 'Connexion...' : 'Se connecter'}
              </button>

            </form>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: 'var(--text-muted)' }}>
          Accès réservé aux agents accrédités
        </div>
      </div>
    </div>
  )
}