import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import Sidebar from './components/Layout/Sidebar'
import DashboardPage from './pages/DashboardPage'
import BrainMaturityPage from './pages/BrainMaturityPage'
import ContentStudioPage from './pages/ContentStudioPage'
import SettingsPage from './pages/SettingsPage'
import PublisherPage from './pages/PublisherPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30 * 1000,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex h-screen bg-gray-50 overflow-hidden">
          <Sidebar />
          <main className="flex-1 min-w-0 overflow-hidden">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/brief" element={<DashboardPage />} />
              <Route path="/draft" element={<DashboardPage />} />
              <Route path="/angles" element={<DashboardPage />} />
              <Route path="/brain" element={<BrainMaturityPage />} />
              <Route path="/studio" element={<ContentStudioPage />} />
              <Route path="/publisher" element={<PublisherPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
