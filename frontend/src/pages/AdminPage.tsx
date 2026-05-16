import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi } from '../services/api'
import type { ManagedUser } from '../types'
import { Shield, UserCheck, UserX, Trash2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { clsx } from 'clsx'
import { useAuth } from '../context/AuthContext'

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-red-100 text-red-700',
  editor: 'bg-violet-100 text-violet-700',
  reporter: 'bg-blue-100 text-blue-700',
  viewer: 'bg-gray-100 text-gray-600',
}

const ROLES = ['admin', 'editor', 'reporter', 'viewer']

export default function AdminPage() {
  const { user: me } = useAuth()
  const qc = useQueryClient()
  const [deletingEmail, setDeletingEmail] = useState<string | null>(null)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['admin-users'],
    queryFn: authApi.listUsers,
  })

  const updateMutation = useMutation({
    mutationFn: ({ email, updates }: { email: string; updates: Parameters<typeof authApi.updateUser>[1] }) =>
      authApi.updateUser(email, updates),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] })
      toast.success('อัปเดตผู้ใช้แล้ว')
    },
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  const deleteMutation = useMutation({
    mutationFn: (email: string) => authApi.deleteUser(email),
    onSuccess: (_, email) => {
      qc.invalidateQueries({ queryKey: ['admin-users'] })
      toast.success(`ลบ ${email} แล้ว`)
      setDeletingEmail(null)
    },
    onError: () => toast.error('ไม่สามารถลบได้'),
  })

  const users: ManagedUser[] = data?.users ?? []

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Shield className="text-red-500" /> จัดการผู้ใช้งาน
            </h1>
            <p className="text-gray-500 mt-1">เฉพาะผู้ดูแลระบบ (Admin) เท่านั้น</p>
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 border rounded-lg px-3 py-2"
          >
            <RefreshCw size={14} /> รีเฟรช
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          {ROLES.map(role => {
            const count = users.filter(u => u.role === role).length
            return (
              <div key={role} className={clsx('rounded-xl p-4 border', ROLE_COLORS[role])}>
                <div className="text-2xl font-bold">{count}</div>
                <div className="text-sm capitalize">{role}</div>
              </div>
            )
          })}
        </div>

        {/* User table */}
        <div className="bg-white border rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b bg-gray-50 text-sm font-semibold text-gray-600">
            ผู้ใช้งานทั้งหมด ({users.length})
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-gray-400 text-sm">กำลังโหลด...</div>
          ) : users.length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-sm">ไม่พบผู้ใช้งาน</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-400 border-b">
                  <th className="text-left px-4 py-2.5 font-medium">ชื่อ / อีเมล</th>
                  <th className="text-left px-4 py-2.5 font-medium">บทบาท</th>
                  <th className="text-left px-4 py-2.5 font-medium">สถานะ</th>
                  <th className="text-right px-4 py-2.5 font-medium">จัดการ</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => {
                  const isSelf = user.email === me?.email
                  return (
                    <tr key={user.email} className="border-b last:border-0 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-800">{user.full_name}</div>
                        <div className="text-xs text-gray-400">{user.email}</div>
                        {isSelf && <span className="text-xs text-violet-500">(คุณ)</span>}
                      </td>
                      <td className="px-4 py-3">
                        <select
                          value={user.role}
                          disabled={isSelf}
                          onChange={e => updateMutation.mutate({ email: user.email, updates: { role: e.target.value } })}
                          className={clsx(
                            'text-xs border rounded-lg px-2 py-1 font-medium focus:outline-none focus:ring-1 focus:ring-violet-500',
                            isSelf ? 'opacity-50 cursor-not-allowed' : '',
                          )}
                        >
                          {ROLES.map(r => (
                            <option key={r} value={r}>{r}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          disabled={isSelf}
                          onClick={() => updateMutation.mutate({ email: user.email, updates: { is_active: !user.is_active } })}
                          className={clsx(
                            'flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border font-medium transition-colors',
                            user.is_active
                              ? 'bg-green-50 text-green-700 border-green-200 hover:bg-red-50 hover:text-red-600 hover:border-red-200'
                              : 'bg-red-50 text-red-600 border-red-200 hover:bg-green-50 hover:text-green-700 hover:border-green-200',
                            isSelf ? 'opacity-50 cursor-not-allowed' : '',
                          )}
                        >
                          {user.is_active ? <><UserCheck size={11} /> ใช้งาน</> : <><UserX size={11} /> ระงับ</>}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {!isSelf && (
                          deletingEmail === user.email ? (
                            <div className="flex items-center gap-1 justify-end">
                              <span className="text-xs text-gray-500">ยืนยันลบ?</span>
                              <button
                                onClick={() => deleteMutation.mutate(user.email)}
                                className="text-xs bg-red-500 text-white px-2 py-1 rounded"
                              >
                                ลบ
                              </button>
                              <button
                                onClick={() => setDeletingEmail(null)}
                                className="text-xs text-gray-500 px-2 py-1"
                              >
                                ยกเลิก
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => setDeletingEmail(user.email)}
                              className="text-gray-300 hover:text-red-500 transition-colors"
                            >
                              <Trash2 size={14} />
                            </button>
                          )
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
