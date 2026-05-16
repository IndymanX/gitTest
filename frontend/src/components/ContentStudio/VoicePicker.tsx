import { clsx } from 'clsx'
import type { VoiceProfile, ReadingTone } from '../../types'

const VOICES: { id: VoiceProfile; name: string; emoji: string; gender: string }[] = [
  { id: 'liam', name: 'Liam', emoji: '🎤', gender: 'ชาย' },
  { id: 'rachel', name: 'Rachel', emoji: '👩', gender: 'หญิง' },
  { id: 'adam', name: 'Adam', emoji: '👨', gender: 'ชาย' },
  { id: 'bella', name: 'Bella', emoji: '👱‍♀️', gender: 'หญิง' },
  { id: 'antoni', name: 'Antoni', emoji: '🧑', gender: 'ชาย' },
  { id: 'josh', name: 'Josh', emoji: '🧔', gender: 'ชาย' },
]

const TONES: { id: ReadingTone; label: string; desc: string; icon: string }[] = [
  { id: 'news', label: 'ข่าว', desc: 'ชัดเจน น่าเชื่อถือ', icon: '📰' },
  { id: 'storytelling', label: 'เล่าเรื่อง', desc: 'มีจังหวะ ดึงดูด', icon: '📖' },
  { id: 'casual', label: 'สบายๆ', desc: 'เป็นกันเอง ธรรมชาติ', icon: '💬' },
  { id: 'educational', label: 'สาระ', desc: 'อธิบายชัด เข้าใจง่าย', icon: '🎓' },
  { id: 'drama', label: 'ดราม่า', desc: 'มีอารมณ์ เร้าใจ', icon: '🎭' },
  { id: 'podcast', label: 'พอดแคสต์', desc: 'สบาย เหมือนคุยกัน', icon: '🎧' },
]

const SPEEDS = [
  { value: 0.8, label: '🐢 ช้า', subLabel: '0.8x' },
  { value: 1.0, label: '🎯 ปกติ', subLabel: '1x' },
  { value: 1.1, label: '🚀 เร็ว', subLabel: '1.1x' },
  { value: 1.2, label: '⚡ เร็วมาก', subLabel: '1.2x' },
]

interface VoicePickerProps {
  voiceProfile: VoiceProfile
  readingTone: ReadingTone
  speed: number
  onVoiceChange: (v: VoiceProfile) => void
  onToneChange: (v: ReadingTone) => void
  onSpeedChange: (v: number) => void
}

export default function VoicePicker({
  voiceProfile, readingTone, speed,
  onVoiceChange, onToneChange, onSpeedChange,
}: VoicePickerProps) {
  return (
    <div className="space-y-6">
      {/* Voice profiles */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">🎤 เลือกเสียง</h3>
        <div className="grid grid-cols-3 gap-2">
          {VOICES.map(v => (
            <button
              key={v.id}
              onClick={() => onVoiceChange(v.id)}
              className={clsx(
                'flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 transition-all',
                voiceProfile === v.id
                  ? 'border-teal-500 bg-teal-50'
                  : 'border-gray-100 bg-white hover:border-gray-300',
              )}
            >
              <span className="text-2xl">{v.emoji}</span>
              <span className={clsx('text-sm font-semibold', voiceProfile === v.id ? 'text-teal-700' : 'text-gray-700')}>
                {v.name}
              </span>
              <span className="text-xs text-gray-400">♂ {v.gender}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Speed */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">⚡ ความเร็ว</h3>
        <div className="grid grid-cols-4 gap-2">
          {SPEEDS.map(s => (
            <button
              key={s.value}
              onClick={() => onSpeedChange(s.value)}
              className={clsx(
                'flex flex-col items-center py-2 px-1 rounded-xl border-2 text-center transition-all',
                speed === s.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-100 bg-white hover:border-gray-300 text-gray-600',
              )}
            >
              <span className="text-xs font-semibold">{s.label}</span>
              <span className="text-xs text-gray-400">{s.subLabel}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Reading tone */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">🎭 โทนการอ่าน</h3>
        <div className="grid grid-cols-3 gap-2">
          {TONES.map(t => (
            <button
              key={t.id}
              onClick={() => onToneChange(t.id)}
              className={clsx(
                'flex flex-col items-center gap-1 p-3 rounded-xl border-2 text-center transition-all',
                readingTone === t.id
                  ? 'border-violet-500 bg-violet-50'
                  : 'border-gray-100 bg-white hover:border-gray-300',
              )}
            >
              <span className="text-lg">{t.icon}</span>
              <span className={clsx('text-xs font-semibold', readingTone === t.id ? 'text-violet-700' : 'text-gray-700')}>
                {t.label}
              </span>
              <span className="text-xs text-gray-400">{t.desc}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
