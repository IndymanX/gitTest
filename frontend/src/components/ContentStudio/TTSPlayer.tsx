import { useRef, useState } from 'react'
import { Play, Pause, Square, Download, Volume2 } from 'lucide-react'
import { clsx } from 'clsx'

interface Props {
  audioBase64?: string
  ttsScript?: string
  estimatedDuration?: number
  voiceProfile?: string
  isLoading?: boolean
}

export default function TTSPlayer({ audioBase64, ttsScript, estimatedDuration, voiceProfile, isLoading }: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)

  const audioSrc = audioBase64 ? `data:audio/mpeg;base64,${audioBase64}` : null

  const toggle = () => {
    if (!audioRef.current) return
    if (playing) {
      audioRef.current.pause()
      setPlaying(false)
    } else {
      audioRef.current.play()
      setPlaying(true)
    }
  }

  const stop = () => {
    if (!audioRef.current) return
    audioRef.current.pause()
    audioRef.current.currentTime = 0
    setPlaying(false)
    setProgress(0)
  }

  const download = () => {
    if (!audioSrc) return
    const a = document.createElement('a')
    a.href = audioSrc
    a.download = `voiceover-${voiceProfile || 'liam'}.mp3`
    a.click()
  }

  return (
    <div className="bg-white border rounded-xl p-4 space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
        <Volume2 size={16} className="text-violet-600" />
        <span>เสียงอ่านข่าวพร้อมแล้ว</span>
        {estimatedDuration && (
          <span className="ml-auto text-xs text-gray-400">~{estimatedDuration} วินาที</span>
        )}
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-gray-400 animate-pulse">
          <div className="w-4 h-4 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
          กำลังสร้างเสียง...
        </div>
      )}

      {audioSrc && (
        <>
          <audio
            ref={audioRef}
            src={audioSrc}
            onTimeUpdate={(e) => {
              const el = e.currentTarget
              if (el.duration) setProgress((el.currentTime / el.duration) * 100)
            }}
            onEnded={() => { setPlaying(false); setProgress(100) }}
          />
          {/* Progress bar */}
          <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-violet-500 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={toggle}
              className="flex items-center gap-1.5 bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700"
            >
              {playing ? <Pause size={14} /> : <Play size={14} />}
              {playing ? 'หยุด' : 'เล่น'}
            </button>
            <button
              onClick={stop}
              className="p-2 text-gray-400 hover:text-gray-600 border rounded-lg"
            >
              <Square size={14} />
            </button>
            <button
              onClick={download}
              className="ml-auto flex items-center gap-1.5 text-sm text-gray-500 hover:text-violet-600 border rounded-lg px-3 py-2"
            >
              <Download size={14} />
              ดาวน์โหลด MP3
            </button>
          </div>
        </>
      )}

      {/* Script preview */}
      {ttsScript && (
        <div className="mt-2 bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-400 mb-1">สคริปต์ TTS</div>
          <p className="text-xs text-gray-600 leading-relaxed line-clamp-4">{ttsScript}</p>
        </div>
      )}

      {!audioSrc && !isLoading && (
        <div className="text-xs text-gray-400 bg-amber-50 border border-amber-100 rounded-lg p-3">
          💡 กด "สร้าง Voiceover" เพื่อสร้างสคริปต์ TTS
          {' '}(ต้องใส่ ELEVENLABS_API_KEY ใน .env เพื่อสังเคราะห์เสียงจริง)
        </div>
      )}
    </div>
  )
}
