import { clsx } from 'clsx'
import type { ImageStyle, AspectRatio, CameraAngle } from '../../types'

// ── Image Style ──────────────────────────────────────────────────────────────

const IMAGE_STYLES: { id: ImageStyle; label: string; icon: string; desc: string }[] = [
  { id: 'photorealistic', label: 'Photorealistic', icon: '📸', desc: 'ภาพถ่ายจริง' },
  { id: 'cinematic', label: 'Cinematic', icon: '🎬', desc: 'สไตล์หนัง' },
  { id: 'illustration', label: 'Illustration', icon: '🎨', desc: 'ภาพวาด' },
  { id: 'minimalist', label: 'Minimalist', icon: '⬜', desc: 'เรียบง่าย' },
  { id: 'abstract', label: 'Abstract', icon: '🔷', desc: 'นามธรรม' },
  { id: 'news_style', label: 'News Style', icon: '📰', desc: 'สไตล์ข่าว' },
]

const ASPECT_RATIOS: { id: AspectRatio; label: string; desc: string; icon: string }[] = [
  { id: '16:9', label: '16:9', desc: 'YouTube / Blog', icon: '🖥️' },
  { id: '1:1', label: '1:1', desc: 'IG / FB Post', icon: '⬛' },
  { id: '9:16', label: '9:16', desc: 'Reels / TikTok', icon: '📱' },
  { id: '4:5', label: '4:5', desc: 'IG สี่เหลี่ยม', icon: '🖼️' },
  { id: '3:2', label: '3:2', desc: 'Twitter / X', icon: '🐦' },
  { id: '4:3', label: '4:3', desc: 'Presentation', icon: '📊' },
]

const CAMERA_ANGLES: { id: CameraAngle; label: string; desc: string }[] = [
  { id: 'eye_level', label: 'Eye Level', desc: 'มุมตรง (ปกติ)' },
  { id: 'aerial', label: 'Aerial', desc: 'มุมสูง / โดรน' },
  { id: 'low_angle', label: 'Low Angle', desc: 'มุมต่ำ ดูยิ่งใหญ่' },
  { id: 'high_angle', label: 'High Angle', desc: 'มุมกดลง' },
  { id: 'close_up', label: 'Close-Up', desc: 'ถ่ายใกล้ / แมโคร' },
  { id: 'wide_angle', label: 'Wide Angle', desc: 'มุมกว้าง / พาโนรามา' },
  { id: 'over_shoulder', label: 'Over Shoulder', desc: 'มุมข้ามไหล่' },
  { id: 'dutch_angle', label: 'Dutch Angle', desc: 'เอียง / ดราม่า' },
  { id: 'isometric', label: 'Isometric', desc: 'มุม 3 มิติ' },
]

interface ImageStylePickerProps {
  imageStyle: ImageStyle
  aspectRatio: AspectRatio
  cameraAngle: CameraAngle
  onImageStyleChange: (v: ImageStyle) => void
  onAspectRatioChange: (v: AspectRatio) => void
  onCameraAngleChange: (v: CameraAngle) => void
}

export default function ImageStylePicker({
  imageStyle, aspectRatio, cameraAngle,
  onImageStyleChange, onAspectRatioChange, onCameraAngleChange,
}: ImageStylePickerProps) {
  return (
    <div className="space-y-6">
      {/* Image Style */}
      <Section title="🖼️ เลือกสไตล์ภาพ">
        <div className="grid grid-cols-3 gap-2">
          {IMAGE_STYLES.map(s => (
            <PickerCard
              key={s.id}
              icon={s.icon}
              label={s.label}
              desc={s.desc}
              selected={imageStyle === s.id}
              onClick={() => onImageStyleChange(s.id)}
              selectedColor="violet"
            />
          ))}
        </div>
      </Section>

      {/* Aspect Ratio */}
      <Section title="📐 ขนาดภาพ">
        <div className="grid grid-cols-3 gap-2">
          {ASPECT_RATIOS.map(r => (
            <PickerCard
              key={r.id}
              icon={r.icon}
              label={r.label}
              desc={r.desc}
              selected={aspectRatio === r.id}
              onClick={() => onAspectRatioChange(r.id)}
              selectedColor="pink"
            />
          ))}
        </div>
      </Section>

      {/* Camera Angle */}
      <Section title="📷 มุมกล้อง">
        <div className="grid grid-cols-3 gap-2">
          {CAMERA_ANGLES.map(a => (
            <PickerCard
              key={a.id}
              label={a.label}
              desc={a.desc}
              selected={cameraAngle === a.id}
              onClick={() => onCameraAngleChange(a.id)}
              selectedColor="teal"
            />
          ))}
        </div>
      </Section>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>
      {children}
    </div>
  )
}

function PickerCard({
  icon, label, desc, selected, onClick, selectedColor = 'violet',
}: {
  icon?: string; label: string; desc: string; selected: boolean; onClick: () => void; selectedColor?: string
}) {
  const selectedStyles: Record<string, string> = {
    violet: 'border-violet-500 bg-violet-50 text-violet-700',
    pink: 'border-pink-500 bg-pink-50 text-pink-700',
    teal: 'border-teal-500 bg-teal-50 text-teal-700',
  }

  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex flex-col items-center gap-1 p-3 rounded-xl border-2 text-center transition-all',
        selected
          ? selectedStyles[selectedColor]
          : 'border-gray-100 bg-white hover:border-gray-300 text-gray-600',
      )}
    >
      {icon && <span className="text-xl">{icon}</span>}
      <span className="text-xs font-semibold leading-tight">{label}</span>
      <span className="text-xs text-gray-400 leading-tight">{desc}</span>
    </button>
  )
}
