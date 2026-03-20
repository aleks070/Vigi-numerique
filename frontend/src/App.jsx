import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
//import { useAuth } from '../hooks/useAuth'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Events from './pages/Events'
import Map from './pages/Map'
import Login from './pages/Login'
import './index.css'

// ─── Route protégée ───────────────────────────────────────────
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-muted)', fontSize: 14,
      }}>
        Chargement...
      </div>
    )
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />
}

// ─── App avec routing ─────────────────────────────────────────
function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="events" element={<Events />} />
        <Route path="map" element={<Map />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}