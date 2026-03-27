import type { CopyrightAnalysis } from '../../types'
import { clsx } from 'clsx'
import { Shield, AlertTriangle, CheckCircle, Info } from 'lucide-react'
import { useState } from 'react'

interface Props {
  analysis: CopyrightAnalysis
}

const RISK_CONFIG = {
  low: { color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'ความเสี่ยงต่ำ', icon: CheckCircle },
  medium: { color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', label: 'ระวัง', icon: AlertTriangle },
  high: { color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', label: 'เสี่ยงละเมิด', icon: AlertTriangle },
}

export default function CopyrightPanel({ analysis }: Props) {
  const [expanded, setExpanded] = useState(false)
  const config = RISK_CONFIG[analysis.risk_level]
  const Icon = config.icon

  return (
    <div className={clsx('border rounded-xl overflow-hidden', config.border)}>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={clsx('w-full flex items-center gap-3 px-4 py-3', config.bg, 'hover:brightness-95')}
      >
        <Icon size={16} className={config.color} />
        <span className="font-semibold text-sm text-gray-800">
          วิเคราะห์ลิขสิทธิ์ ({analysis.overall_risk_score}% — {config.label})
        </span>
        <div className="ml-auto flex items-center gap-2">
          {analysis.thai_copyright_act_compliant && (
            <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
              พ.ร.บ. ลิขสิทธิ์ ✓
            </span>
          )}
          <span className="text-xs text-gray-400">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div className="p-4 space-y-4 bg-white">
          {/* Score ring */}
          <div className="flex items-center gap-6">
            <ScoreRing score={analysis.overall_risk_score} riskLevel={analysis.risk_level} />
            <div className="flex-1 space-y-2">
              <ScoreBar label="เนื้อหา" score={analysis.risk_breakdown?.เนื้อหา ?? analysis.content_similarity_score} />
              <ScoreBar label="สำนวน" score={analysis.risk_breakdown?.สำนวน ?? analysis.style_similarity_score} />
              <ScoreBar label="โครงสร้าง" score={analysis.risk_breakdown?.โครงสร้าง ?? analysis.structure_similarity_score} />
            </div>
          </div>

          {/* Fair use notice */}
          {analysis.fair_use_applicable && analysis.fair_use_reason && (
            <div className="flex gap-2 text-xs text-blue-700 bg-blue-50 rounded-lg p-3">
              <Info size={14} className="shrink-0 mt-0.5" />
              <span>{analysis.fair_use_reason}</span>
            </div>
          )}

          {/* Recommendations */}
          {analysis.recommendations.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-2">คำแนะนำ</h4>
              <ul className="space-y-1">
                {analysis.recommendations.map((rec, i) => (
                  <li key={i} className="text-xs text-gray-600 flex gap-2">
                    <span className="text-amber-500 shrink-0">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Source chain */}
          {analysis.source_chain.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-2">Source Chain Transparency</h4>
              <div className="space-y-1">
                {analysis.source_chain.map((s, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-gray-500">
                    <span className="w-4 h-4 bg-gray-100 rounded-full flex items-center justify-center text-gray-400 shrink-0">{i + 1}</span>
                    <span className="font-medium text-gray-700">{s.source_name}</span>
                    <span className="bg-gray-100 px-1.5 py-0.5 rounded">
                      {(s as { transform_level_label?: string }).transform_level_label || `ระดับ ${s.transform_level}`}
                    </span>
                    {s.is_licensed && (
                      <span className="text-amber-600">© สงวนสิทธิ์</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scale */}
          <div className="flex gap-3 text-xs pt-2 border-t">
            <span className="text-emerald-600">● 0-30% ปลอดภัย</span>
            <span className="text-amber-600">● 31-60% ระวัง</span>
            <span className="text-red-600">● 61-100% เสี่ยงละเมิด</span>
          </div>
        </div>
      )}
    </div>
  )
}

function ScoreRing({ score, riskLevel }: { score: number; riskLevel: string }) {
  const colors = { low: '#10B981', medium: '#F59E0B', high: '#EF4444' }
  const textColors = { low: 'text-emerald-600', medium: 'text-amber-600', high: 'text-red-600' }
  const color = colors[riskLevel as keyof typeof colors] || colors.low
  const radius = 28
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference - (score / 100) * circumference

  return (
    <div className="relative w-20 h-20">
      <svg className="w-20 h-20 -rotate-90" viewBox="0 0 72 72">
        <circle cx="36" cy="36" r={radius} fill="none" stroke="#E5E7EB" strokeWidth="6" />
        <circle
          cx="36" cy="36" r={radius} fill="none"
          stroke={color} strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={clsx('text-lg font-bold', textColors[riskLevel as keyof typeof textColors])}>
          {score.toFixed(0)}%
        </span>
      </div>
    </div>
  )
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  const color = score < 30 ? 'bg-emerald-500' : score < 60 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-600 w-16 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all', color)} style={{ width: `${Math.min(score, 100)}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-700 w-8 text-right">{score.toFixed(0)}%</span>
    </div>
  )
}
