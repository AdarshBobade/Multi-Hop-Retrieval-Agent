export type TrailStep = Record<string, unknown>

export type Citation = {
  id: string
  source_type: string
  source: string
  title: string | null
  url: string | null
  page: number | null
  doc_id: string | null
  chunk_id: string | null
  published_date: string | null
  content: string | null
}

export type GroundednessCheck = {
  score: number
  verdict: string
  unsupported_claims: string[]
  reasoning: string
}

export type AskResponse = {
  answer: string
  trail: TrailStep[]
  confidence: number
  citations: Citation[]
  groundedness: GroundednessCheck
  retrieval_calls: number
  web_search_calls: number
  llm_calls: number
}

export type UploadResponse = {
  message: string
  doc_id: string
  filename: string
  chunks: number
  pages: number
  path: string
}

export type AskError = {
  detail: string
}
