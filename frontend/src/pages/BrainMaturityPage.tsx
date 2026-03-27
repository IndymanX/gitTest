import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { brainApi } from '../services/api'
import { Brain, Upload, TrendingUp, BookOpen } from 'lucide-react'
import { clsx } from 'clsx'
import { toast } from 'sonner'

const DEFAULT_ORG_PROFILE = 'org-default'

export default function BrainMaturityPage() {
  const [sampleText, setSampleText] = useState('')
  const [feedback, setFeedback] = useState<'accepted' | 'rejected' | 'edited'>('accepted')
  const [editedVersion, setEditedVersion] = useState('')
  const [showEdited, setShowEdited] = useState(false)

  const { data: profileData, refetch } = useQuery({
    queryKey: ['brain-profile', DEFAULT_ORG_PROFILE],
    queryFn: () => brainApi.getProfile(DEFAULT_ORG_PROFILE),
    retry: false,
  })

  const createMutation = useMutation({
    mutationFn: () => brainApi.createProfile({
      profile_id: DEFAULT_ORG_PROFILE,
      name: 'องค์กรหลัก',
      organization_id: 'org-1',
    }),
    onSuccess: () => { toast.success('สร้าง Profile สำเร็จ'); refetch() },
  })

  const learnMutation = useMutation({
    mutationFn: () => brainApi.learn({
      profile_id: DEFAULT_ORG_PROFILE,
      sample_text: sampleText,
      feedback,
      edited_version: showEdited ? editedVersion : undefined,
    }),
    onSuccess: (data) => {
      toast.success(`เรียนรู้สำเร็จ! Maturity: ${data.profile.maturity_score.toFixed(1)}%`)
      setSampleText('')
      setEditedVersion('')
      refetch()
    },
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  const profile = profileData?.profile
  const report = profileData?.report

  const maturity = profile?.maturity_score || 0
  const maturityColor = maturity >= 75 ? 'text-emerald-600' : maturity >= 50 ? 'text-violet-600' : maturity >= 20 ? 'text-amber-600' : 'text-gray-400'

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Brain className="text-violet-600" />
            AI Brain Maturity
          </h1>
          <p className="text-gray-500 mt-1">สอนระบบให้รู้จักสไตล์การเขียนของคุณและองค์กร</p>
        </div>

        {!profile && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center justify-between">
            <p className="text-sm text-amber-700">ยังไม่มี Brain Profile — สร้าง Profile เพื่อเริ่มต้น</p>
            <button
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending}
              className="text-sm bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700"
            >
              สร้าง Profile
            </button>
          </div>
        )}

        {profile && report && (
          <>
            {/* Maturity gauge */}
            <div className="bg-white border rounded-xl p-6">
              <div className="flex items-center gap-6">
                {/* Big score */}
                <div className="text-center">
                  <div className={clsx('text-5xl font-bold', maturityColor)}>
                    {maturity.toFixed(0)}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">Maturity Score</div>
                  <div className={clsx('text-sm font-semibold mt-1', maturityColor)}>{report.level}</div>
                </div>

                <div className="flex-1">
                  <p className="text-sm text-gray-600 mb-4">{report.description}</p>

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <Stat label="ตัวอย่าง" value={report.samples_learned} />
                    <Stat label="อนุมัติ" value={`${report.acceptance_rate}%`} color="emerald" />
                    <Stat label="เป้าถัดไป" value={`${report.next_milestone.target_score}%`} color="violet" />
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mt-4 bg-gray-100 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-gradient-to-r from-violet-500 to-emerald-500 transition-all"
                  style={{ width: `${maturity}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>เริ่มต้น</span>
                <span>กำลังพัฒนา</span>
                <span>เชี่ยวชาญ</span>
                <span>สมบูรณ์แบบ</span>
              </div>
            </div>

            {/* Next milestone */}
            <div className="bg-violet-50 border border-violet-100 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <TrendingUp size={16} className="text-violet-600 mt-0.5" />
                <div>
                  <div className="text-sm font-semibold text-violet-700">
                    เป้าถัดไป: {report.next_milestone.milestone_name}
                  </div>
                  <div className="text-xs text-violet-600 mt-0.5">{report.next_milestone.action_needed}</div>
                </div>
              </div>
            </div>

            {/* Top vocabulary */}
            {report.top_vocabulary.length > 0 && (
              <div className="bg-white border rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
                  <BookOpen size={14} /> คำที่ใช้บ่อย (สไตล์ของคุณ)
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {report.top_vocabulary.map((word, i) => (
                    <span key={i} className="text-xs bg-violet-50 text-violet-700 px-2.5 py-1 rounded-full border border-violet-100">
                      {word}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Learn form */}
        {profile && (
          <div className="bg-white border rounded-xl p-6 space-y-4">
            <h2 className="font-semibold text-gray-800 flex items-center gap-2">
              <Upload size={16} className="text-violet-600" />
              เพิ่มตัวอย่างการเรียนรู้
            </h2>

            <div>
              <label className="text-xs font-medium text-gray-500 block mb-1.5">บทความตัวอย่าง</label>
              <textarea
                value={sampleText}
                onChange={e => setSampleText(e.target.value)}
                placeholder="วางบทความข่าวที่เขียนในสไตล์ที่ต้องการสอนระบบ..."
                className="w-full border rounded-lg p-3 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500 min-h-[150px] resize-y"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500 block mb-1.5">Feedback จากบรรณาธิการ</label>
              <div className="flex gap-2">
                {([
                  ['accepted', '✅ อนุมัติ', 'emerald'],
                  ['rejected', '❌ ปฏิเสธ', 'red'],
                  ['edited', '✏️ แก้ไข', 'amber'],
                ] as const).map(([value, label, color]) => (
                  <button
                    key={value}
                    onClick={() => { setFeedback(value); setShowEdited(value === 'edited') }}
                    className={clsx(
                      'flex-1 py-2 text-sm rounded-lg border font-medium transition-colors',
                      feedback === value
                        ? color === 'emerald' ? 'bg-emerald-600 text-white border-emerald-600'
                        : color === 'red' ? 'bg-red-500 text-white border-red-500'
                        : 'bg-amber-500 text-white border-amber-500'
                        : 'border-gray-200 text-gray-600 hover:border-gray-300',
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {showEdited && (
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1.5">ฉบับที่แก้ไขแล้ว</label>
                <textarea
                  value={editedVersion}
                  onChange={e => setEditedVersion(e.target.value)}
                  placeholder="วางฉบับที่บรรณาธิการแก้ไขแล้ว เพื่อให้ระบบเรียนรู้จากการเปลี่ยนแปลง..."
                  className="w-full border rounded-lg p-3 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500 min-h-[120px] resize-y"
                />
              </div>
            )}

            <button
              onClick={() => learnMutation.mutate()}
              disabled={learnMutation.isPending || !sampleText.trim()}
              className="w-full flex items-center justify-center gap-2 bg-violet-600 text-white py-3 rounded-lg hover:bg-violet-700 disabled:opacity-50 font-medium"
            >
              <Brain size={16} />
              {learnMutation.isPending ? 'กำลังเรียนรู้...' : 'สอนระบบ'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value, color }: { label: string; value: string | number; color?: string }) {
  const colors: Record<string, string> = {
    emerald: 'text-emerald-600',
    violet: 'text-violet-600',
    default: 'text-gray-900',
  }
  return (
    <div>
      <div className={clsx('text-xl font-bold', colors[color || 'default'])}>{value}</div>
      <div className="text-xs text-gray-400">{label}</div>
    </div>
  )
}
