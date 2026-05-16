import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '../services/api'
import { Settings, Rss, BookOpen, Plus, Trash2, Download, Save } from 'lucide-react'
import { clsx } from 'clsx'
import { toast } from 'sonner'

type Tab = 'feeds' | 'style'

const STRUCTURE_OPTIONS = [
  { value: 'inverted_pyramid', label: 'Inverted Pyramid', desc: 'สำคัญที่สุดก่อน (มาตรฐานข่าว)' },
  { value: 'narrative', label: 'Narrative', desc: 'เล่าเป็นเรื่องราว' },
  { value: 'explainer', label: 'Explainer', desc: 'อธิบาย สาระ ให้ความรู้' },
  { value: 'listicle', label: 'Listicle', desc: 'รายการหัวข้อ อ่านง่าย' },
]

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>('feeds')

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Settings className="text-violet-600" /> ตั้งค่าระบบ
          </h1>
          <p className="text-gray-500 mt-1">จัดการแหล่งข่าว RSS และ Style Constitution ของสำนักข่าว</p>
        </div>

        {/* Tab bar */}
        <div className="flex border-b">
          <TabBtn active={tab === 'feeds'} onClick={() => setTab('feeds')} icon={<Rss size={15} />} label="แหล่งข่าว RSS" />
          <TabBtn active={tab === 'style'} onClick={() => setTab('style')} icon={<BookOpen size={15} />} label="Style Constitution" />
        </div>

        {tab === 'feeds' && <FeedsTab />}
        {tab === 'style' && <StyleConstitutionTab />}
      </div>
    </div>
  )
}

// ── RSS Feeds Tab ─────────────────────────────────────────────────────────────

function FeedsTab() {
  const qc = useQueryClient()
  const [newName, setNewName] = useState('')
  const [newUrl, setNewUrl] = useState('')
  const [newReliability, setNewReliability] = useState(0.8)

  const { data, isLoading } = useQuery({
    queryKey: ['settings-feeds'],
    queryFn: settingsApi.listFeeds,
    refetchInterval: 10000,
  })

  const addMutation = useMutation({
    mutationFn: () => settingsApi.addFeed({ name: newName, url: newUrl, reliability_score: newReliability }),
    onSuccess: () => {
      toast.success('เพิ่มแหล่งข่าวสำเร็จ')
      setNewName(''); setNewUrl('')
      qc.invalidateQueries({ queryKey: ['settings-feeds'] })
    },
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => settingsApi.removeFeed(id),
    onSuccess: () => {
      toast.success('ลบแหล่งข่าวสำเร็จ')
      qc.invalidateQueries({ queryKey: ['settings-feeds'] })
    },
  })

  const loadDefaultsMutation = useMutation({
    mutationFn: settingsApi.loadThaiDefaults,
    onSuccess: (data) => {
      toast.success(data.message)
      qc.invalidateQueries({ queryKey: ['settings-feeds'] })
    },
  })

  const sources = data?.sources || []

  return (
    <div className="space-y-4">
      {/* One-click Thai defaults */}
      <div className="bg-violet-50 border border-violet-100 rounded-xl p-4 flex items-center justify-between">
        <div>
          <div className="font-semibold text-violet-800 text-sm">โหลดแหล่งข่าวไทยยอดนิยม</div>
          <div className="text-xs text-violet-600 mt-0.5">ไทยรัฐ, มติชน, PPTV, The Standard, ประชาไท, Bangkok Post, ข่าวสด, BBC Thai</div>
        </div>
        <button
          onClick={() => loadDefaultsMutation.mutate()}
          disabled={loadDefaultsMutation.isPending}
          className="flex items-center gap-1.5 bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 disabled:opacity-50 shrink-0"
        >
          <Download size={14} />
          {loadDefaultsMutation.isPending ? 'กำลังโหลด...' : 'โหลดแหล่งข่าวไทย'}
        </button>
      </div>

      {/* Add form */}
      <div className="bg-white border rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
          <Plus size={14} className="text-violet-600" /> เพิ่มแหล่งข่าวใหม่
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="ชื่อสำนักข่าว"
            className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
          />
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 shrink-0">ความน่าเชื่อ:</span>
            <input
              type="range" min="0.5" max="1.0" step="0.05"
              value={newReliability}
              onChange={e => setNewReliability(Number(e.target.value))}
              className="flex-1"
            />
            <span className="text-xs font-medium text-gray-700 w-8">{(newReliability * 100).toFixed(0)}%</span>
          </div>
        </div>
        <div className="flex gap-2">
          <input
            value={newUrl}
            onChange={e => setNewUrl(e.target.value)}
            placeholder="RSS Feed URL (https://...)"
            className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
          />
          <button
            onClick={() => addMutation.mutate()}
            disabled={addMutation.isPending || !newName.trim() || !newUrl.trim()}
            className="bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 disabled:opacity-50"
          >
            เพิ่ม
          </button>
        </div>
      </div>

      {/* Sources list */}
      <div className="bg-white border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50 text-xs font-semibold text-gray-500 flex items-center justify-between">
          <span>แหล่งข่าวที่กำหนดค่า ({sources.length} แหล่ง)</span>
          {isLoading && <span className="text-violet-500">กำลังโหลด...</span>}
        </div>
        {sources.length === 0 ? (
          <div className="py-8 text-center text-gray-400 text-sm">
            <Rss size={24} className="mx-auto mb-2 opacity-30" />
            ยังไม่มีแหล่งข่าว — กด "โหลดแหล่งข่าวไทย" หรือเพิ่มเอง
          </div>
        ) : (
          sources.map((source: { id: string; name: string; url: string; reliability_score: number }) => (
            <div key={source.id} className="flex items-center gap-3 px-4 py-3 border-b last:border-0 hover:bg-gray-50">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-800">{source.name}</div>
                <div className="text-xs text-gray-400 truncate">{source.url}</div>
              </div>
              <ReliabilityBadge score={source.reliability_score} />
              <button
                onClick={() => deleteMutation.mutate(source.id)}
                className="text-gray-300 hover:text-red-500 transition-colors"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function ReliabilityBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 85 ? 'bg-emerald-100 text-emerald-700' : pct >= 70 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
  return <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium shrink-0', color)}>{pct}%</span>
}

// ── Style Constitution Tab ────────────────────────────────────────────────────

function StyleConstitutionTab() {
  const qc = useQueryClient()

  const { data } = useQuery({
    queryKey: ['style-constitution'],
    queryFn: settingsApi.getStyleConstitution,
  })

  const sc = data?.style_constitution || {}
  const [formality, setFormality] = useState<number>(sc.formality_level ?? 0.7)
  const [structure, setStructure] = useState<string>(sc.preferred_structure ?? 'inverted_pyramid')
  const [forbiddenWords, setForbiddenWords] = useState<string>(
    (sc.forbidden_words || []).join(', ')
  )
  const [brandVoice, setBrandVoice] = useState<string>(
    (sc.brand_voice_markers || []).join(', ')
  )
  const [minSources, setMinSources] = useState<number>(sc.min_sources_required ?? 2)

  const saveMutation = useMutation({
    mutationFn: () => settingsApi.saveStyleConstitution({
      formality_level: formality,
      preferred_structure: structure,
      forbidden_words: forbiddenWords.split(',').map(w => w.trim()).filter(Boolean),
      brand_voice_markers: brandVoice.split(',').map(w => w.trim()).filter(Boolean),
      avg_sentence_length: 20,
      requires_source_attribution: true,
      min_sources_required: minSources,
    }),
    onSuccess: () => {
      toast.success('บันทึก Style Constitution สำเร็จ')
      qc.invalidateQueries({ queryKey: ['style-constitution'] })
    },
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  return (
    <div className="space-y-5">
      {data?.is_default && (
        <div className="text-xs text-amber-600 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
          ใช้ค่าเริ่มต้น — กำหนดสไตล์ขององค์กรเพื่อให้ AI เขียนได้ตรงกับเอกลักษณ์ของคุณ
        </div>
      )}

      {/* Formality */}
      <div className="bg-white border rounded-xl p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">ระดับทางการ</h3>
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-400 shrink-0">เป็นกันเอง</span>
          <input
            type="range" min="0" max="1" step="0.1"
            value={formality}
            onChange={e => setFormality(Number(e.target.value))}
            className="flex-1 accent-violet-600"
          />
          <span className="text-xs text-gray-400 shrink-0">ทางการมาก</span>
          <span className="text-sm font-bold text-violet-600 w-12 text-right">
            {formality <= 0.3 ? 'เป็นกันเอง' : formality <= 0.6 ? 'กึ่งทางการ' : 'ทางการ'}
          </span>
        </div>
      </div>

      {/* Preferred structure */}
      <div className="bg-white border rounded-xl p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">โครงสร้างบทความที่ต้องการ</h3>
        <div className="grid grid-cols-2 gap-2">
          {STRUCTURE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setStructure(opt.value)}
              className={clsx(
                'text-left p-3 rounded-xl border-2 transition-colors',
                structure === opt.value
                  ? 'border-violet-500 bg-violet-50'
                  : 'border-gray-100 hover:border-gray-300',
              )}
            >
              <div className={clsx('text-sm font-semibold', structure === opt.value ? 'text-violet-700' : 'text-gray-700')}>
                {opt.label}
              </div>
              <div className="text-xs text-gray-400 mt-0.5">{opt.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Vocabulary */}
      <div className="bg-white border rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700">คำศัพท์และเอกลักษณ์</h3>
        <div>
          <label className="text-xs text-gray-500 block mb-1.5">คำที่ห้ามใช้ (คั่นด้วย ,)</label>
          <input
            value={forbiddenWords}
            onChange={e => setForbiddenWords(e.target.value)}
            placeholder="เช่น เสียชีวิต, ดับ, โดนฆ่า"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1.5">เอกลักษณ์สำนักข่าว / Brand Voice (คั่นด้วย ,)</label>
          <input
            value={brandVoice}
            onChange={e => setBrandVoice(e.target.value)}
            placeholder="เช่น รายงานพิเศษ, ผู้สื่อข่าวรายงาน, ข้อมูลเพิ่มเติมพบได้ที่..."
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1.5">จำนวนแหล่งข่าวขั้นต่ำ</label>
          <div className="flex gap-2">
            {[1, 2, 3, 4].map(n => (
              <button
                key={n}
                onClick={() => setMinSources(n)}
                className={clsx(
                  'w-10 h-9 rounded-lg border text-sm font-medium',
                  minSources === n ? 'bg-violet-600 text-white border-violet-600' : 'border-gray-200 text-gray-600 hover:border-violet-400',
                )}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button
        onClick={() => saveMutation.mutate()}
        disabled={saveMutation.isPending}
        className="w-full flex items-center justify-center gap-2 bg-violet-600 text-white py-3 rounded-xl hover:bg-violet-700 disabled:opacity-50 font-medium"
      >
        <Save size={16} />
        {saveMutation.isPending ? 'กำลังบันทึก...' : 'บันทึก Style Constitution'}
      </button>
    </div>
  )
}

function TabBtn({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
        active ? 'text-violet-700 border-violet-600' : 'text-gray-500 border-transparent hover:text-gray-700',
      )}
    >
      {icon} {label}
    </button>
  )
}
