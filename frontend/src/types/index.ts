// Core domain types for AInewsroom

export type NewsCategory =
  | 'breaking' | 'politics' | 'economy' | 'technology'
  | 'society' | 'environment' | 'entertainment' | 'sports'
  | 'international' | 'local'

export type NewsStatus =
  | 'incoming' | 'prioritized' | 'briefed' | 'drafting'
  | 'reviewing' | 'published' | 'archived'

export interface NewsItem {
  id?: string
  title: string
  summary?: string
  content?: string
  url?: string
  source_name?: string
  author?: string
  published_at?: string
  category?: NewsCategory
  status?: NewsStatus
  language?: string
  // Editorial weight
  editorial_weight: number
  public_impact_score: number
  source_reliability_score: number
  urgency_score: number
  exclusivity_score: number
  // Flags
  is_breaking: boolean
  is_exclusive: boolean
  needs_immediate_action: boolean
  can_wait: boolean
  // Source chain
  source_chain?: SourceChainEntry[]
  tags?: string[]
}

export interface SourceChainEntry {
  source_name: string
  source_url: string
  fetched_at: string
  transform_level: number
  transform_level_label?: string
  is_licensed?: boolean
  license_type?: string
}

export interface FeedStats {
  total: number
  breaking: number
  urgent: number
  can_wait: number
  exclusive: number
  last_hour: number
  avg_editorial_weight: number
  updated_at: string
}

export interface EditorBrief {
  top_stories: TopStory[]
  can_wait_stories: TopStory[]
  trend_summary: string
  editor_recommendations: string[]
  exclusive_opportunities: string[]
  total_items: number
  processed_at: string
}

export interface TopStory {
  index: number
  title: string
  reason?: string
  editorial_weight?: number
}

// Content types
export type ContentFormat = 'article' | 'social_post' | 'video_script' | 'podcast_script' | 'infographic_text' | 'newsletter'
export type Platform = 'website' | 'facebook' | 'twitter' | 'instagram' | 'tiktok' | 'youtube' | 'line' | 'podcast'
export type ImageStyle = 'photorealistic' | 'cinematic' | 'illustration' | 'minimalist' | 'abstract' | 'news_style'
export type AspectRatio = '16:9' | '1:1' | '9:16' | '4:5' | '3:2' | '4:3'
export type CameraAngle = 'eye_level' | 'aerial' | 'low_angle' | 'high_angle' | 'close_up' | 'wide_angle' | 'over_shoulder' | 'dutch_angle' | 'isometric'
export type VoiceProfile = 'liam' | 'rachel' | 'adam' | 'bella' | 'antoni' | 'josh'
export type ReadingTone = 'news' | 'storytelling' | 'casual' | 'educational' | 'drama' | 'podcast'

export interface DraftContent {
  title: string
  lead: string
  body: string
  seo_title?: string
  seo_description?: string
  aio_keywords?: string[]
  tags?: string[]
  source_attribution?: string
  fact_claims?: string[]
  platform?: Platform
  format?: ContentFormat
  angle_used?: string
  word_count?: number
  reading_time_minutes?: number
}

// Copyright analysis
export interface CopyrightAnalysis {
  overall_risk_score: number
  risk_level: 'low' | 'medium' | 'high'
  content_similarity_score: number
  style_similarity_score: number
  structure_similarity_score: number
  flagged_segments: FlaggedSegment[]
  source_chain: SourceChainEntry[]
  recommendations: string[]
  thai_copyright_act_compliant: boolean
  fair_use_applicable: boolean
  fair_use_reason?: string
  risk_breakdown: {
    เนื้อหา: number
    สำนวน: number
    โครงสร้าง: number
  }
}

export interface FlaggedSegment {
  text: string
  similarity_score: number
  risk_type: 'content' | 'style' | 'structure'
  matched_source: string
}

// Fact check
export interface FactCheckResult {
  has_claims: boolean
  claims: Claim[]
  high_priority_claims: Claim[]
  total_claims: number
  overall_risk: 'low' | 'medium' | 'high'
  fact_check_score: number
  recommendations: string[]
  checklist: ChecklistItem[]
}

export interface Claim {
  text: string
  category: string
  category_th: string
  verification_priority: number
}

export interface ChecklistItem {
  task: string
  priority: number
  status: 'pending' | 'verified' | 'failed'
}

// Content angle
export interface ContentAngle {
  angle_type: string
  angle_name_th: string
  proposed_title: string
  hook: string
  key_questions: string[]
  target_audience: string
  best_platform: Platform
  estimated_effort: 'low' | 'medium' | 'high'
  research_needed: string[]
  platform_best_fit?: Platform[]
}

// Brain maturity
export interface BrainProfile {
  id: string
  name: string
  maturity_score: number
  total_samples_learned: number
  accepted_count: number
  rejected_count: number
  edited_count: number
}

export interface BrainMaturityReport {
  maturity_score: number
  level: string
  description: string
  samples_learned: number
  acceptance_rate: number
  top_vocabulary: string[]
  next_milestone: {
    target_score: number
    milestone_name: string
    action_needed: string
  }
}

// Draft history
export interface DraftHistoryItem {
  id: string
  title: string
  body_preview: string
  platform: Platform
  format: ContentFormat
  word_count: number
  generated_at: string
  news_title: string
  full_draft: DraftContent
}

// User management
export interface ManagedUser {
  email: string
  full_name: string
  role: string
  is_active: boolean
  organization_id: string
}

// Content Studio
export interface ContentStudioSettings {
  image_style: ImageStyle
  image_aspect_ratio: AspectRatio
  camera_angle: CameraAngle
  voice_profile: VoiceProfile
  reading_tone: ReadingTone
  speed: number
}
