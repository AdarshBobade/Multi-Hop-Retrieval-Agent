export type TrailStep = Record<string, unknown>

export type AskResponse = {
  answer: string
  trail: TrailStep[]
  confidence: number
  sources: string[]
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
