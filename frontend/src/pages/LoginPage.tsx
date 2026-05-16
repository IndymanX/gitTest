import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Radio } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../services/api'

type Mode = 'login' | 'register'

export default function LoginPage() {
  const { login, register, user } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState<Mode>('login')
  const [isFirstRun, setIsFirstRun] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('reporter')
  const [loading, setLoading] = useState(false)

  // If already logged in, redirect home
  useEffect(() => {
    if (user) navigate('/', { replace: true })
  }, [user, navigate])

  // Check if this is first-run (no users yet) — auto-switch to register
  useEffect(() => {
    authApi.check().then(({ has_users }) => {
      if (!has_users) {
        setIsFirstRun(true)
        setMode('register')
      }
    }).catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(email, password)
        navigate('/', { replace: true })
      } else {
        if (!fullName.trim()) { toast.error('กรุณาใส่ชื่อ-นามสกุล'); return }
        await register(email, password, fullName, role)
        navigate('/', { replace: true })
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg || (mode === 'login' ? 'เข้าสู่ระบบไม่สำเร็จ' : 'ลงทะเบียนไม่สำเร็จ'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-50 to-gray-100">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center gap-3 justify-center mb-8">
          <div className="w-10 h-10 bg-violet-600 rounded-xl flex items-center justify-center">
            <Radio size={20} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900 text-xl leading-none">AInewsroom</h1>
            <p className="text-xs text-violet-600 leading-none mt-0.5">Editorial Intelligence</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border p-6">
          {isFirstRun && (
            <div className="mb-4 p-3 bg-violet-50 border border-violet-100 rounded-lg text-sm text-violet-700">
              ยินดีต้อนรับ! ลงทะเบียนบัญชีแรกของระบบ (Admin)
            </div>
          )}

          {/* Mode tabs */}
          {!isFirstRun && (
            <div className="flex mb-5 bg-gray-100 rounded-lg p-1">
              {(['login', 'register'] as const).map(m => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`flex-1 text-sm py-1.5 rounded-md font-medium transition-colors ${
                    mode === m ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'
                  }`}
                >
                  {m === 'login' ? 'เข้าสู่ระบบ' : 'ลงทะเบียน'}
                </button>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            {mode === 'register' && (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">ชื่อ-นามสกุล</label>
                <input
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  placeholder="สมชาย ใจดี"
                  required
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">อีเมล</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="editor@newsroom.th"
                required
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">รหัสผ่าน</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={6}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            {mode === 'register' && !isFirstRun && (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">บทบาท</label>
                <select
                  value={role}
                  onChange={e => setRole(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                >
                  <option value="reporter">นักข่าว (Reporter)</option>
                  <option value="editor">บรรณาธิการ (Editor)</option>
                  <option value="viewer">ผู้ชม (Viewer)</option>
                  <option value="admin">ผู้ดูแลระบบ (Admin)</option>
                </select>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-violet-600 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-violet-700 disabled:opacity-50 mt-2"
            >
              {loading
                ? 'กำลังดำเนินการ...'
                : mode === 'login' ? 'เข้าสู่ระบบ' : 'ลงทะเบียน'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-400 mt-4">
          AI ที่ไม่ใช่แค่เครื่องมือ แต่เป็นระบบที่ช่วยคิด
        </p>
      </div>
    </div>
  )
}
