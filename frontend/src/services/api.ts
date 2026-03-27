import axios from 'axios'
import type {
  NewsItem, FeedStats, EditorBrief,
  DraftContent, CopyrightAnalysis, FactCheckResult,
  ContentAngle, ContentFormat, Platform,
  BrainProfile, BrainMaturityReport,
} from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Feed Heartbeat ──────────────────────────────────────────────────────────

export const feedApi = {
  getLive: async (params?: { limit?: number; category?: string; min_weight?: number }) => {
    const { data } = await api.get<{ items: NewsItem[]; total: number }>('/feed/live', { params })
    return data
  },

  getStats: async (): Promise<FeedStats> => {
    const { data } = await api.get<FeedStats>('/feed/stats')
    return data
  },

  fetchUrls: async (urls: string[], source_name = 'Manual') => {
    const { data } = await api.post('/feed/fetch', { urls, source_name })
    return data
  },

  getEditorBrief: async (): Promise<EditorBrief> => {
    const { data } = await api.get<EditorBrief>('/feed/brief')
    return data
  },

  getBreaking: async () => {
    const { data } = await api.get<{ items: NewsItem[]; count: number }>('/feed/items/breaking')
    return data
  },
}

// ── AI Drafting ──────────────────────────────────────────────────────────────

export interface GenerateDraftParams {
  news_item: Partial<NewsItem> & { title: string }
  format?: ContentFormat
  platform?: Platform
  angle?: string
  style_constitution?: Record<string, unknown>
  brain_profile?: Record<string, unknown>
  auto_check_copyright?: boolean
  auto_check_facts?: boolean
}

export interface GenerateDraftResponse {
  draft: DraftContent
  copyright?: CopyrightAnalysis
  fact_check?: FactCheckResult
}

export const draftApi = {
  generate: async (params: GenerateDraftParams): Promise<GenerateDraftResponse> => {
    const { data } = await api.post<GenerateDraftResponse>('/draft/generate', params)
    return data
  },

  generateAngles: async (
    news_item: Partial<NewsItem> & { title: string },
    num_angles = 5,
    angle_types?: string[],
  ) => {
    const { data } = await api.post<{ angles: ContentAngle[]; total: number; content_plan_summary: string }>(
      '/draft/angles',
      { news_item, num_angles, angle_types },
    )
    return data
  },

  checkCopyright: async (params: {
    draft_text: string
    draft_title?: string
    source_texts?: string[]
    source_chain?: unknown[]
  }): Promise<CopyrightAnalysis> => {
    const { data } = await api.post<CopyrightAnalysis>('/draft/copyright/check', params)
    return data
  },

  factCheck: async (params: { draft_text: string; source_urls?: string[] }): Promise<FactCheckResult> => {
    const { data } = await api.post<FactCheckResult>('/draft/factcheck', params)
    return data
  },

  repurpose: async (params: {
    original_article: string
    original_title: string
    target_platforms?: Platform[]
  }) => {
    const { data } = await api.post('/draft/repurpose', params)
    return data
  },

  adaptForPlatform: async (platform: Platform, params: { title: string; body: string }) => {
    const { data } = await api.post(`/draft/adapt/${platform}`, params)
    return data
  },
}

// ── Brain Maturity ─────────────────────────────────────────────────────────

export const brainApi = {
  createProfile: async (params: {
    profile_id: string
    name: string
    organization_id: string
    user_id?: string
  }) => {
    const { data } = await api.post('/brain/profiles', params)
    return data
  },

  getProfile: async (profileId: string): Promise<{ profile: BrainProfile; report: BrainMaturityReport }> => {
    const { data } = await api.get(`/brain/profiles/${profileId}`)
    return data
  },

  learn: async (params: {
    profile_id: string
    sample_text: string
    feedback: 'accepted' | 'rejected' | 'edited'
    edited_version?: string
  }) => {
    const { data } = await api.post('/brain/learn', params)
    return data
  },

  getStylePrompt: async (profileId: string) => {
    const { data } = await api.get(`/brain/profiles/${profileId}/style-prompt`)
    return data
  },

  listProfiles: async () => {
    const { data } = await api.get('/brain/profiles')
    return data
  },
}

export default api
