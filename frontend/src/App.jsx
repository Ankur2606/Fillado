import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'

// Existing Components
import Dashboard from './components/Dashboard'
import TradingFloor from './components/TradingFloor'
import DebateHistory from './components/DebateHistory'
import GraphIntelligence from './components/GraphIntelligence'

// Auth Components
import Login from './pages/Login'
// import Signup from './pages/Signup'
import { AuthProvider, useAuth } from './context/AuthContext'
import { useWebSocket } from './hooks/useWebSocket'

// --- Auth Protected Wrapper ---
const ProtectedRoute = ({ children }) => {
  const { loading } = useAuth();
  const sessionId = localStorage.getItem('sessionId');

  if (loading) return <div className="loading-screen">Initializing Fillado...</div>;
  if (!sessionId) return <Navigate to="/login" replace />;

  return children;
};

// --- The Main Application Logic (formerly your App component) ---
function FilladoApp() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [triggeredEvent, setTriggeredEvent] = useState(null)
  const [isDebating, setIsDebating] = useState(false)
  const [isHistoryOpen, setIsHistoryOpen] = useState(false)
  
  const { logout, user } = useAuth(); // Access auth state
  const { messages, lastMessage, status: wsStatus, clearMessages } = useWebSocket()

  const handleTriggerEvent = useCallback((data) => {
    clearMessages()
    setTriggeredEvent(data)
    setIsDebating(true)
    setActiveTab('trading-floor')
  }, [clearMessages])

  useEffect(() => {
    document.body.addEventListener("click", () => {
      const audio = new Audio();
      audio.play().catch(() => {});
    }, { once: true });
  }, []);

  const latestMsg = messages[messages.length - 1]
  if (latestMsg?.type === 'debate_end' && isDebating) {
    setIsDebating(false)
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ── Nav bar ── */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(5,8,16,0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border)',
        padding: '0 32px',
      }}>
        <div style={{
          maxWidth: 1280, margin: '0 auto',
          display: 'flex', alignItems: 'center', height: 60, gap: 20,
        }}>
          {/* Logo Section */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginRight: 32 }}>
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
              style={{ fontSize: '1.4rem' }}
            >◈</motion.div>
            <div>
              <div className="gradient-text" style={{ fontSize: '1.15rem', fontWeight: 900 }}>Fillado</div>
              <div style={{ fontSize: '0.55rem', color: 'var(--text-muted)', fontWeight: 600 }}>REALITY-ANCHORED</div>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav style={{ display: 'flex', gap: 4 }}>
            {['dashboard', 'trading-floor', 'graph'].map(id => (
              <button 
                key={id} 
                onClick={() => setActiveTab(id)}
                style={{
                   /* Keep your existing style logic here */
                   background: activeTab === id ? 'rgba(99,102,241,0.15)' : 'transparent',
                   color: activeTab === id ? 'var(--accent-purple)' : 'var(--text-muted)',
                   cursor: 'pointer', padding: '6px 16px', borderRadius: 8, border: 'none'
                }}
              >
                {id === 'dashboard' ? '📡 Radar' : id === 'graph' ? '🕸 Graph' : '🎯 Floor'}
              </button>
            ))}
          </nav>

          {/* Auth & History */}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 16 }}>
            <button onClick={() => setIsHistoryOpen(true)} className="btn-secondary">🕒 History</button>
            
            {/* Logout Button */}
            <button 
              onClick={logout} 
              style={{ 
                background: 'rgba(239, 68, 68, 0.1)', 
                border: '1px solid rgba(239, 68, 68, 0.2)',
                color: '#ef4444', padding: '6px 12px', borderRadius: 8, fontSize: '0.75rem'
              }}
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <DebateHistory isOpen={isHistoryOpen} onClose={() => setIsHistoryOpen(false)} />

      {/* Main Content Areas (Your existing logic) */}
      <main style={{ flex: 1, padding: '32px', maxWidth: 1280, margin: '0 auto', width: '100%' }}>
         <AnimatePresence mode="wait">
            {activeTab === 'dashboard' && (
              <Dashboard onTriggerEvent={handleTriggerEvent} isDebating={isDebating} wsStatus={wsStatus} />
            )}
            {activeTab === 'trading-floor' && (
              <TradingFloor messages={messages} lastMessage={lastMessage} wsStatus={wsStatus} />
            )}
            {activeTab === 'graph' && <GraphIntelligence />}
         </AnimatePresence>
      </main>

      {/* Footer code stays same */}
    </div>
  )
}

// --- The Root Export with Routing ---
export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          {/* <Route path="/signup" element={<Signup />} /> */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <FilladoApp />
              </ProtectedRoute>
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}