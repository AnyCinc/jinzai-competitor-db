const BASE = ''  // 同一オリジン（本番）またはviteプロキシ経由

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ---- Companies ----
export const getCompanies = (q?: string) =>
  api<Company[]>(`/api/companies${q ? `?q=${encodeURIComponent(q)}` : ''}`)

export const createCompany = (data: Partial<Company>) =>
  api<Company>('/api/companies', { method: 'POST', body: JSON.stringify(data) })

export const getCompany = (id: number) =>
  api<Company>(`/api/companies/${id}`)

export const updateCompany = (id: number, data: Partial<Company>) =>
  api<Company>(`/api/companies/${id}`, { method: 'PUT', body: JSON.stringify(data) })

export const deleteCompany = (id: number) =>
  api<{ ok: boolean }>(`/api/companies/${id}`, { method: 'DELETE' })

// ---- Files ----
export const uploadFile = async (companyId: number, file: File): Promise<CompanyFile> => {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`/api/companies/${companyId}/files`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const deleteFile = (id: number) =>
  api<{ ok: boolean }>(`/api/files/${id}`, { method: 'DELETE' })

// ---- Links ----
export const addLink = (companyId: number, data: Partial<CompanyLink>) =>
  api<CompanyLink>(`/api/companies/${companyId}/links`, {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const deleteLink = (id: number) =>
  api<{ ok: boolean }>(`/api/links/${id}`, { method: 'DELETE' })

// ---- Analysis ----
export const searchCompetitors = (query: string, max_results = 10) =>
  api<SearchResponse>('/api/search', {
    method: 'POST',
    body: JSON.stringify({ query, max_results }),
  })

export const analyzeUrl = (url: string, save_company_id?: number) =>
  api<AnalyzeResponse>('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({ url, save_company_id }),
  })

export const analyzeCompany = (id: number) =>
  api<AnalyzeResponse>(`/api/analyze/${id}`, { method: 'POST' })

// ---- Types ----
export interface Company {
  id: number
  name: string
  hp_url?: string
  industry_detail?: string
  description?: string
  strengths?: string   // JSON文字列
  weaknesses?: string  // JSON文字列
  notes?: string
  ai_summary?: string
  status: string
  created_at: string
  updated_at: string
  files: CompanyFile[]
  links: CompanyLink[]
}

export interface CompanyFile {
  id: number
  company_id: number
  filename: string
  original_name: string
  file_type?: string
  size?: number
  description?: string
  created_at: string
}

export interface CompanyLink {
  id: number
  company_id: number
  url: string
  title?: string
  link_type?: string
  description?: string
  created_at: string
}

export interface SearchResultItem {
  title: string
  url: string
  snippet?: string
}

export interface SearchResponse {
  query: string
  results: SearchResultItem[]
}

export interface AnalyzeResponse {
  url: string
  company_name?: string
  summary?: string
  strengths: string[]
  weaknesses: string[]
  raw_text?: string
}

export const parseJsonList = (json?: string): string[] => {
  if (!json) return []
  try {
    return JSON.parse(json)
  } catch {
    return []
  }
}

export const formatSize = (bytes?: number): string => {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}
