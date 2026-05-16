import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { studioApi } from '../services/api'
import type { ContentStudioSettings } from '../types'
import ImageStylePicker from '../components/ContentStudio/ImageStylePicker'
import VoicePicker from '../components/ContentStudio/VoicePicker'
import TTSPlayer from '../components/ContentStudio/TTSPlayer'
import { Mic, Image, Zap, Copy } from 'lucide-react'
import { toast } from 'sonner'
import { clsx } from 'clsx'

const DEFAULT_SETTINGS: ContentStudioSettings = {
  image_style: 'news_style',
  image_aspect_ratio: '16:9',
  camera_angle: 'eye_level',
  voice_profile: 'liam',
  reading_tone: 'news',
  speed: 1.0,
}

export default function ContentStudioPage() {
  const [settings, setSettings] = useState<ContentStudioSettings>(DEFAULT_SETTINGS)
  const [articleTitle, setArticleTitle] = useState('')
  const [articleBody, setArticleBody] = useState('')
  const [activeTab, setActiveTab] = useState<'image' | 'voice'>('voice')

  // TTS script generation
  const ttsScriptMutation = useMutation({
    mutationFn: () => studioApi.generateTTSScript({
      article_title: articleTitle,
      article_body: articleBody,
      reading_tone: settings.reading_tone,
      voice_profile: settings.voice_profile,
      speed: settings.speed,
    }),
    onSuccess: () => toast.success('สร้างสคริปต์ TTS สำเร็จ'),
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  // TTS audio synthesis
  const ttsSynthMutation = useMutation({
    mutationFn: () => {
      const script = ttsScriptMutation.data?.tts_script || ''
      if (!script) throw new Error('กรุณาสร้างสคริปต์ก่อน')
      return studioApi.synthesizeAudio({
        tts_script: script,
        voice_profile: settings.voice_profile,
        speed: settings.speed,
      })
    },
    onSuccess: (data) => {
      if (data.success) toast.success('สร้างเสียงสำเร็จ')
      else toast.error(data.error || 'เกิดข้อผิดพลาด')
    },
  })

  // Image spec generation
  const imageSpecMutation = useMutation({
    mutationFn: () => studioApi.generateImageSpec({
      title: articleTitle,
      summary: articleBody.slice(0, 200),
      preferred_style: settings.image_style,
      preferred_ratio: settings.image_aspect_ratio,
      preferred_angle: settings.camera_angle,
    }),
    onSuccess: () => toast.success('สร้าง Image Spec สำเร็จ'),
    onError: () => toast.error('เกิดข้อผิดพลาด'),
  })

  const update = <K extends keyof ContentStudioSettings>(key: K, value: ContentStudioSettings[K]) =>
    setSettings(prev => ({ ...prev, [key]: value }))

  const imageSpec = imageSpecMutation.data

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <span className="text-3xl">🎨</span> Content Studio
          </h1>
          <p className="text-gray-500 mt-1">สร้างภาพประกอบ + เสียงอ่านข่าวในขั้นตอนเดียว</p>
        </div>

        {/* Article input */}
        <div className="bg-white border rounded-xl p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-600">บทความที่ต้องการผลิต</h2>
          <input
            value={articleTitle}
            onChange={e => setArticleTitle(e.target.value)}
            placeholder="หัวข้อข่าว..."
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500 font-medium"
          />
          <textarea
            value={articleBody}
            onChange={e => setArticleBody(e.target.value)}
            placeholder="เนื้อหาบทความ (วางจาก AI Drafting หรือพิมพ์เอง)..."
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500 min-h-[120px] resize-y"
          />
        </div>

        {/* Tab switcher */}
        <div className="flex bg-gray-100 rounded-xl p-1">
          <TabBtn active={activeTab === 'voice'} onClick={() => setActiveTab('voice')} icon={<Mic size={14} />} label="🎤 เสียง (Voiceover)" />
          <TabBtn active={activeTab === 'image'} onClick={() => setActiveTab('image')} icon={<Image size={14} />} label="🖼️ ภาพประกอบ (Image Spec)" />
        </div>

        {/* Voice tab */}
        {activeTab === 'voice' && (
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-white border rounded-xl p-5">
              <VoicePicker
                voiceProfile={settings.voice_profile}
                readingTone={settings.reading_tone}
                speed={settings.speed}
                onVoiceChange={v => update('voice_profile', v)}
                onToneChange={v => update('reading_tone', v)}
                onSpeedChange={v => update('speed', v)}
              />

              {/* TTS provider info */}
              <div className="mt-4 flex items-center gap-2 text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2">
                <span className="text-base">🎙️</span>
                <div>
                  <div className="font-medium">ElevenLabs TTS</div>
                  <div className="text-gray-400">Multilingual v2 · ภาษาไทย · {settings.voice_profile}</div>
                </div>
                <span className="ml-auto text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                  {settings.speed}x
                </span>
              </div>

              {/* Generate buttons */}
              <div className="mt-4 space-y-2">
                <button
                  onClick={() => ttsScriptMutation.mutate()}
                  disabled={ttsScriptMutation.isPending || !articleBody.trim()}
                  className="w-full flex items-center justify-center gap-2 bg-emerald-600 text-white py-2.5 rounded-lg hover:bg-emerald-700 disabled:opacity-50 font-medium text-sm"
                >
                  <Zap size={14} />
                  {ttsScriptMutation.isPending ? 'กำลังสร้างสคริปต์...' : '🎤 สร้าง Voiceover'}
                </button>

                {ttsScriptMutation.data && (
                  <button
                    onClick={() => ttsSynthMutation.mutate()}
                    disabled={ttsSynthMutation.isPending}
                    className="w-full flex items-center justify-center gap-2 bg-violet-600 text-white py-2.5 rounded-lg hover:bg-violet-700 disabled:opacity-50 font-medium text-sm"
                  >
                    {ttsSynthMutation.isPending ? 'กำลังสังเคราะห์เสียง...' : '🔊 สังเคราะห์เสียง (ElevenLabs)'}
                  </button>
                )}
              </div>
            </div>

            {/* TTS Player + Script */}
            <div className="space-y-4">
              <TTSPlayer
                audioBase64={ttsSynthMutation.data?.audio_base64}
                ttsScript={ttsScriptMutation.data?.tts_script}
                estimatedDuration={ttsScriptMutation.data?.estimated_duration_seconds}
                voiceProfile={settings.voice_profile}
                isLoading={ttsScriptMutation.isPending || ttsSynthMutation.isPending}
              />

              {ttsScriptMutation.data?.tts_script && (
                <div className="bg-white border rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-gray-500">สคริปต์ฉบับเต็ม</span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(ttsScriptMutation.data.tts_script)
                        toast.success('คัดลอกสคริปต์แล้ว')
                      }}
                      className="text-xs text-gray-400 hover:text-violet-600 flex items-center gap-1"
                    >
                      <Copy size={12} /> คัดลอก
                    </button>
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {ttsScriptMutation.data.tts_script}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Image tab */}
        {activeTab === 'image' && (
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-white border rounded-xl p-5">
              <ImageStylePicker
                imageStyle={settings.image_style}
                aspectRatio={settings.image_aspect_ratio}
                cameraAngle={settings.camera_angle}
                onImageStyleChange={v => update('image_style', v)}
                onAspectRatioChange={v => update('image_aspect_ratio', v)}
                onCameraAngleChange={v => update('camera_angle', v)}
              />
              <button
                onClick={() => imageSpecMutation.mutate()}
                disabled={imageSpecMutation.isPending || !articleTitle.trim()}
                className="mt-4 w-full flex items-center justify-center gap-2 bg-violet-600 text-white py-2.5 rounded-lg hover:bg-violet-700 disabled:opacity-50 font-medium text-sm"
              >
                <Zap size={14} />
                {imageSpecMutation.isPending ? 'กำลังสร้าง...' : '🖼️ สร้าง Image Spec'}
              </button>
            </div>

            {/* Image spec result */}
            <div className="space-y-4">
              {imageSpecMutation.isPending && (
                <div className="bg-white border rounded-xl p-6 animate-pulse space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-2/3" />
                  <div className="h-20 bg-gray-100 rounded" />
                </div>
              )}

              {imageSpec && (
                <>
                  {/* Color palette */}
                  {imageSpec.color_palette && (
                    <div className="bg-white border rounded-xl p-4">
                      <div className="text-xs font-semibold text-gray-500 mb-2">Color Palette</div>
                      <div className="flex gap-2">
                        {imageSpec.color_palette.map((color: string, i: number) => (
                          <div key={i} className="flex flex-col items-center gap-1">
                            <div
                              className="w-10 h-10 rounded-lg border shadow-sm"
                              style={{ backgroundColor: color }}
                            />
                            <span className="text-xs text-gray-400">{color}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Prompt for image gen tools */}
                  <div className="bg-white border rounded-xl p-4 space-y-3">
                    <div className="text-xs font-semibold text-gray-500">Image Generation Prompt</div>
                    <div className="space-y-2">
                      {(['midjourney', 'dalle', 'stable_diffusion'] as const).map(tool => (
                        imageSpec.generation_tools?.[tool] && (
                          <div key={tool} className="bg-gray-50 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-medium text-gray-600 capitalize">{tool.replace('_', ' ')}</span>
                              <button
                                onClick={() => {
                                  navigator.clipboard.writeText(imageSpec.generation_tools[tool])
                                  toast.success(`คัดลอก ${tool} prompt แล้ว`)
                                }}
                                className="text-xs text-gray-400 hover:text-violet-600"
                              >
                                <Copy size={11} />
                              </button>
                            </div>
                            <p className="text-xs text-gray-600 leading-relaxed font-mono">
                              {imageSpec.generation_tools[tool]}
                            </p>
                          </div>
                        )
                      ))}
                    </div>
                  </div>

                  {/* Thai alt text */}
                  {imageSpec.thai_alt_text && (
                    <div className="bg-white border rounded-xl p-4">
                      <div className="text-xs font-semibold text-gray-500 mb-1">Thai Alt Text (Accessibility)</div>
                      <p className="text-sm text-gray-700">{imageSpec.thai_alt_text}</p>
                    </div>
                  )}
                </>
              )}

              {!imageSpec && !imageSpecMutation.isPending && (
                <div className="flex flex-col items-center justify-center h-48 text-gray-300 gap-2">
                  <Image size={36} />
                  <p className="text-sm">กด "สร้าง Image Spec" เพื่อรับ Prompt สำหรับสร้างภาพ</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function TabBtn({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all',
        active ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700',
      )}
    >
      {icon} {label}
    </button>
  )
}
