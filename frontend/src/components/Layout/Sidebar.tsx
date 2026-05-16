import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  Radio, Brain, FileText, Layers, Mic, BarChart2, Settings, Send, LogOut, History, Shield, TrendingUp, CalendarClock,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const NAV_ITEMS = [
  { to: '/', icon: Radio, label: 'Feed Heartbeat', badge: 'Live' },
  { to: '/brief', icon: Brain, label: 'Editor Brief' },
  { to: '/draft', icon: FileText, label: 'AI Drafting' },
  { to: '/history', icon: History, label: 'ประวัติบทความ' },
  { to: '/angles', icon: Layers, label: 'Angle Generator' },
  { to: '/studio', icon: Mic, label: 'Content Studio' },
  { to: '/publisher', icon: Send, label: 'Publisher' },
  { to: '/schedule', icon: CalendarClock, label: 'ตั้งเวลาโพสต์' },
  { to: '/brain', icon: BarChart2, label: 'Brain Maturity' },
  { to: '/analytics', icon: TrendingUp, label: 'Analytics' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="w-56 bg-white border-r flex flex-col h-full shrink-0">
      {/* Logo */}
      <div className="px-4 py-4 border-b">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-violet-600 rounded-lg flex items-center justify-center">
            <Radio size={16} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900 text-sm leading-none">AInewsroom</h1>
            <p className="text-xs text-violet-600 leading-none mt-0.5">Editorial Intelligence</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5">
        {NAV_ITEMS.map(({ to, icon: Icon, label, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => clsx(
              'flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              isActive
                ? 'bg-violet-50 text-violet-700'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
            )}
          >
            <Icon size={16} />
            <span className="flex-1">{label}</span>
            {badge && (
              <span className="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded-full font-semibold animate-pulse">
                {badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="border-t px-2 py-3 space-y-1">
        {user?.role === 'admin' && (
          <NavLink
            to="/admin"
            className={({ isActive }) => clsx(
              'flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              isActive
                ? 'bg-red-50 text-red-700'
                : 'text-gray-500 hover:bg-gray-50',
            )}
          >
            <Shield size={16} />
            จัดการผู้ใช้
          </NavLink>
        )}
        <NavLink
          to="/settings"
          className={({ isActive }) => clsx(
            'flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
            isActive
              ? 'bg-violet-50 text-violet-700'
              : 'text-gray-500 hover:bg-gray-50',
          )}
        >
          <Settings size={16} />
          ตั้งค่าระบบ
        </NavLink>

        {user && (
          <div className="px-3 pt-2">
            <div className="text-xs font-medium text-gray-700 truncate">{user.full_name}</div>
            <div className="text-xs text-gray-400 truncate">{user.email}</div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-xs bg-violet-100 text-violet-700 px-1.5 py-0.5 rounded-full capitalize">
                {user.role}
              </span>
              <button
                onClick={logout}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-500 transition-colors"
                title="ออกจากระบบ"
              >
                <LogOut size={12} />
                ออก
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
