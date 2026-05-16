import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workflowApi } from '../services/api'
import { ClipboardCheck, CheckCircle, XCircle, Globe, Facebook, Twitter, MessageSquare, Youtube, Clock } from 'lucide-react'
import { toast } from 'sonner'
import { clsx } from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import { th } from 'date-fns/locale'
import { useAuth } from '../context/AuthContext'

const PLATFORM_ICON: Record<string, React.ReactNode> = {
  website: <Globe size={12} />,
  facebook: <Facebook size={12} />,
  twitter: <Twitter size={12} />,
  line: <MessageSquare size={12} />,
  youtube: <Youtube size={12} />,
}

interface WorkflowItem {
  draft_id: string
  title: string
  body: string
  platform: string
  format: string
  word_count: number
  news_title: string
  note: string
  status: string
  submitted_by: string
  submitted_by_name: string
  submitted_at: string
  reviewed_by: string | null
  reviewed_by_name?: string
  reviewed_at: string | null
  review_comment: string
}

function QueueCard({ item, onReview }: {
  item: WorkflowItem
  onReview: (draftId: string, action: 'approve' | 'reject', comment: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [comment, setComment] = useState('')
  const [showReject, setShowReject] = useState(false)

  const timeAgo = formatDistanceToNow(new Date(item.submitted_at), { addSuffix: true, locale: th })

  return (
    <div className="bg-white border rounded-xl overflow-hidden">
      <div className="px-4 py-3">
        {/* Meta row */}
        <div className="flex items-center gap-2 flex-wrap mb-2">
          <span className="flex items-center gap-1 text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
            {PLATFORM_ICON[item.platform] || <Globe size={12} />}
            {item.platform}
          </span>
          <span className="text-xs text-gray-400">{item.format}</span>
          {item.word_count > 0 && <span className="text-xs text-gray-400">{item.word_count} คำ</span>}
          <span className="ml-auto text-xs text-gray-400 flex items-center gap-1">
            <Clock size={11} /> {timeAgo}
          </span>
        </div>

        {/* Title + author */}
        <p className="text-sm font-semibold text-gray-900 mb-0.5">{item.title}</p>
        <p className="text-xs text-gray-400">
          ส่งโดย {item.submitted_by_name || item.submitted_by}
          {item.news_title && ` · จากข่าว: ${item.news_title}`}
        </p>
        {item.note && (
          <p className="text-xs text-violet-600 mt-1 italic">หมายเหตุ: {item.note}</p>
        )}

        {/* Preview toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-violet-500 hover:text-violet-700 mt-2"
        >
          {expanded ? 'ซ่อนเนื้อหา' : 'ดูเนื้อหา'}
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-3 border-t bg-gray-50">
          <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap pt-3 max-h-48 overflow-y-auto">
            {item.body}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="px-4 py-3 border-t bg-gray-50 flex items-start gap-3">
        {showReject ? (
          <div className="flex-1 space-y-2">
            <textarea
              value={comment}
              onChange={e => setComment(e.target.value)}
              placeholder="ความเห็น / เหตุผลที่ปฏิเสธ (ไม่บังคับ)"
              className="w-full text-xs border rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-red-400 min-h-[60px] resize-none"
            />
            <div className="flex gap-2">
              <button
                onClick={() => { onReview(item.draft_id, 'reject', comment); setShowReject(false) }}
                className="text-xs bg-red-500 text-white px-3 py-1.5 rounded-lg hover:bg-red-600"
              >
                ยืนยันปฏิเสธ
              </button>
              <button
                onClick={() => setShowReject(false)}
                className="text-xs text-gray-500 px-3 py-1.5"
              >
                ยกเลิก
              </button>
            </div>
          </div>
        ) : (
          <>
            <button
              onClick={() => onReview(item.draft_id, 'approve', '')}
              className="flex items-center gap-1.5 text-xs bg-emerald-600 text-white px-3 py-2 rounded-lg hover:bg-emerald-700"
            >
              <CheckCircle size={13} /> อนุมัติ
            </button>
            <button
              onClick={() => setShowReject(true)}
              className="flex items-center gap-1.5 text-xs border border-red-300 text-red-600 px-3 py-2 rounded-lg hover:bg-red-50"
            >
              <XCircle size={13} /> ปฏิเสธ
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export default function ReviewQueuePage() {
  const { user } = useAuth()
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['workflow-queue'],
    queryFn: workflowApi.getQueue,
    refetchInterval: 30000,
  })

  const reviewMutation = useMutation({
    mutationFn: ({ draftId, action, comment }: { draftId: string; action: 'approve' | 'reject'; comment: string }) =>
      workflowApi.review(draftId, action, comment),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['workflow-queue'] })
      toast.success(data.status === 'approved' ? 'อนุมัติบทความแล้ว' : 'ปฏิเสธบทความแล้ว')
    },
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  const items: WorkflowItem[] = data?.items ?? []
  const isEditor = user?.role === 'editor' || user?.role === 'admin'

  if (!isEditor) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400 text-sm">
        เฉพาะบรรณาธิการ (Editor) และผู้ดูแลระบบเท่านั้น
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto p-6 space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <ClipboardCheck className="text-violet-600" /> คิวตรวจสอบบทความ
          </h1>
          <p className="text-gray-500 mt-1">
            {items.length > 0
              ? `${items.length} บทความรอการอนุมัติ`
              : 'ไม่มีบทความรอการอนุมัติ'}
          </p>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map(i => <div key={i} className="h-32 bg-gray-100 rounded-xl animate-pulse" />)}
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-300 gap-3">
            <ClipboardCheck size={48} className="opacity-30" />
            <p className="text-sm text-gray-400">ทุกบทความได้รับการตรวจสอบแล้ว</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map(item => (
              <QueueCard
                key={item.draft_id}
                item={item}
                onReview={(draftId, action, comment) =>
                  reviewMutation.mutate({ draftId, action, comment })
                }
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
