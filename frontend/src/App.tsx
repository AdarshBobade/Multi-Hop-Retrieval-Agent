import {
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
  type FormEvent,
} from 'react'
import ReactMarkdown from 'react-markdown'
import { askQuestion, uploadPdf } from './api'
import type { AskResponse, UploadResponse } from './types'
import './App.css'

const EXAMPLES = [
  'How did the invention of the printing press influence the Scientific Revolution?',
  'What connects the fall of Constantinople to the Age of Exploration?',
  'How do coral reefs affect coastal economies during climate change?',
]

const MAX_UPLOAD_BYTES = 25 * 1024 * 1024

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [result, setResult] = useState<AskResponse | null>(null)
  const [uploads, setUploads] = useState<UploadResponse[]>([])
  const resultsRef = useRef<HTMLElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = query.trim()
    if (!trimmed || loading || uploading) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await askQuestion(trimmed)
      setResult(data)
      requestAnimationFrame(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  async function processFile(file: File) {
    if (uploading || loading) return

    const name = file.name.toLowerCase()
    if (!name.endsWith('.pdf')) {
      setUploadError('Only PDF files are supported.')
      return
    }

    if (file.size > MAX_UPLOAD_BYTES) {
      setUploadError('File exceeds the 25 MB limit.')
      return
    }

    if (file.size === 0) {
      setUploadError('Uploaded file is empty.')
      return
    }

    setUploading(true)
    setUploadError(null)

    try {
      const data = await uploadPdf(file)
      setUploads((prev) => [data, ...prev])
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) void processFile(file)
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault()
    setDragOver(false)
    const file = event.dataTransfer.files?.[0]
    if (file) void processFile(file)
  }

  const busy = loading || uploading

  return (
    <div className="page">
      <div className="atmosphere" aria-hidden="true">
        <div className="orb orb-a" />
        <div className="orb orb-b" />
        <div className="grid-wash" />
      </div>

      <header className="hero">
        <p className="brand">MultiHop</p>
        <h1>Ask questions that need more than one leap.</h1>
        <p className="lede">
          Decompose complex queries, retrieve and verify evidence across hops,
          then synthesize cited answers from real sources.
        </p>

        <section className="upload-panel" aria-labelledby="upload-heading">
          <div className="upload-copy">
            <h2 id="upload-heading">Source PDFs</h2>
            <p>Drop a PDF to ingest it into the retrieval index before you ask.</p>
          </div>

          <label
            className={`dropzone${dragOver ? ' is-dragover' : ''}${uploading ? ' is-busy' : ''}`}
            onDragEnter={(event) => {
              event.preventDefault()
              setDragOver(true)
            }}
            onDragOver={(event) => {
              event.preventDefault()
              setDragOver(true)
            }}
            onDragLeave={(event) => {
              event.preventDefault()
              setDragOver(false)
            }}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              disabled={busy}
            />
            <span className="dropzone-title">
              {uploading ? (
                <>
                  <span className="spinner spinner-dark" aria-hidden="true" />
                  Ingesting PDF…
                </>
              ) : (
                'Drop a PDF here, or browse'
              )}
            </span>
            <span className="dropzone-hint">PDF only · up to 25 MB</span>
          </label>

          {uploadError && (
            <div className="banner error upload-banner" role="alert">
              {uploadError}
            </div>
          )}

          {uploads.length > 0 && (
            <ul className="upload-list">
              {uploads.map((item) => (
                <li key={item.doc_id}>
                  <div>
                    <p className="upload-name">{item.filename}</p>
                    <p className="upload-meta">
                      {item.pages} pages · {item.chunks} chunks · ingested
                    </p>
                  </div>
                  <span className="upload-badge">Ready</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <form className="ask-form" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="query">
            Research question
          </label>
          <textarea
            id="query"
            name="query"
            rows={3}
            maxLength={300}
            placeholder="What multi-hop research question should we chase?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={busy}
          />
          <div className="ask-actions">
            <span className="char-count">{query.length}/300</span>
            <button type="submit" disabled={busy || !query.trim()}>
              {loading ? (
                <>
                  <span className="spinner" aria-hidden="true" />
                  Researching…
                </>
              ) : (
                'Start research'
              )}
            </button>
          </div>
        </form>

        <div className="examples">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              className="example"
              disabled={busy}
              onClick={() => setQuery(example)}
            >
              {example}
            </button>
          ))}
        </div>
      </header>

      {error && (
        <div className="banner error" role="alert">
          {error}
        </div>
      )}

      {result && (
        <section className="results" ref={resultsRef} aria-live="polite">
          <div className="result-head">
            <h2>Synthesized answer</h2>
            <p className="confidence">
              Confidence{' '}
              <strong>{Math.round(result.confidence * 100)}%</strong>
            </p>
          </div>

          <article className="answer prose">
            <ReactMarkdown>{result.answer}</ReactMarkdown>
          </article>

          {result.trail.length > 0 && (
            <section className="trail">
              <h3>Research trail</h3>
              <ol>
                {result.trail.map((step, index) => (
                  <li key={index}>
                    <span className="hop-index">Hop {index + 1}</span>
                    <pre>{JSON.stringify(step, null, 2)}</pre>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {result.citations.length > 0 && (
            <section className="sources">
              <h3>Sources</h3>
              <ul>
                {result.citations.map((citation) => (
                  <li key={citation.id}>
                    <p>
                      <strong>[{citation.id}]</strong>{' '}
                      {citation.source_type === 'web' ? (
                        <a href={citation.url ?? undefined} target="_blank" rel="noopener noreferrer">
                          {citation.title ?? citation.source}
                        </a>
                      ) : (
                        <>
                          {citation.source}
                          {citation.page !== null && ` (page ${citation.page})`}
                        </>
                      )}
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="groundedness">
            <h3>Groundedness check</h3>
            <p>
              <strong>{result.groundedness.verdict.replace('_', ' ')}</strong>{' '}
              ({Math.round(result.groundedness.score * 100)}%)
            </p>
            {result.groundedness.unsupported_claims.length > 0 && (
              <ul>
                {result.groundedness.unsupported_claims.map((claim, i) => (
                  <li key={i}>⚠ {claim}</li>
                ))}
              </ul>
            )}
          </section>
        </section>
      )}

      <footer className="footer">
        <p>Multi-Hop Retrieval Agent</p>
      </footer>
    </div>
  )
}

export default App
