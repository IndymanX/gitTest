import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../services/api'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { BarChart2, FileText, Cpu, Rss, Brain } from 'lucide-react'

const PLATFORM_COLORS: Record<string, string> = {
  website: '#3b82f6',
  facebook: '#6366f1',
  twitter: '#0ea5e9',
  line: '#22c55e',
  youtube: '#ef4444',
  instagram: '#ec4899',
  podcast: '#f97316',
  unknown: '#9ca3af',
}

const FORMAT_COLORS = ['#7c3aed', '#2563eb', '#0891b2', '#059669', '#d97706']

function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white border rounded-xl p-5">
      <div className="flex items-center gap-3 mb-2">
        <div className="text-violet-500">{icon}</div>
        <span className="text-sm text-gray-500">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  )
}

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: analyticsApi.getSummary,
    staleTime: 60000,
  })

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400 text-sm">
        กำลังโหลดข้อมูลวิเคราะห์...
      </div>
    )
  }

  if (!data) return null

  const { drafts, tokens, feed, brain, scheduler } = data

  // Platform pie data
  const platformData = Object.entries(drafts.by_platform || {}).map(([name, value]) => ({
    name, value: value as number,
  }))

  // Format bar data
  const formatData = Object.entries(drafts.by_format || {}).map(([name, value]) => ({
    name, value: value as number,
  }))

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart2 className="text-violet-600" /> Analytics
          </h1>
          <p className="text-gray-500 mt-1">ภาพรวมการผลิตเนื้อหาของห้องข่าว</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={<FileText size={20} />}
            label="บทความสร้างทั้งหมด"
            value={drafts.total.toLocaleString()}
            sub={`เฉลี่ย ${drafts.avg_word_count} คำ/ชิ้น`}
          />
          <StatCard
            icon={<Cpu size={20} />}
            label="Token ที่ใช้เดือนนี้"
            value={tokens.monthly_total.toLocaleString()}
            sub="Claude API usage"
          />
          <StatCard
            icon={<Rss size={20} />}
            label="ข่าวใน Feed"
            value={feed.total_items.toLocaleString()}
            sub="รายการในคลัง"
          />
          <StatCard
            icon={<Brain size={20} />}
            label="Brain Maturity"
            value={`${(brain.avg_maturity * 100).toFixed(0)}%`}
            sub={`${brain.total_profiles} โปรไฟล์`}
          />
        </div>

        {/* Draft trend */}
        <div className="bg-white border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-600 mb-4">บทความที่สร้าง — 14 วันล่าสุด</h2>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={drafts.last_14_days} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="draftGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={v => v.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                labelFormatter={v => `วันที่ ${v}`}
                formatter={(v: number) => [`${v} ชิ้น`, 'บทความ']}
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#7c3aed"
                strokeWidth={2}
                fill="url(#draftGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Platform distribution */}
          <div className="bg-white border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-600 mb-4">สัดส่วนแพลตฟอร์ม</h2>
            {platformData.length === 0 ? (
              <div className="flex items-center justify-center h-40 text-gray-300 text-sm">ยังไม่มีข้อมูล</div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={platformData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {platformData.map((entry) => (
                      <Cell key={entry.name} fill={PLATFORM_COLORS[entry.name] || '#9ca3af'} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => [`${v} ชิ้น`]} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Format distribution */}
          <div className="bg-white border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-600 mb-4">ประเภทเนื้อหา</h2>
            {formatData.length === 0 ? (
              <div className="flex items-center justify-center h-40 text-gray-300 text-sm">ยังไม่มีข้อมูล</div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={formatData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip formatter={(v: number) => [`${v} ชิ้น`]} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {formatData.map((_, i) => (
                      <Cell key={i} fill={FORMAT_COLORS[i % FORMAT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Token usage trend */}
        <div className="bg-white border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-600 mb-4">Token Usage — 7 วันล่าสุด</h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={tokens.last_7_days} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={v => v.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                labelFormatter={v => `วันที่ ${v}`}
                formatter={(v: number, name: string) => [
                  v.toLocaleString(),
                  name === 'input_tokens' ? 'Input' : 'Output',
                ]}
              />
              <Legend formatter={v => v === 'input_tokens' ? 'Input tokens' : 'Output tokens'} />
              <Bar dataKey="input_tokens" stackId="t" fill="#7c3aed" radius={[0, 0, 0, 0]} />
              <Bar dataKey="output_tokens" stackId="t" fill="#a78bfa" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-gray-400 mt-2">
            Claude Haiku ≈ $0.25/Mtok · Claude Opus ≈ $15/Mtok input
          </p>
        </div>

        {/* Scheduler summary */}
        {scheduler.pending_posts > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl px-5 py-4 flex items-center gap-3">
            <span className="text-amber-600 font-semibold text-sm">
              {scheduler.pending_posts} โพสต์ที่รอเผยแพร่ตามกำหนดเวลา
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
