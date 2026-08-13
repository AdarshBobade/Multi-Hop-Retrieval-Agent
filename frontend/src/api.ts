import type { AskResponse, UploadResponse } from './types'

async function readError(response: Response): Promise<string> {
  if (response.status === 502 || response.status === 503 || response.status === 504) {
    return 'API is unreachable. Start the backend with: .venv/bin/uvicorn app_data.main:app --reload --port 8000'
  }

  let detail = `Request failed (${response.status})`
  try {
    const data = (await response.json()) as { detail?: string }
    if (data.detail) detail = data.detail
  } catch {
    // ignore JSON parse errors
  }
  return detail
}

export async function askQuestion(query: string): Promise<AskResponse> {
  const response = await fetch('/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  const data = await response.json();

  // Backends may return citations instead of a simple `sources` string array.
  // Normalize common shapes so the UI can always rely on `sources: string[]`.
  if (!('sources' in data) && Array.isArray((data as any).citations)) {
    (data as any).sources = (data as any).citations.map((c: any) => c.source ?? c.title ?? c.url ?? c.doc_id ?? JSON.stringify(c));
  }

  return data as AskResponse
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const body = new FormData()
  body.append('file', file)

  const response = await fetch('/upload', {
    method: 'POST',
    body,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  return response.json() as Promise<UploadResponse>
}
