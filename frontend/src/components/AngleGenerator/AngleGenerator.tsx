import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { draftApi } from '../../services/api'
import type { NewsItem, ContentAngle } from '../../types'
import { Layers, ArrowRight, Zap } from 'lucide-react'
import { clsx } from 'clsx'
import { toast } from 'sonner'

interface Props {
  selectedItem?: NewsItem | null
  onSelectAngle?: (angle: ContentAngle) => void
}

const EFFORT_COLORS = {
  low: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-red-100 text-red-700',
}

const EFFORT_LABELS = {
  low: 'ง่าย',
  medium: 'ปานกลาง',
  high: 'ยาก',
}

export default function AngleGenerator({ selectedItem, onSelectAngle }: Props) {
  const [angles, setAngles] = useState<ContentAngle[]>([])
  const [planSummary, setPlanSummary] = useState('')
  const [numAngles, setNumAngles] = useState(5)

  const generateMutation = useMutation({
    mutationFn: () => draftApi.generateAngles(
      selectedItem || { title: 'ทดสอบ' },
      numAngles,
    ),
    onSuccess: (data) => {
      setAngles(data.angles)
      setPlanSummary(data.content_plan_summary)
      toast.success(`สร้าง ${data.total} มุมมองสำเร็จ`)
    },
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3">
        <div className="flex items-center gap-2 mb-3">
          <Layers size={16} className="text-violet-600" />
          <h2 className="font-semibold text-gray-800">Angle Generator</h2>
          <span className="text-xs text-gray-400 ml-1">1 ข่าว → หลายมุมมอง</span>
        </div>

        {selectedItem && (
          <div className="text-xs text-gray-600 bg-violet-50 rounded-lg px-3 py-2 mb-3 border border-violet-100 line-clamp-2">
            📰 {selectedItem.title}
          </div>
        )}

        <div className="flex gap-2">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-gray-500">จำนวนมุม:</span>
            {[3, 5, 8].map(n => (
              <button
                key={n}
                onClick={() => setNumAngles(n)}
                className={clsx(
                  'w-8 h-7 rounded border font-medium transition-colors',
                  numAngles === n
                    ? 'bg-violet-600 text-white border-violet-600'
                    : 'border-gray-200 text-gray-600 hover:border-violet-400',
                )}
              >
                {n}
              </button>
            ))}
          </div>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="ml-auto flex items-center gap-1.5 text-xs bg-emerald-600 text-white px-4 py-1.5 rounded-lg hover:bg-emerald-700 disabled:opacity-50 font-medium"
          >
            <Zap size={12} />
            {generateMutation.isPending ? 'กำลังสร้าง...' : 'สร้างมุมมอง'}
          </button>
        </div>
      </div>

      {/* Content plan summary */}
      {planSummary && (
        <div className="bg-gray-50 border-b px-4 py-2">
          <h3 className="text-xs font-semibold text-gray-500 mb-1">Content Plan</h3>
          <pre className="text-xs text-gray-600 whitespace-pre-wrap font-sans">{planSummary}</pre>
        </div>
      )}

      {/* Angle cards */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {generateMutation.isPending && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="animate-pulse bg-gray-100 rounded-xl h-32" />
            ))}
          </div>
        )}

        {!generateMutation.isPending && angles.length === 0 && (
          <div className="flex flex-col items-center justify-center h-48 text-gray-300 gap-2">
            <Layers size={36} />
            <p className="text-sm">เลือกข่าวแล้วกด "สร้างมุมมอง"</p>
          </div>
        )}

        {angles.map((angle, i) => (
          <AngleCard
            key={i}
            angle={angle}
            index={i + 1}
            onSelect={() => onSelectAngle?.(angle)}
          />
        ))}
      </div>
    </div>
  )
}

function AngleCard({ angle, index, onSelect }: { angle: ContentAngle; index: number; onSelect: () => void }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-white border rounded-xl overflow-hidden hover:border-violet-300 transition-colors">
      <div
        className="flex items-start gap-3 px-4 py-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="w-7 h-7 bg-violet-100 text-violet-700 rounded-lg flex items-center justify-center text-sm font-bold shrink-0">
          {index}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-xs font-semibold text-violet-600">{angle.angle_name_th}</span>
            <span className={clsx('text-xs px-1.5 py-0.5 rounded-full font-medium', EFFORT_COLORS[angle.estimated_effort])}>
              {EFFORT_LABELS[angle.estimated_effort]}
            </span>
            <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
              {angle.best_platform}
            </span>
          </div>
          <p className="text-sm font-medium text-gray-800 line-clamp-2">{angle.proposed_title}</p>
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t space-y-3 bg-gray-50">
          <div className="pt-3">
            <label className="text-xs text-gray-500 block mb-1">Hook</label>
            <p className="text-sm text-gray-700 italic">"{angle.hook}"</p>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1">คำถามที่บทความต้องตอบ</label>
            <ul className="space-y-1">
              {angle.key_questions?.map((q, i) => (
                <li key={i} className="text-xs text-gray-600 flex gap-1.5">
                  <span className="text-violet-400 shrink-0">?</span> {q}
                </li>
              ))}
            </ul>
          </div>

          {angle.research_needed?.length > 0 && (
            <div>
              <label className="text-xs text-gray-500 block mb-1">ต้องค้นคว้าเพิ่ม</label>
              <div className="flex flex-wrap gap-1">
                {angle.research_needed.map((r, i) => (
                  <span key={i} className="text-xs bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full border border-amber-100">{r}</span>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={onSelect}
            className="flex items-center gap-1.5 text-xs bg-violet-600 text-white px-4 py-2 rounded-lg hover:bg-violet-700 w-full justify-center font-medium"
          >
            ใช้มุมนี้ในการเขียน <ArrowRight size={12} />
          </button>
        </div>
      )}
    </div>
  )
}
