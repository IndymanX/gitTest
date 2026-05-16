import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AuthProvider, useAuth } from './context/AuthContext'
import { NotificationProvider } from './context/NotificationContext'
import BreakingNewsBanner from './components/BreakingNewsBanner'
import Sidebar from './components/Layout/Sidebar'
import DashboardPage from './pages/DashboardPage'
import BrainMaturityPage from './pages/BrainMaturityPage'
import ContentStudioPage from './pages/ContentStudioPage'
import SettingsPage from './pages/SettingsPage'
import PublisherPage from './pages/PublisherPage'
import HistoryPage from './pages/HistoryPage'
import AdminPage from './pages/AdminPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SchedulerPage from './pages/SchedulerPage'
import ReviewQueuePage from './pages/ReviewQueuePage'
import SearchModal from './components/Search/SearchModal'
import LoginPage from './pages/LoginPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30 * 1000,
    },
  },
})

function AppShell() {
  const { user, isLoading } = useAuth()
  const [searchOpen, setSearchOpen] = useState(false)

  // Global Cmd+K / Ctrl+K listener
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setSearchOpen(prev => !prev)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3 text-gray-400">
          <div className="w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">กำลังโหลด...</span>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <NotificationProvider>
      <BreakingNewsBanner />
      <SearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />
      <div className="flex h-screen bg-gray-50 overflow-hidden">
        <Sidebar onSearchOpen={() => setSearchOpen(true)} />
        <main className="flex-1 min-w-0 overflow-hidden">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/brief" element={<DashboardPage />} />
            <Route path="/draft" element={<DashboardPage />} />
            <Route path="/angles" element={<DashboardPage />} />
            <Route path="/brain" element={<BrainMaturityPage />} />
            <Route path="/studio" element={<ContentStudioPage />} />
            <Route path="/publisher" element={<PublisherPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/schedule" element={<SchedulerPage />} />
            <Route path="/review" element={<ReviewQueuePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </NotificationProvider>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AppShell />
          <Toaster position="top-right" richColors />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
