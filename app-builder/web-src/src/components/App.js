import React, { useState } from 'react'

const SEARCH_URL = '/api/v1/web/app-builder/search'

const TYPE_COLORS = {
  db_schema: '#0070f3',
  et_schema: '#7928ca',
  mview:     '#ff6b00',
  indexer:   '#cc0000',
  query:     '#0a7c4e',
  command:   '#444',
}

const EXAMPLES = [
  'cde_products_feed table columns',
  'saas resync command product sync',
  'live search indexer class',
  'catalog_data_exporter_products dependencies',
  'B2B company credit table schema',
]

export default function App () {
  const [query, setQuery]     = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)
  const [expanded, setExpanded] = useState({})

  async function doSearch (q) {
    const trimmed = (q !== undefined ? q : query).trim()
    if (!trimmed) return
    setQuery(trimmed)
    setLoading(true)
    setError(null)
    setResults(null)
    setExpanded({})
    try {
      const res = await fetch(`${SEARCH_URL}?query=${encodeURIComponent(trimmed)}&top_k=7`)
      const data = await res.json()
      setResults(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function toggle (i) {
    setExpanded(prev => ({ ...prev, [i]: !prev[i] }))
  }

  return (
    <div style={{ fontFamily: 'Inter,system-ui,sans-serif', maxWidth: 860, margin: '0 auto', padding: '36px 24px', color: '#1a1a1a' }}>

      {/* Header */}
      <h1 style={{ fontSize: 26, fontWeight: 700, margin: '0 0 4px' }}>Commerce Brain</h1>
      <p style={{ color: '#666', marginTop: 4, marginBottom: 28, fontSize: 14 }}>
        Search 519 Adobe Commerce source files — schemas, indexers, feeds, CLI commands, query models
      </p>

      {/* Search bar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && doSearch()}
          placeholder="e.g. cde_products_feed columns"
          style={{
            flex: 1, padding: '11px 14px', fontSize: 15,
            border: '1.5px solid #ccc', borderRadius: 8, outline: 'none',
          }}
          autoFocus
        />
        <button
          onClick={() => doSearch()}
          disabled={loading}
          style={{
            padding: '11px 24px', background: '#e1251b', color: '#fff',
            border: 'none', borderRadius: 8, fontSize: 15, cursor: 'pointer', fontWeight: 600,
          }}
        >
          {loading ? '...' : 'Search'}
        </button>
      </div>

      {/* Example chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 32 }}>
        {EXAMPLES.map(ex => (
          <button key={ex} onClick={() => doSearch(ex)} style={{
            padding: '4px 12px', fontSize: 12, background: '#f5f5f5',
            border: '1px solid #ddd', borderRadius: 20, cursor: 'pointer', color: '#444',
          }}>
            {ex}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {/* Results */}
      {results && (
        <div>
          <p style={{ fontSize: 13, color: '#777', marginBottom: 16 }}>
            {results.count} results for <strong>&ldquo;{results.query}&rdquo;</strong>
          </p>
          {results.results.map((r, i) => (
            <div key={i} style={{ border: '1px solid #e5e5e5', borderRadius: 10, marginBottom: 10, overflow: 'hidden' }}>
              <div onClick={() => toggle(i)} style={{
                padding: '12px 16px', cursor: 'pointer',
                background: expanded[i] ? '#fafafa' : '#fff',
                display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
              }}>
                <span style={{
                  fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 4,
                  background: TYPE_COLORS[r.file_type] || '#888', color: '#fff',
                  textTransform: 'uppercase', letterSpacing: 0.4, whiteSpace: 'nowrap',
                }}>
                  {r.file_type}
                </span>
                <span style={{ fontWeight: 600, fontSize: 13, color: '#333' }}>{r.repo}</span>
                <span style={{ fontSize: 12, color: '#888', flex: 1 }}>
                  {r.path.split('/').slice(1).join('/')}
                </span>
                <span style={{ fontSize: 12, color: '#bbb', whiteSpace: 'nowrap' }}>score {r.score}</span>
                <span style={{ fontSize: 13, color: '#bbb' }}>{expanded[i] ? '▲' : '▼'}</span>
              </div>
              {expanded[i] && (
                <pre style={{
                  margin: 0, padding: '14px 16px', background: '#1e1e1e', color: '#d4d4d4',
                  fontSize: 12, overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                  borderTop: '1px solid #333', maxHeight: 500,
                }}>
                  {r.content}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!results && !loading && !error && (
        <div style={{ textAlign: 'center', padding: '56px 0', color: '#bbb' }}>
          <div style={{ fontSize: 48 }}>🔍</div>
          <p style={{ marginTop: 12, fontSize: 14 }}>Search source of truth — no API key, no hallucination</p>
        </div>
      )}
    </div>
  )
}
