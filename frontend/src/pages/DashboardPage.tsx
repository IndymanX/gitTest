import { useState } from 'react'
import type { NewsItem, ContentAngle } from '../types'
import FeedHeartbeat from '../components/FeedHeartbeat/FeedHeartbeat'
import EditorBrief from '../components/EditorBrief/EditorBrief'
import AIDrafting from '../components/AIDrafting/AIDrafting'
import AngleGenerator from '../components/AngleGenerator/AngleGenerator'

type ActiveTab = 'feed' | 'brief' | 'draft' | 'angles'

export default function DashboardPage() {
  const [selectedItem, setSelectedItem] = useState<NewsItem | null>(null)
  const [selectedAngle, setSelectedAngle] = useState<ContentAngle | null>(null)
  const [rightTab, setRightTab] = useState<'draft' | 'angles'>('draft')

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left: Feed Heartbeat */}
      <div className="w-80 border-r flex flex-col shrink-0 overflow-hidden">
        <FeedHeartbeat onSelectItem={setSelectedItem} />
      </div>

      {/* Center: Editor Brief */}
      <div className="w-72 border-r flex flex-col shrink-0 overflow-hidden">
        <EditorBrief onSelectStory={(title) => {
          setSelectedItem({ title, editorial_weight: 0, public_impact_score: 0, source_reliability_score: 0, urgency_score: 0, exclusivity_score: 0, is_breaking: false, is_exclusive: false, needs_immediate_action: false, can_wait: false })
        }} />
      </div>

      {/* Right: Draft + Angles */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Tab switcher */}
        <div className="bg-white border-b flex">
          {([['draft', '✍️ AI Drafting'], ['angles', '🎯 Angle Generator']] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setRightTab(key)}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${
                rightTab === key
                  ? 'text-violet-700 border-b-2 border-violet-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-hidden">
          {rightTab === 'draft' ? (
            <AIDrafting selectedItem={selectedItem} />
          ) : (
            <AngleGenerator
              selectedItem={selectedItem}
              onSelectAngle={(angle) => {
                setSelectedAngle(angle)
                setRightTab('draft')
              }}
            />
          )}
        </div>
      </div>
    </div>
  )
}
