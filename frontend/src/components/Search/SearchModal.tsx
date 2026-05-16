import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, X, FileText, Rss } from 'lucide-react'
import { searchApi } from '../../services/api'
import { clsx } from 'clsx'

interface SearchResult {
  type: 'draft' | 'feed'
  id: string
  title: string
  subtitle: string
  platform?: string
  editorial_weight?: number
  date: string
}

interface Props {
  open: boolean
  onClose: () => void
}

export default function SearchModal({ open, onClose }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [activeIdx, setActiveIdx] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const navigate = useNavigate()

  // Focus input on open
  useEffect(() => {
    if (open) {
      setQuery('')
      setResults([])
      setActiveIdx(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  // Debounced search
  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    if (query.trim().length < 2) { setResults([]); return }

    timerRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const data = await searchApi.search(query)
        setResults(data.results as SearchResult[])
        setActiveIdx(0)
      } catch { setResults([]) }
      finally { setLoading(false) }
    }, 300)

    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [query])

  const handleSelect = useCallback((result: SearchResult) => {
    if (result.type === 'draft') {
      navigate('/history')
    } else {
      navigate('/')
    }
    onClose()
  }, [navigate, onClose])

  // Keyboard nav
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { onClose(); return }
      if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, results.length - 1)) }
      if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, 0)) }
      if (e.key === 'Enter' && results[activeIdx]) handleSelect(results[activeIdx])
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, results, activeIdx, handleSelect, onClose])

  if (!open) return null

  const drafts = results.filter(r => r.type === 'draft')
  const feed = results.filter(r => r.type === 'feed')

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-start justify-center pt-[15vh]"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-white rounded-2xl shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b">
          <Search size={16} className="text-gray-400 shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="ค้นหาบทความ หรือข่าวใน Feed..."
            className="flex-1 text-sm text-gray-900 focus:outline-none placeholder-gray-300"
          />
          {query && (
            <button onClick={() => setQuery('')} className="text-gray-300 hover:text-gray-500">
              <X size={14} />
            </button>
          )}
          <kbd className="hidden sm:inline text-xs border rounded px-1.5 py-0.5 text-gray-400 bg-gray-50">Esc</kbd>
        </div>

        {/* Results */}
        <div className="max-h-[400px] overflow-y-auto">
          {loading && (
            <div className="py-8 text-center text-gray-300 text-sm">กำลังค้นหา...</div>
          )}

          {!loading && query.length >= 2 && results.length === 0 && (
            <div className="py-8 text-center text-gray-300 text-sm">ไม่พบผลลัพธ์สำหรับ "{query}"</div>
          )}

          {!loading && query.length < 2 && (
            <div className="py-8 text-center text-gray-300 text-sm">พิมพ์อย่างน้อย 2 ตัวอักษรเพื่อค้นหา</div>
          )}

          {drafts.length > 0 && (
            <div>
              <div className="px-4 pt-3 pb-1 text-xs font-semibold text-gray-400 uppercase tracking-wide flex items-center gap-1.5">
                <FileText size={11} /> บทความที่สร้างไว้
              </div>
              {drafts.map((r, i) => {
                const globalIdx = i
                return (
                  <button
                    key={r.id}
                    onClick={() => handleSelect(r)}
                    className={clsx(
                      'w-full text-left px-4 py-2.5 flex items-center gap-3 hover:bg-violet-50 transition-colors',
                      activeIdx === globalIdx && 'bg-violet-50',
                    )}
                  >
                    <FileText size={14} className="text-violet-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 truncate">{r.title}</p>
                      {r.subtitle && <p className="text-xs text-gray-400 truncate">{r.subtitle}</p>}
                    </div>
                    {r.platform && (
                      <span className="text-xs text-gray-400 shrink-0">{r.platform}</span>
                    )}
                  </button>
                )
              })}
            </div>
          )}

          {feed.length > 0 && (
            <div>
              <div className="px-4 pt-3 pb-1 text-xs font-semibold text-gray-400 uppercase tracking-wide flex items-center gap-1.5">
                <Rss size={11} /> ข่าวใน Feed
              </div>
              {feed.map((r, i) => {
                const globalIdx = drafts.length + i
                return (
                  <button
                    key={r.id || i}
                    onClick={() => handleSelect(r)}
                    className={clsx(
                      'w-full text-left px-4 py-2.5 flex items-center gap-3 hover:bg-violet-50 transition-colors',
                      activeIdx === globalIdx && 'bg-violet-50',
                    )}
                  >
                    <Rss size={14} className="text-emerald-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 truncate">{r.title}</p>
                      {r.subtitle && <p className="text-xs text-gray-400 truncate">{r.subtitle}</p>}
                    </div>
                    {r.editorial_weight !== undefined && (
                      <span className={clsx(
                        'text-xs font-bold shrink-0',
                        r.editorial_weight >= 0.75 ? 'text-red-500' :
                        r.editorial_weight >= 0.5 ? 'text-amber-500' : 'text-gray-400',
                      )}>
                        {(r.editorial_weight * 100).toFixed(0)}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* Footer hint */}
        <div className="border-t px-4 py-2 flex items-center gap-4 text-xs text-gray-300">
          <span>↑↓ นำทาง</span>
          <span>↵ เปิด</span>
          <span>Esc ปิด</span>
        </div>
      </div>
    </div>
  )
}
