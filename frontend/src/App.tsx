import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import Sidebar from './components/Layout/Sidebar'
import DashboardPage from './pages/DashboardPage'
import BrainMaturityPage from './pages/BrainMaturityPage'

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
              <Route path="/studio" element={<ContentStudioPlaceholder />} />
              <Route path="/settings" element={<SettingsPlaceholder />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

function ContentStudioPlaceholder() {
  return (
    <div className="flex items-center justify-center h-full text-gray-400">
      <div className="text-center">
        <div className="text-4xl mb-3">🎨</div>
        <h2 className="text-lg font-semibold text-gray-600">Content Studio</h2>
        <p className="text-sm mt-1">Image Generation + TTS Voiceover</p>
        <p className="text-xs mt-2 text-gray-300">Coming in Phase 2</p>
      </div>
    </div>
  )
}

function SettingsPlaceholder() {
  return (
    <div className="flex items-center justify-center h-full text-gray-400">
      <div className="text-center">
        <div className="text-4xl mb-3">⚙️</div>
        <h2 className="text-lg font-semibold text-gray-600">ตั้งค่าระบบ</h2>
        <p className="text-sm mt-1">Style Constitution, API Keys, Organization</p>
        <p className="text-xs mt-2 text-gray-300">Coming in Phase 2</p>
      </div>
    </div>
  )
}
