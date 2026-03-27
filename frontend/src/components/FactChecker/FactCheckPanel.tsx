import type { FactCheckResult } from '../../types'
import { clsx } from 'clsx'
import { AlertCircle, CheckSquare } from 'lucide-react'
import { useState } from 'react'

interface Props {
  result: FactCheckResult
}

export default function FactCheckPanel({ result }: Props) {
  const [expanded, setExpanded] = useState(false)

  if (!result.has_claims) {
    return (
      <div className="flex items-center gap-2 text-xs text-emerald-600 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
        <CheckSquare size={14} />
        <span>ไม่พบข้ออ้างที่ต้องตรวจสอบเป็นพิเศษ</span>
      </div>
    )
  }

  const riskColors = {
    low: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    medium: 'bg-amber-50 border-amber-200 text-amber-700',
    high: 'bg-red-50 border-red-200 text-red-700',
  }

  return (
    <div className={clsx('border rounded-xl overflow-hidden', riskColors[result.overall_risk].split(' ')[1])}>
      <button
        onClick={() => setExpanded(!expanded)}
        className={clsx('w-full flex items-center gap-3 px-4 py-3', riskColors[result.overall_risk].split(' ')[0])}
      >
        <AlertCircle size={16} className={riskColors[result.overall_risk].split(' ')[2]} />
        <span className="font-semibold text-sm text-gray-800">
          Fact Check — พบ {result.total_claims} ข้ออ้าง (คะแนน {result.fact_check_score.toFixed(0)}/100)
        </span>
        <span className="ml-auto text-xs text-gray-400">{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div className="p-4 bg-white space-y-4">
          {/* Checklist */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 mb-2">รายการตรวจสอบ</h4>
            <div className="space-y-2">
              {result.checklist.map((item, i) => (
                <div key={i} className="flex items-start gap-2">
                  <PriorityDot priority={item.priority} />
                  <span className="text-xs text-gray-600 leading-snug">{item.task}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-2">คำแนะนำ</h4>
              <ul className="space-y-1">
                {result.recommendations.map((rec, i) => (
                  <li key={i} className="text-xs text-gray-600 flex gap-2">
                    <span className="text-violet-400 shrink-0">→</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function PriorityDot({ priority }: { priority: number }) {
  const config = priority >= 4
    ? 'bg-red-500' : priority >= 3
    ? 'bg-amber-500' : 'bg-emerald-500'
  return <div className={clsx('w-2 h-2 rounded-full shrink-0 mt-1', config)} />
}
