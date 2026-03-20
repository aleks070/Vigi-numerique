import { useState, useEffect, createContext, useContext } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [agent, setAgent] = useState(null)
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)

  // Au démarrage, récupère le token en mémoire (sessionStorage)
  useEffect(() => {
    const savedToken = sessionStorage.getItem('vigi_token')
    const savedAgent = sessionStorage.getItem('vigi_agent')
    if (savedToken && savedAgent) {
      setToken(savedToken)
      setAgent(JSON.parse(savedAgent))
      axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)

    const response = await axios.post(`${API}/auth/login`, form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    const data = response.data
    setToken(data.access_token)
    setAgent({ agent_id: data.agent_id, full_name: data.full_name, role: data.role })

    // Stocke en sessionStorage (effacé à la fermeture du navigateur)
    sessionStorage.setItem('vigi_token', data.access_token)
    sessionStorage.setItem('vigi_agent', JSON.stringify({
      agent_id: data.agent_id,
      full_name: data.full_name,
      role: data.role,
    }))

    // Injecte le token dans tous les appels axios suivants
    axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

    return data
  }

  const logout = () => {
    setToken(null)
    setAgent(null)
    sessionStorage.removeItem('vigi_token')
    sessionStorage.removeItem('vigi_agent')
    delete axios.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ agent, token, login, logout, loading, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans AuthProvider')
  return ctx
}