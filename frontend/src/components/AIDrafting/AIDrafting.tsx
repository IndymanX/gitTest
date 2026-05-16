import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { draftApi, factCheckApi } from '../../services/api'
import type { NewsItem, DraftContent, CopyrightAnalysis, FactCheckResult, Platform, ContentFormat } from '../../types'
import { FileText, Zap, Copy, RefreshCw, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { toast } from 'sonner'
import CopyrightPanel from '../CopyrightAnalysis/CopyrightPanel'
import FactCheckPanel from '../FactChecker/FactCheckPanel'

interface Props {
  selectedItem?: NewsItem | null
}

const PLATFORMS: { value: Platform; label: string; icon: string }[] = [
  { value: 'website', label: 'เว็บไซต์', icon: '🌐' },
  { value: 'facebook', label: 'Facebook', icon: '📘' },
  { value: 'twitter', label: 'Twitter/X', icon: '🐦' },
  { value: 'line', label: 'LINE', icon: '💚' },
  { value: 'youtube', label: 'YouTube', icon: '📺' },
  { value: 'instagram', label: 'Instagram', icon: '📷' },
]

const FORMATS: { value: ContentFormat; label: string }[] = [
  { value: 'article', label: 'ข่าวปกติ' },
  { value: 'social_post', label: 'Social Post' },
  { value: 'video_script', label: 'สคริปต์วิดีโอ' },
  { value: 'podcast_script', label: 'สคริปต์พอดแคสต์' },
]

export default function AIDrafting({ selectedItem }: Props) {
  const [platform, setPlatform] = useState<Platform>('website')
  const [format, setFormat] = useState<ContentFormat>('article')
  const [angle, setAngle] = useState('')
  const [draft, setDraft] = useState<DraftContent | null>(null)
  const [copyright, setCopyright] = useState<CopyrightAnalysis | null>(null)
  const [factCheck, setFactCheck] = useState<FactCheckResult | null>(null)
  const [factCheckTaskId, setFactCheckTaskId] = useState<string | null>(null)
  const [showSeo, setShowSeo] = useState(false)
  const [editedBody, setEditedBody] = useState('')

  // Poll for async fact-check result every 3 seconds until done
  useQuery({
    queryKey: ['factcheck-status', factCheckTaskId],
    queryFn: () => factCheckApi.getStatus(factCheckTaskId!),
    enabled: !!factCheckTaskId && !factCheck,
    refetchInterval: 3000,
    select: (data) => {
      if (data.status === 'done' && data.fact_check) {
        setFactCheck(data.fact_check)
        setFactCheckTaskId(null)
      }
      return data
    },
  })

  const generateMutation = useMutation({
    mutationFn: () => draftApi.generate({
      news_item: selectedItem || { title: 'ทดสอบระบบ', summary: 'ทดสอบการสร้างบทความ' },
      format,
      platform,
      angle: angle || undefined,
      auto_check_copyright: true,
      auto_check_facts: true,
    }),
    onSuccess: (data) => {
      setDraft(data.draft)
      setEditedBody(data.draft.body)
      setFactCheck(null)
      if (data.copyright) setCopyright(data.copyright)
      if (data.fact_check) {
        setFactCheck(data.fact_check)
      } else if (data.fact_check_task_id) {
        setFactCheckTaskId(data.fact_check_task_id)
      }
      toast.success('สร้างบทความสำเร็จ')
    },
    onError: () => toast.error('เกิดข้อผิดพลาดในการสร้างบทความ'),
  })

  const reCopyrightMutation = useMutation({
    mutationFn: () => draftApi.checkCopyright({
      draft_text: editedBody,
      draft_title: draft?.title || '',
      source_texts: [selectedItem?.content || selectedItem?.summary || ''],
      source_chain: selectedItem?.source_chain || [],
    }),
    onSuccess: (data) => {
      setCopyright(data)
      toast.success('ตรวจลิขสิทธิ์ฉบับแก้ไข')
    },
  })

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('คัดลอกแล้ว')
  }

  const isLoading = generateMutation.isPending
  const factCheckPending = !!factCheckTaskId && !factCheck

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="bg-white border-b px-4 py-3">
        <div className="flex items-center gap-2 mb-3">
          <FileText size={16} className="text-violet-600" />
          <h2 className="font-semibold text-gray-800">AI Drafting</h2>
          {selectedItem && (
            <span className="text-xs text-gray-400 ml-auto truncate max-w-xs">{selectedItem.title}</span>
          )}
        </div>

        {/* Platform selector */}
        <div className="flex gap-1.5 flex-wrap mb-2">
          {PLATFORMS.map(p => (
            <button
              key={p.value}
              onClick={() => setPlatform(p.value)}
              className={clsx(
                'text-xs px-2.5 py-1.5 rounded-lg border font-medium transition-colors',
                platform === p.value
                  ? 'bg-violet-600 text-white border-violet-600'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-violet-400',
              )}
            >
              {p.icon} {p.label}
            </button>
          ))}
        </div>

        {/* Format + Angle + Generate */}
        <div className="flex gap-2">
          <select
            value={format}
            onChange={e => setFormat(e.target.value as ContentFormat)}
            className="text-xs border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-violet-500"
          >
            {FORMATS.map(f => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
          <input
            value={angle}
            onChange={e => setAngle(e.target.value)}
            placeholder="มุมมองพิเศษ (ไม่บังคับ)"
            className="flex-1 text-xs border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-violet-500"
          />
          <button
            onClick={() => generateMutation.mutate()}
            disabled={isLoading}
            className="flex items-center gap-1.5 text-xs bg-violet-600 text-white px-4 py-1.5 rounded-lg hover:bg-violet-700 disabled:opacity-50 font-medium"
          >
            <Zap size={12} />
            {isLoading ? 'กำลังเขียน...' : 'สร้างบทความ'}
          </button>
        </div>
      </div>

      {/* Draft content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!draft && !isLoading && (
          <div className="flex flex-col items-center justify-center h-64 text-gray-300 text-sm gap-2">
            <FileText size={40} />
            <p>เลือกข่าวจาก Feed แล้วกด "สร้างบทความ"</p>
          </div>
        )}

        {isLoading && (
          <div className="space-y-3 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-3/4" />
            <div className="h-4 bg-gray-100 rounded w-full" />
            <div className="h-4 bg-gray-100 rounded w-5/6" />
            <div className="h-4 bg-gray-100 rounded w-4/6" />
          </div>
        )}

        {draft && !isLoading && (
          <>
            {/* Title */}
            <div className="bg-white border rounded-xl p-4">
              <div className="flex items-start justify-between gap-2 mb-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">หัวข้อ</label>
                <button onClick={() => copyToClipboard(draft.title)} className="text-gray-300 hover:text-gray-500">
                  <Copy size={12} />
                </button>
              </div>
              <p className="text-base font-bold text-gray-900 leading-snug">{draft.title}</p>
            </div>

            {/* Lead */}
            {draft.lead && (
              <div className="bg-white border rounded-xl p-4">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-2">ย่อหน้านำ</label>
                <p className="text-sm text-gray-700 leading-relaxed">{draft.lead}</p>
              </div>
            )}

            {/* Body */}
            <div className="bg-white border rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">เนื้อหา</label>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <span>{draft.word_count} คำ · {draft.reading_time_minutes} นาที</span>
                  <button onClick={() => copyToClipboard(editedBody)} className="hover:text-gray-600">
                    <Copy size={12} />
                  </button>
                </div>
              </div>
              <textarea
                value={editedBody}
                onChange={e => setEditedBody(e.target.value)}
                className="w-full text-sm text-gray-700 leading-relaxed resize-none focus:outline-none min-h-[300px]"
              />
              {editedBody !== draft.body && (
                <button
                  onClick={() => reCopyrightMutation.mutate()}
                  disabled={reCopyrightMutation.isPending}
                  className="mt-2 flex items-center gap-1 text-xs text-violet-600 hover:text-violet-700"
                >
                  <RefreshCw size={10} />
                  ตรวจลิขสิทธิ์ฉบับแก้ไข
                </button>
              )}
            </div>

            {/* SEO collapsible */}
            {(draft.seo_title || draft.seo_description) && (
              <div className="bg-white border rounded-xl overflow-hidden">
                <button
                  onClick={() => setShowSeo(!showSeo)}
                  className="w-full flex items-center justify-between px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide hover:bg-gray-50"
                >
                  <span>SEO / AIO</span>
                  {showSeo ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                {showSeo && (
                  <div className="px-4 pb-4 space-y-3 border-t">
                    <div>
                      <label className="text-xs text-gray-500 block mb-1">SEO Title</label>
                      <p className="text-sm font-medium">{draft.seo_title}</p>
                    </div>
                    <div>
                      <label className="text-xs text-gray-500 block mb-1">Meta Description</label>
                      <p className="text-sm text-gray-600">{draft.seo_description}</p>
                    </div>
                    {draft.aio_keywords && draft.aio_keywords.length > 0 && (
                      <div>
                        <label className="text-xs text-gray-500 block mb-1">AIO Keywords</label>
                        <div className="flex flex-wrap gap-1">
                          {draft.aio_keywords.map((kw, i) => (
                            <span key={i} className="text-xs bg-violet-50 text-violet-700 px-2 py-0.5 rounded-full border border-violet-100">
                              {kw}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Copyright Analysis */}
            {copyright && <CopyrightPanel analysis={copyright} />}

            {/* Fact Check — shows spinner while Celery task is running */}
            {factCheckPending && (
              <div className="bg-white border rounded-xl p-4 flex items-center gap-2 text-sm text-gray-500">
                <Loader2 size={14} className="animate-spin text-violet-500" />
                กำลังตรวจสอบข้อเท็จจริง...
                <span className="text-xs text-gray-400">(ทำงานเบื้องหลัง)</span>
              </div>
            )}
            {factCheck && <FactCheckPanel result={factCheck} />}
          </>
        )}
      </div>
    </div>
  )
}
