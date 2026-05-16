import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { draftApi, workflowApi } from '../services/api'
import type { DraftHistoryItem } from '../types'
import { History, ChevronDown, ChevronUp, Copy, Globe, Facebook, Twitter, MessageSquare, Youtube, Send, CheckCircle, XCircle, Clock } from 'lucide-react'
import { toast } from 'sonner'
import { clsx } from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import { th } from 'date-fns/locale'

const PLATFORM_ICON: Record<string, React.ReactNode> = {
  website: <Globe size={12} />,
  facebook: <Facebook size={12} />,
  twitter: <Twitter size={12} />,
  line: <MessageSquare size={12} />,
  youtube: <Youtube size={12} />,
}

const PLATFORM_COLOR: Record<string, string> = {
  website: 'bg-blue-50 text-blue-700',
  facebook: 'bg-indigo-50 text-indigo-700',
  twitter: 'bg-sky-50 text-sky-700',
  line: 'bg-green-50 text-green-700',
  youtube: 'bg-red-50 text-red-700',
  instagram: 'bg-pink-50 text-pink-700',
  podcast: 'bg-orange-50 text-orange-700',
}

const STATUS_BADGE: Record<string, { label: string; cls: string; icon: React.ReactNode }> = {
  pending_review: { label: 'รอตรวจสอบ', cls: 'bg-amber-100 text-amber-700', icon: <Clock size={11} /> },
  approved: { label: 'อนุมัติแล้ว', cls: 'bg-emerald-100 text-emerald-700', icon: <CheckCircle size={11} /> },
  rejected: { label: 'ปฏิเสธ', cls: 'bg-red-100 text-red-700', icon: <XCircle size={11} /> },
}

function HistoryCard({
  item,
  workflowStatus,
  onSubmit,
  isSubmitting,
}: {
  item: DraftHistoryItem
  workflowStatus?: { status: string; review_comment: string; reviewed_by: string | null }
  onSubmit: (item: DraftHistoryItem, note: string) => void
  isSubmitting: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const [showSubmit, setShowSubmit] = useState(false)
  const [note, setNote] = useState('')

  const copy = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('คัดลอกแล้ว')
  }

  const timeAgo = formatDistanceToNow(new Date(item.generated_at), { addSuffix: true, locale: th })
  const badge = workflowStatus ? STATUS_BADGE[workflowStatus.status] : null

  return (
    <div className="bg-white border rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-4 py-3 flex items-start gap-3 hover:bg-gray-50 transition-colors"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={clsx(
              'flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium',
              PLATFORM_COLOR[item.platform] || 'bg-gray-100 text-gray-600',
            )}>
              {PLATFORM_ICON[item.platform]}
              {item.platform}
            </span>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{item.format}</span>
            {item.word_count > 0 && <span className="text-xs text-gray-400">{item.word_count} คำ</span>}
            {badge && (
              <span className={clsx('flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium', badge.cls)}>
                {badge.icon} {badge.label}
              </span>
            )}
            <span className="text-xs text-gray-400 ml-auto">{timeAgo}</span>
          </div>
          <p className="text-sm font-semibold text-gray-900 line-clamp-1">{item.title}</p>
          {item.news_title && item.news_title !== item.title && (
            <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">จากข่าว: {item.news_title}</p>
          )}
          {workflowStatus?.status === 'rejected' && workflowStatus.review_comment && (
            <p className="text-xs text-red-500 mt-0.5">ความเห็น: {workflowStatus.review_comment}</p>
          )}
        </div>
        <div className="shrink-0 text-gray-400 mt-0.5">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {expanded && item.full_draft && (
        <div className="border-t px-4 py-4 space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-xs text-gray-400 mb-1">หัวข้อ</p>
              <p className="text-sm font-bold text-gray-900">{item.full_draft.title}</p>
            </div>
            <button onClick={() => copy(item.full_draft.title)} className="text-gray-300 hover:text-violet-600 shrink-0">
              <Copy size={13} />
            </button>
          </div>

          {item.full_draft.lead && (
            <div>
              <p className="text-xs text-gray-400 mb-1">ย่อหน้านำ</p>
              <p className="text-sm text-gray-700 leading-relaxed">{item.full_draft.lead}</p>
            </div>
          )}

          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-400 mb-1">เนื้อหา</p>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap line-clamp-6">{item.full_draft.body}</p>
            </div>
            <button onClick={() => copy(item.full_draft.body)} className="text-gray-300 hover:text-violet-600 shrink-0">
              <Copy size={13} />
            </button>
          </div>

          {item.full_draft.seo_title && (
            <div className="bg-gray-50 rounded-lg px-3 py-2 space-y-1">
              <p className="text-xs text-gray-400 font-medium">SEO</p>
              <p className="text-xs font-medium text-gray-700">{item.full_draft.seo_title}</p>
              {item.full_draft.seo_description && <p className="text-xs text-gray-500">{item.full_draft.seo_description}</p>}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => copy(`# ${item.full_draft.title}\n\n${item.full_draft.lead || ''}\n\n${item.full_draft.body}`)}
              className="flex-1 text-xs border rounded-lg py-2 text-violet-600 hover:bg-violet-50 transition-colors flex items-center justify-center gap-1"
            >
              <Copy size={12} /> คัดลอกทั้งหมด
            </button>
            {/* Submit for review — only if not already submitted or rejected */}
            {(!workflowStatus || workflowStatus.status === 'rejected') && (
              <button
                onClick={() => setShowSubmit(!showSubmit)}
                className="flex-1 text-xs border border-violet-200 rounded-lg py-2 text-violet-600 hover:bg-violet-50 transition-colors flex items-center justify-center gap-1"
              >
                <Send size={12} /> ส่งตรวจสอบ
              </button>
            )}
          </div>

          {showSubmit && (
            <div className="space-y-2">
              <input
                value={note}
                onChange={e => setNote(e.target.value)}
                placeholder="หมายเหตุสำหรับบรรณาธิการ (ไม่บังคับ)"
                className="w-full text-xs border rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => { onSubmit(item, note); setShowSubmit(false); setNote('') }}
                  disabled={isSubmitting}
                  className="text-xs bg-violet-600 text-white px-3 py-1.5 rounded-lg hover:bg-violet-700 disabled:opacity-50"
                >
                  {isSubmitting ? 'กำลังส่ง...' : 'ยืนยันส่ง'}
                </button>
                <button onClick={() => setShowSubmit(false)} className="text-xs text-gray-400 px-2">ยกเลิก</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function HistoryPage() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['draft-history'],
    queryFn: () => draftApi.getHistory(100),
    staleTime: 30000,
  })

  const { data: statuses } = useQuery({
    queryKey: ['workflow-statuses'],
    queryFn: workflowApi.getStatuses,
    staleTime: 30000,
  })

  const submitMutation = useMutation({
    mutationFn: ({ item, note }: { item: DraftHistoryItem; note: string }) =>
      workflowApi.submit({
        draft_id: item.id,
        title: item.full_draft.title,
        body: item.full_draft.body,
        platform: item.platform,
        format: item.format,
        word_count: item.word_count,
        news_title: item.news_title,
        note,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflow-statuses'] })
      toast.success('ส่งบทความเพื่อตรวจสอบแล้ว')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg || 'เกิดข้อผิดพลาด')
    },
  })

  const items = data?.items ?? []

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto p-6 space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <History className="text-violet-600" /> ประวัติบทความ
          </h1>
          <p className="text-gray-500 mt-1">บทความ AI ที่สร้างไว้ล่าสุด {items.length} ชิ้น</p>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />)}
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-300 gap-3">
            <History size={48} className="opacity-30" />
            <p className="text-sm text-gray-400">ยังไม่มีบทความ — ไปสร้างบทความที่ AI Drafting</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map(item => (
              <HistoryCard
                key={item.id}
                item={item}
                workflowStatus={statuses?.[item.id]}
                onSubmit={(it, note) => submitMutation.mutate({ item: it, note })}
                isSubmitting={submitMutation.isPending}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
