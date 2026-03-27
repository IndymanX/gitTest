import { useQuery } from '@tanstack/react-query'
import { feedApi } from '../../services/api'
import type { NewsItem } from '../../types'
import { Brain, TrendingUp, Lightbulb, AlertCircle, RefreshCw } from 'lucide-react'

interface Props {
  onSelectStory?: (title: string) => void
}

export default function EditorBrief({ onSelectStory }: Props) {
  const { data: brief, isLoading, refetch } = useQuery({
    queryKey: ['editor-brief'],
    queryFn: feedApi.getEditorBrief,
    staleTime: 5 * 60 * 1000,
  })

  return (
    <div className="flex flex-col h-full">
      <div className="bg-white border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <Brain size={16} className="text-violet-600" />
          <h2 className="font-semibold text-gray-800">Editor Brief Intelligence</h2>
          <button
            onClick={() => refetch()}
            className="ml-auto text-gray-400 hover:text-gray-600"
          >
            <RefreshCw size={14} />
          </button>
        </div>
        {brief && (
          <p className="text-xs text-gray-400 mt-1">{brief.total_items} ข่าว · อัพเดท {new Date(brief.processed_at).toLocaleTimeString('th-TH')}</p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading && (
          <div className="space-y-3 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-4 bg-gray-100 rounded w-full" />
            <div className="h-4 bg-gray-100 rounded w-5/6" />
          </div>
        )}

        {!isLoading && !brief?.top_stories?.length && (
          <div className="text-center text-gray-400 text-sm py-10">
            <Brain size={32} className="mx-auto mb-2 opacity-30" />
            <p>ยังไม่มีข้อมูล กรุณาดึงข่าวก่อน</p>
          </div>
        )}

        {brief && (
          <>
            {/* Trend summary */}
            {brief.trend_summary && (
              <div className="bg-violet-50 border border-violet-100 rounded-xl p-3">
                <div className="flex items-center gap-1.5 mb-1 text-xs font-semibold text-violet-600">
                  <TrendingUp size={12} /> ภาพรวมวันนี้
                </div>
                <p className="text-sm text-gray-700">{brief.trend_summary}</p>
              </div>
            )}

            {/* Top stories — Must act now */}
            {brief.top_stories?.length > 0 && (
              <Section title="🔥 ต้องทำทันที" color="red">
                {brief.top_stories.map((s, i) => (
                  <StoryItem
                    key={i} index={i + 1} title={s.title}
                    reason={s.reason}
                    urgent
                    onClick={() => onSelectStory?.(s.title)}
                  />
                ))}
              </Section>
            )}

            {/* Can wait */}
            {brief.can_wait_stories?.length > 0 && (
              <Section title="🕐 รอได้" color="gray">
                {brief.can_wait_stories.map((s, i) => (
                  <StoryItem
                    key={i} index={i + 1} title={s.title}
                    onClick={() => onSelectStory?.(s.title)}
                  />
                ))}
              </Section>
            )}

            {/* Editor recommendations */}
            {brief.editor_recommendations?.length > 0 && (
              <Section title="💡 คำแนะนำบรรณาธิการ" color="amber">
                {brief.editor_recommendations.map((rec, i) => (
                  <li key={i} className="text-xs text-gray-600 flex gap-2 list-none">
                    <AlertCircle size={12} className="text-amber-500 shrink-0 mt-0.5" />
                    {rec}
                  </li>
                ))}
              </Section>
            )}

            {/* Exclusive opportunities */}
            {brief.exclusive_opportunities?.length > 0 && (
              <Section title="⚡ โอกาสข่าวเจาะ" color="purple">
                {brief.exclusive_opportunities.map((opp, i) => (
                  <li key={i} className="text-xs text-gray-600 flex gap-2 list-none">
                    <Lightbulb size={12} className="text-violet-500 shrink-0 mt-0.5" />
                    {opp}
                  </li>
                ))}
              </Section>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function Section({ title, color, children }: { title: string; color: string; children: React.ReactNode }) {
  const borderColors: Record<string, string> = {
    red: 'border-red-100',
    amber: 'border-amber-100',
    purple: 'border-violet-100',
    gray: 'border-gray-100',
  }
  return (
    <div className={`border rounded-xl overflow-hidden ${borderColors[color] || 'border-gray-100'}`}>
      <div className="px-3 py-2 bg-gray-50 border-b">
        <h3 className="text-xs font-semibold text-gray-600">{title}</h3>
      </div>
      <div className="p-3 space-y-2 bg-white">{children}</div>
    </div>
  )
}

function StoryItem({
  index, title, reason, urgent, onClick,
}: {
  index: number; title: string; reason?: string; urgent?: boolean; onClick?: () => void
}) {
  return (
    <div
      onClick={onClick}
      className="flex gap-2.5 cursor-pointer hover:bg-gray-50 rounded-lg p-1.5 -mx-1.5 transition-colors"
    >
      <span className={`w-5 h-5 rounded flex items-center justify-center text-xs font-bold shrink-0 ${urgent ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
        {index}
      </span>
      <div>
        <p className="text-sm text-gray-800 leading-snug">{title}</p>
        {reason && <p className="text-xs text-gray-400 mt-0.5">{reason}</p>}
      </div>
    </div>
  )
}
