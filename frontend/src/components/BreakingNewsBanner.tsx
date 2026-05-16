import { X, Zap } from 'lucide-react'
import { useNotifications } from '../context/NotificationContext'

export default function BreakingNewsBanner() {
  const { breakingAlerts, dismissAlert } = useNotifications()

  if (breakingAlerts.length === 0) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-50 space-y-1 pointer-events-none">
      {breakingAlerts.map(alert => (
        <div
          key={alert.id}
          className="flex items-center gap-3 bg-red-600 text-white px-4 py-2.5 shadow-lg pointer-events-auto animate-in slide-in-from-top duration-300"
        >
          <Zap size={16} className="shrink-0 animate-pulse" />
          <span className="text-xs font-bold uppercase tracking-wider text-red-200">BREAKING</span>
          <span className="text-sm font-medium flex-1 line-clamp-1">{alert.title}</span>
          <span className="text-xs text-red-300 shrink-0">{alert.timestamp}</span>
          <button
            onClick={() => dismissAlert(alert.id)}
            className="text-red-200 hover:text-white shrink-0"
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  )
}
