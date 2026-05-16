import axios from 'axios'
import type {
  NewsItem, FeedStats, EditorBrief,
  DraftContent, CopyrightAnalysis, FactCheckResult,
  ContentAngle, ContentFormat, Platform,
  BrainProfile, BrainMaturityReport,
  DraftHistoryItem, ManagedUser,
} from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// Inject auth token + optional API key on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  const apiKey = import.meta.env.VITE_API_KEY
  if (apiKey) config.headers['X-API-Key'] = apiKey
  return config
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

  getHistory: async (limit = 50): Promise<{ items: DraftHistoryItem[]; total: number }> => {
    const { data } = await api.get('/draft/history', { params: { limit } })
    return data
  },

  translate: async (text: string, targetLanguage: 'en' | 'th'): Promise<{ translated: string; target_language: string }> => {
    const { data } = await api.post('/draft/translate', { text, target_language: targetLanguage })
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

  bulkLearn: async (params: {
    profile_id: string
    samples: string[]
    feedback?: 'accepted' | 'rejected' | 'edited'
  }) => {
    const { data } = await api.post('/brain/bulk-learn', params)
    return data
  },
}

// ── Content Studio ─────────────────────────────────────────────────────────

export const studioApi = {
  generateImageSpec: async (params: {
    title: string
    summary: string
    preferred_style?: string
    preferred_ratio?: string
    preferred_angle?: string
  }) => {
    const { data } = await api.post('/studio/image-spec', params)
    return data
  },

  generateTTSScript: async (params: {
    article_title: string
    article_body: string
    reading_tone?: string
    voice_profile?: string
    speed?: number
  }) => {
    const { data } = await api.post('/studio/tts/script', params)
    return data
  },

  synthesizeAudio: async (params: {
    tts_script: string
    voice_profile?: string
    speed?: number
  }) => {
    const { data } = await api.post('/studio/tts/generate', params)
    return data
  },

  listVoices: async () => {
    const { data } = await api.get('/studio/voices')
    return data
  },
}

// ── Settings ────────────────────────────────────────────────────────────────

export const settingsApi = {
  listFeeds: async () => {
    const { data } = await api.get('/settings/feeds')
    return data
  },

  addFeed: async (params: { name: string; url: string; reliability_score?: number }) => {
    const { data } = await api.post('/settings/feeds', params)
    return data
  },

  removeFeed: async (feedId: string) => {
    const { data } = await api.delete(`/settings/feeds/${feedId}`)
    return data
  },

  loadThaiDefaults: async () => {
    const { data } = await api.post('/settings/feeds/load-thai-defaults')
    return data
  },

  getStyleConstitution: async () => {
    const { data } = await api.get('/settings/style-constitution')
    return data
  },

  saveStyleConstitution: async (params: {
    formality_level?: number
    preferred_structure?: string
    forbidden_words?: string[]
    brand_voice_markers?: string[]
    avg_sentence_length?: number
    requires_source_attribution?: boolean
    min_sources_required?: number
  }) => {
    const { data } = await api.post('/settings/style-constitution', params)
    return data
  },

  getTokenUsage: async () => {
    const { data } = await api.get('/settings/token-usage')
    return data
  },
}

// ── Social Publisher ────────────────────────────────────────────────────────

export const publisherApi = {
  getStatus: async (): Promise<{ line: boolean; facebook: boolean; twitter: boolean }> => {
    const { data } = await api.get('/publish/status')
    return data
  },

  send: async (params: {
    title: string
    body: string
    platforms: string[]
    link?: string
    image_url?: string
    platform_overrides?: Record<string, string>
  }) => {
    const { data } = await api.post('/publish/send', params)
    return data
  },
}

// ── Fact-check polling ──────────────────────────────────────────────────────

// ── Editorial Workflow ──────────────────────────────────────────────────────

export const workflowApi = {
  submit: async (params: {
    draft_id: string; title: string; body: string
    platform?: string; format?: string; word_count?: number
    news_title?: string; note?: string
  }) => {
    const { data } = await api.post('/workflow/submit', params)
    return data
  },

  getQueue: async () => {
    const { data } = await api.get('/workflow/queue')
    return data
  },

  getMine: async () => {
    const { data } = await api.get('/workflow/mine')
    return data
  },

  getStatuses: async (): Promise<Record<string, { status: string; review_comment: string; reviewed_by: string | null }>> => {
    const { data } = await api.get('/workflow/statuses')
    return data
  },

  review: async (draftId: string, action: 'approve' | 'reject', comment = '') => {
    const { data } = await api.patch(`/workflow/${draftId}`, { action, comment })
    return data
  },
}

// ── Search ──────────────────────────────────────────────────────────────────

export const searchApi = {
  search: async (q: string, type = 'all', limit = 20) => {
    const { data } = await api.get('/search', { params: { q, type, limit } })
    return data
  },
}

// ── Analytics ───────────────────────────────────────────────────────────────

export const analyticsApi = {
  getSummary: async () => {
    const { data } = await api.get('/analytics/summary')
    return data
  },
}

// ── Content Scheduler ───────────────────────────────────────────────────────

export const schedulerApi = {
  create: async (params: {
    title: string
    body: string
    platforms: string[]
    scheduled_at: string
    link?: string
  }) => {
    const { data } = await api.post('/schedule', params)
    return data
  },

  list: async (): Promise<{ posts: unknown[]; total: number }> => {
    const { data } = await api.get('/schedule')
    return data
  },

  cancel: async (postId: string) => {
    const { data } = await api.delete(`/schedule/${postId}`)
    return data
  },
}

// ── Fact-check polling ──────────────────────────────────────────────────────

export const factCheckApi = {
  getStatus: async (taskId: string) => {
    const { data } = await api.get(`/draft/factcheck/status/${taskId}`)
    return data
  },
}

// ── Authentication ──────────────────────────────────────────────────────────

export interface AuthUser {
  email: string
  full_name: string
  role: string
  is_active: boolean
  organization_id: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export const authApi = {
  register: async (params: { email: string; password: string; full_name: string; role?: string }): Promise<AuthResponse> => {
    const { data } = await api.post<AuthResponse>('/auth/register', params)
    return data
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const form = new URLSearchParams()
    form.set('username', email)
    form.set('password', password)
    const { data } = await api.post<AuthResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  me: async (): Promise<AuthUser> => {
    const { data } = await api.get<AuthUser>('/auth/me')
    return data
  },

  check: async (): Promise<{ has_users: boolean; user_count: number }> => {
    const { data } = await api.get('/auth/check')
    return data
  },

  listUsers: async (): Promise<{ users: ManagedUser[]; total: number }> => {
    const { data } = await api.get('/auth/users')
    return data
  },

  updateUser: async (email: string, updates: { role?: string; is_active?: boolean; full_name?: string }): Promise<ManagedUser> => {
    const { data } = await api.patch(`/auth/users/${encodeURIComponent(email)}`, updates)
    return data
  },

  deleteUser: async (email: string): Promise<void> => {
    await api.delete(`/auth/users/${encodeURIComponent(email)}`)
  },
}

export default api
