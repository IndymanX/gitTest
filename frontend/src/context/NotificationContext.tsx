import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react'
import type { ReactNode } from 'react'
import { useAuth } from './AuthContext'

interface BreakingAlert {
  id: string
  title: string
  timestamp: string
}

interface NotificationContextValue {
  breakingAlerts: BreakingAlert[]
  dismissAlert: (id: string) => void
}

const NotificationContext = createContext<NotificationContextValue>({
  breakingAlerts: [],
  dismissAlert: () => {},
})

export function NotificationProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [breakingAlerts, setBreakingAlerts] = useState<BreakingAlert[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  const dismissAlert = useCallback((id: string) => {
    setBreakingAlerts(prev => prev.filter(a => a.id !== id))
  }, [])

  useEffect(() => {
    if (!user) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/feed`)
    wsRef.current = ws

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg.type === 'feed_update' && msg.breaking) {
          const alert: BreakingAlert = {
            id: `${Date.now()}`,
            title: msg.title || 'ข่าวด่วน',
            timestamp: new Date().toLocaleTimeString('th-TH'),
          }
          setBreakingAlerts(prev => [alert, ...prev].slice(0, 5))
          // Auto-dismiss after 15 seconds
          setTimeout(() => dismissAlert(alert.id), 15000)
        }
      } catch {}
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [user]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <NotificationContext.Provider value={{ breakingAlerts, dismissAlert }}>
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  return useContext(NotificationContext)
}
