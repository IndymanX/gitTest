import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { schedulerApi } from '../services/api'
import { CalendarClock, Trash2, Globe, Facebook, Twitter, MessageSquare, Youtube, Clock } from 'lucide-react'
import { toast } from 'sonner'
import { formatDistanceToNow, format } from 'date-fns'
import { th } from 'date-fns/locale'
import { clsx } from 'clsx'

const PLATFORM_ICON: Record<string, React.ReactNode> = {
  website: <Globe size={13} />,
  facebook: <Facebook size={13} />,
  twitter: <Twitter size={13} />,
  line: <MessageSquare size={13} />,
  youtube: <Youtube size={13} />,
}

const PLATFORM_COLOR: Record<string, string> = {
  website: 'bg-blue-100 text-blue-700',
  facebook: 'bg-indigo-100 text-indigo-700',
  twitter: 'bg-sky-100 text-sky-700',
  line: 'bg-green-100 text-green-700',
  youtube: 'bg-red-100 text-red-700',
}

interface ScheduledPost {
  id: string
  title: string
  body: string
  platforms: string[]
  scheduled_at: string
  link?: string
  created_by: string
  status: string
}

export default function SchedulerPage() {
  const qc = useQueryClient()
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['scheduled-posts'],
    queryFn: schedulerApi.list,
    refetchInterval: 30000,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => schedulerApi.cancel(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['scheduled-posts'] })
      toast.success('ยกเลิกโพสต์แล้ว')
      setConfirmDelete(null)
    },
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  const posts: ScheduledPost[] = data?.posts ?? []
  const now = new Date()

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto p-6 space-y-4">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <CalendarClock className="text-violet-600" /> โพสต์ที่กำหนดเวลา
          </h1>
          <p className="text-gray-500 mt-1">
            จัดการโพสต์ที่รอการเผยแพร่ — Celery Beat ตรวจสอบทุก 60 วินาที
          </p>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : posts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-300 gap-3">
            <CalendarClock size={48} className="opacity-30" />
            <p className="text-sm text-gray-400">ยังไม่มีโพสต์ที่กำหนดไว้ — ตั้งเวลาจากหน้า Publisher</p>
          </div>
        ) : (
          <div className="space-y-3">
            {posts.map(post => {
              const scheduledDate = new Date(post.scheduled_at)
              const isPast = scheduledDate <= now
              const timeLabel = isPast
                ? 'กำลังประมวลผล...'
                : formatDistanceToNow(scheduledDate, { addSuffix: true, locale: th })

              return (
                <div key={post.id} className={clsx(
                  'bg-white border rounded-xl p-4',
                  isPast && 'opacity-60',
                )}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      {/* Platform badges */}
                      <div className="flex gap-1.5 flex-wrap mb-2">
                        {post.platforms.map(p => (
                          <span key={p} className={clsx(
                            'flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium',
                            PLATFORM_COLOR[p] || 'bg-gray-100 text-gray-600',
                          )}>
                            {PLATFORM_ICON[p]}
                            {p}
                          </span>
                        ))}
                      </div>

                      <p className="text-sm font-semibold text-gray-900 line-clamp-1">{post.title}</p>
                      <p className="text-xs text-gray-400 line-clamp-2 mt-0.5">{post.body}</p>

                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <Clock size={11} />
                          {format(scheduledDate, 'dd MMM yyyy · HH:mm', { locale: th })}
                        </span>
                        <span className={clsx(
                          'font-medium',
                          isPast ? 'text-amber-500' : 'text-emerald-600',
                        )}>
                          {timeLabel}
                        </span>
                        <span>โดย {post.created_by}</span>
                      </div>
                    </div>

                    {/* Cancel */}
                    {!isPast && (
                      confirmDelete === post.id ? (
                        <div className="flex items-center gap-1 shrink-0">
                          <span className="text-xs text-gray-500">ยืนยัน?</span>
                          <button
                            onClick={() => deleteMutation.mutate(post.id)}
                            className="text-xs bg-red-500 text-white px-2 py-1 rounded"
                          >
                            ยกเลิก
                          </button>
                          <button
                            onClick={() => setConfirmDelete(null)}
                            className="text-xs text-gray-400 px-1 py-1"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setConfirmDelete(post.id)}
                          className="text-gray-300 hover:text-red-500 transition-colors shrink-0"
                        >
                          <Trash2 size={15} />
                        </button>
                      )
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
