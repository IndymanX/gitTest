import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { feedApi } from '../../services/api'
import type { NewsItem, FeedStats } from '../../types'
import { clsx } from 'clsx'
import { Flame, Clock, Zap, Star, RefreshCw, Rss, BarChart2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { th } from 'date-fns/locale'
import { toast } from 'sonner'

interface Props {
  onSelectItem?: (item: NewsItem) => void
}

const WEIGHT_COLOR = (w: number) => {
  if (w >= 0.75) return 'text-red-500 bg-red-50 border-red-200'
  if (w >= 0.5) return 'text-amber-600 bg-amber-50 border-amber-200'
  return 'text-green-600 bg-green-50 border-green-200'
}

const WEIGHT_LABEL = (w: number) => {
  if (w >= 0.75) return 'ด่วน'
  if (w >= 0.5) return 'สำคัญ'
  return 'รอได้'
}

export default function FeedHeartbeat({ onSelectItem }: Props) {
  const [feedUrls, setFeedUrls] = useState('')
  const [filter, setFilter] = useState<'all' | 'urgent' | 'breaking' | 'wait'>('all')

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['feed-stats'],
    queryFn: feedApi.getStats,
    refetchInterval: 30000,
  })

  const { data: feedData, refetch: refetchFeed, isLoading } = useQuery({
    queryKey: ['feed-live', filter],
    queryFn: () => feedApi.getLive({
      limit: 100,
      min_weight: filter === 'urgent' ? 0.75 : filter === 'wait' ? 0 : 0,
    }),
    refetchInterval: 60000,
  })

  // WebSocket — live feed updates via Redis pub/sub
  const wsRef = useRef<WebSocket | null>(null)
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/feed`)
    wsRef.current = ws

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg.type === 'feed_update') {
          refetchFeed()
          refetchStats()
          if (msg.breaking) toast.info(`Breaking: ${msg.title || 'ข่าวด่วน'}`, { duration: 6000 })
        }
      } catch {}
    }

    return () => ws.close()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const fetchMutation = useMutation({
    mutationFn: (urls: string[]) => feedApi.fetchUrls(urls),
    onSuccess: (data) => {
      toast.success(`ดึงข่าวสำเร็จ — ${data.total_in_cache} ชิ้น`)
      refetchFeed()
      refetchStats()
    },
    onError: () => toast.error('ไม่สามารถดึงข่าวได้'),
  })

  const handleFetch = () => {
    const urls = feedUrls.split('\n').map(u => u.trim()).filter(Boolean)
    if (!urls.length) return toast.error('กรุณาใส่ URL')
    fetchMutation.mutate(urls)
  }

  const items = feedData?.items || []
  const filtered = items.filter(item => {
    if (filter === 'urgent') return item.needs_immediate_action
    if (filter === 'breaking') return item.is_breaking
    if (filter === 'wait') return item.can_wait
    return true
  })

  return (
    <div className="flex flex-col h-full">
      {/* Header Stats */}
      <div className="bg-white border-b px-4 py-3">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          <h2 className="font-semibold text-gray-800">Feed Heartbeat</h2>
          <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">Live</span>
          <button
            onClick={() => { refetchFeed(); refetchStats() }}
            className="ml-auto text-gray-400 hover:text-gray-600"
          >
            <RefreshCw size={14} />
          </button>
        </div>

        {/* Stats bar */}
        {stats && (
          <div className="grid grid-cols-5 gap-2">
            <StatBadge icon={<BarChart2 size={12} />} label="ทั้งหมด" value={stats.total} color="gray" />
            <StatBadge icon={<Flame size={12} />} label="ด่วน" value={stats.urgent} color="red" />
            <StatBadge icon={<Clock size={12} />} label="รอได้" value={stats.can_wait} color="yellow" />
            <StatBadge icon={<Zap size={12} />} label="1 ชม." value={stats.last_hour} color="blue" />
            <StatBadge icon={<Star size={12} />} label="Exclusive" value={stats.exclusive} color="purple" />
          </div>
        )}
      </div>

      {/* Feed URL input */}
      <div className="bg-gray-50 border-b px-4 py-2">
        <div className="flex gap-2">
          <input
            value={feedUrls}
            onChange={e => setFeedUrls(e.target.value)}
            placeholder="ใส่ RSS URL (หนึ่ง URL ต่อบรรทัด)"
            className="flex-1 text-xs border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-violet-500"
          />
          <button
            onClick={handleFetch}
            disabled={fetchMutation.isPending}
            className="text-xs bg-violet-600 text-white px-3 py-1.5 rounded hover:bg-violet-700 disabled:opacity-50 flex items-center gap-1"
          >
            <Rss size={12} />
            {fetchMutation.isPending ? 'กำลังดึง...' : 'ดึงข่าว'}
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex border-b bg-white">
        {([['all', 'ทั้งหมด'], ['urgent', 'ต้องทำทันที'], ['breaking', 'Breaking'], ['wait', 'รอได้']] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={clsx(
              'flex-1 text-xs py-2 font-medium transition-colors',
              filter === key
                ? 'text-violet-600 border-b-2 border-violet-600'
                : 'text-gray-500 hover:text-gray-700',
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {/* News list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            กำลังโหลด...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-gray-400 text-sm gap-2">
            <Rss size={24} className="opacity-30" />
            <p>ยังไม่มีข่าว — กรุณาใส่ RSS URL แล้วกด "ดึงข่าว"</p>
          </div>
        ) : (
          filtered.map((item, i) => (
            <NewsCard key={i} item={item} onClick={() => onSelectItem?.(item)} />
          ))
        )}
      </div>
    </div>
  )
}

function StatBadge({
  icon, label, value, color,
}: {
  icon: React.ReactNode
  label: string
  value: number
  color: string
}) {
  const colors: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-700',
    red: 'bg-red-100 text-red-700',
    yellow: 'bg-amber-100 text-amber-700',
    blue: 'bg-blue-100 text-blue-700',
    purple: 'bg-violet-100 text-violet-700',
  }
  return (
    <div className={clsx('flex flex-col items-center rounded-lg p-1.5', colors[color])}>
      <div className="flex items-center gap-1">
        {icon}
        <span className="font-bold text-sm">{value}</span>
      </div>
      <span className="text-xs opacity-70">{label}</span>
    </div>
  )
}

function NewsCard({ item, onClick }: { item: NewsItem; onClick: () => void }) {
  const weightColor = WEIGHT_COLOR(item.editorial_weight)
  const publishedText = item.published_at
    ? formatDistanceToNow(new Date(item.published_at), { addSuffix: true, locale: th })
    : ''

  return (
    <div
      onClick={onClick}
      className="flex gap-3 px-4 py-3 border-b hover:bg-violet-50 cursor-pointer transition-colors group"
    >
      {/* Weight badge */}
      <div className={clsx('shrink-0 mt-0.5 text-xs font-bold px-1.5 py-0.5 rounded border h-fit', weightColor)}>
        {(item.editorial_weight * 100).toFixed(0)}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start gap-1.5 flex-wrap mb-0.5">
          {item.is_breaking && (
            <span className="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded-full font-semibold">BREAKING</span>
          )}
          {item.needs_immediate_action && !item.is_breaking && (
            <span className="text-xs bg-orange-500 text-white px-1.5 py-0.5 rounded-full">ด่วน</span>
          )}
          {item.is_exclusive && (
            <span className="text-xs bg-violet-600 text-white px-1.5 py-0.5 rounded-full">Exclusive</span>
          )}
        </div>
        <p className="text-sm font-medium text-gray-800 leading-snug group-hover:text-violet-700 line-clamp-2">
          {item.title}
        </p>
        <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
          <span>{item.source_name}</span>
          {publishedText && <span>· {publishedText}</span>}
          {item.category && (
            <span className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-500">{item.category}</span>
          )}
        </div>
      </div>
    </div>
  )
}
