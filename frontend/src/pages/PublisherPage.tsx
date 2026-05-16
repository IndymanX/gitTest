import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { draftApi } from '../services/api'
import type { Platform } from '../types'
import { Copy, Download, Globe, Facebook, Twitter, MessageSquare, Youtube, Send } from 'lucide-react'
import { toast } from 'sonner'
import { clsx } from 'clsx'

const PLATFORMS: { id: Platform; label: string; icon: React.ReactNode; color: string; maxChars?: number; desc: string }[] = [
  { id: 'website', label: 'Website', icon: <Globe size={16} />, color: 'blue', desc: 'บทความเต็ม SEO-friendly' },
  { id: 'facebook', label: 'Facebook', icon: <Facebook size={16} />, color: 'indigo', maxChars: 63206, desc: 'โพสต์เฟซบุ๊ก มี emoji' },
  { id: 'twitter', label: 'Twitter / X', icon: <Twitter size={16} />, color: 'sky', maxChars: 280, desc: 'ข้อความสั้น กระชับ' },
  { id: 'line', label: 'LINE Today', icon: <MessageSquare size={16} />, color: 'green', desc: 'ข่าวสั้น ลิงก์ต่อ' },
  { id: 'youtube', label: 'YouTube', icon: <Youtube size={16} />, color: 'red', desc: 'คำอธิบายวิดีโอ + แท็ก' },
]

const COLOR_MAP: Record<string, string> = {
  blue: 'border-blue-500 bg-blue-50 text-blue-700',
  indigo: 'border-indigo-500 bg-indigo-50 text-indigo-700',
  sky: 'border-sky-500 bg-sky-50 text-sky-700',
  green: 'border-green-500 bg-green-50 text-green-700',
  red: 'border-red-500 bg-red-50 text-red-700',
}

function readingTime(text: string) {
  const words = text.trim().split(/\s+/).length
  const minutes = Math.max(1, Math.round(words / 200))
  return `${minutes} นาที`
}

export default function PublisherPage() {
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [activePlatform, setActivePlatform] = useState<Platform>('website')
  const [adaptedContent, setAdaptedContent] = useState<Record<string, string>>({})

  const adaptMutation = useMutation({
    mutationFn: (platform: Platform) => draftApi.adaptForPlatform(platform, { title, body }),
    onSuccess: (data, platform) => {
      const text = data.adapted_content ?? data.content ?? data.text ?? JSON.stringify(data)
      setAdaptedContent(prev => ({ ...prev, [platform]: text }))
      toast.success(`ปรับรูปแบบสำหรับ ${PLATFORMS.find(p => p.id === platform)?.label} สำเร็จ`)
    },
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  const adaptAll = () => {
    if (!title.trim() || !body.trim()) return
    PLATFORMS.forEach(p => adaptMutation.mutate(p.id))
  }

  const currentText = adaptedContent[activePlatform] ?? ''
  const platform = PLATFORMS.find(p => p.id === activePlatform)!

  const copyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    toast.success(`คัดลอก ${label} แล้ว`)
  }

  const downloadText = (text: string, filename: string) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Send className="text-violet-600" /> Publisher Export
          </h1>
          <p className="text-gray-500 mt-1">แปลงบทความเป็นรูปแบบที่เหมาะกับแต่ละแพลตฟอร์ม</p>
        </div>

        {/* Article input */}
        <div className="bg-white border rounded-xl p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-600">บทความต้นฉบับ</h2>
          <input
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="หัวข้อข่าว..."
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500 font-medium"
          />
          <textarea
            value={body}
            onChange={e => setBody(e.target.value)}
            placeholder="เนื้อหาบทความ (วางจาก AI Drafting หรือพิมพ์เอง)..."
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500 min-h-[140px] resize-y"
          />
          <div className="flex items-center justify-between">
            <div className="flex gap-4 text-xs text-gray-400">
              <span>{body.trim().split(/\s+/).filter(Boolean).length} คำ</span>
              <span>อ่าน {readingTime(body)}</span>
            </div>
            <button
              onClick={adaptAll}
              disabled={adaptMutation.isPending || !title.trim() || !body.trim()}
              className="flex items-center gap-1.5 bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 disabled:opacity-50"
            >
              <Send size={13} />
              {adaptMutation.isPending ? 'กำลังปรับรูปแบบ...' : 'ปรับทุกแพลตฟอร์ม'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-[220px_1fr] gap-6">
          {/* Platform selector */}
          <div className="space-y-2">
            {PLATFORMS.map(p => {
              const hasContent = !!adaptedContent[p.id]
              const isActive = activePlatform === p.id
              return (
                <button
                  key={p.id}
                  onClick={() => setActivePlatform(p.id)}
                  className={clsx(
                    'w-full text-left px-4 py-3 rounded-xl border-2 transition-all',
                    isActive ? COLOR_MAP[p.color] : 'border-gray-100 bg-white hover:border-gray-300',
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span className={isActive ? '' : 'text-gray-400'}>{p.icon}</span>
                    <span className={clsx('text-sm font-semibold', isActive ? '' : 'text-gray-700')}>
                      {p.label}
                    </span>
                    {hasContent && (
                      <span className="ml-auto w-2 h-2 rounded-full bg-emerald-400 shrink-0" title="มีเนื้อหาแล้ว" />
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5 pl-6">{p.desc}</p>
                </button>
              )
            })}
          </div>

          {/* Content panel */}
          <div className="bg-white border rounded-xl overflow-hidden flex flex-col">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
              <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                {platform.icon}
                <span>{platform.label}</span>
                {currentText && platform.maxChars && (
                  <span className={clsx(
                    'text-xs font-normal',
                    currentText.length > platform.maxChars ? 'text-red-500' : 'text-gray-400',
                  )}>
                    {currentText.length}/{platform.maxChars}
                  </span>
                )}
                {currentText && (
                  <span className="text-xs text-gray-400 font-normal">· {readingTime(currentText)} อ่าน</span>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => adaptMutation.mutate(activePlatform)}
                  disabled={adaptMutation.isPending || !title.trim() || !body.trim()}
                  className="text-xs text-violet-600 hover:text-violet-800 border border-violet-200 rounded-lg px-2.5 py-1.5 disabled:opacity-50"
                >
                  {adaptMutation.isPending ? 'กำลังสร้าง...' : 'สร้างใหม่'}
                </button>
                {currentText && (
                  <>
                    <button
                      onClick={() => copyText(currentText, platform.label)}
                      className="flex items-center gap-1 text-xs text-gray-500 hover:text-violet-600 border rounded-lg px-2.5 py-1.5"
                    >
                      <Copy size={12} /> คัดลอก
                    </button>
                    <button
                      onClick={() => downloadText(currentText, `${activePlatform}-${Date.now()}.txt`)}
                      className="flex items-center gap-1 text-xs text-gray-500 hover:text-violet-600 border rounded-lg px-2.5 py-1.5"
                    >
                      <Download size={12} /> .txt
                    </button>
                    <button
                      onClick={() => downloadText(`# ${title}\n\n${currentText}`, `${activePlatform}-${Date.now()}.md`)}
                      className="flex items-center gap-1 text-xs text-gray-500 hover:text-violet-600 border rounded-lg px-2.5 py-1.5"
                    >
                      <Download size={12} /> .md
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Content area */}
            <div className="flex-1 p-4">
              {adaptMutation.isPending && !currentText ? (
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                  <div className="h-4 bg-gray-200 rounded w-full" />
                  <div className="h-4 bg-gray-200 rounded w-5/6" />
                  <div className="h-4 bg-gray-200 rounded w-2/3" />
                </div>
              ) : currentText ? (
                <textarea
                  value={currentText}
                  onChange={e => setAdaptedContent(prev => ({ ...prev, [activePlatform]: e.target.value }))}
                  className="w-full h-full min-h-[300px] text-sm text-gray-800 leading-relaxed resize-none focus:outline-none"
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-48 text-gray-300 gap-3">
                  <div className="text-5xl opacity-30">{platform.icon}</div>
                  <p className="text-sm text-gray-400">กด "สร้างใหม่" หรือ "ปรับทุกแพลตฟอร์ม" เพื่อสร้างเนื้อหา</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
