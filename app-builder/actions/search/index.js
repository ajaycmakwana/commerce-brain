/*
 * Commerce Brain — Search Action (App Builder)
 * BM25 search over 519 Adobe Commerce source files.
 *
 * Index is bundled with the action (index.json, ~3.5 MB).
 * Loaded once on cold start and cached in memory.
 */

const TOP_K = 5
const K1 = 1.5
const B = 0.75

// Bundled by webpack at build time — no runtime file I/O needed
const INDEX = require('./index.json')

function tokenize(text) {
  return text.toLowerCase().split(/[^a-zA-Z0-9_]+/).filter(t => t.length > 2)
}

function loadIndex() {
  return INDEX
}

function bm25Scores(queryTokens, store) {
  const { docs, idf, avgdl } = store
  return docs.map(doc => {
    const dl = doc.tokens.length
    let score = 0
    for (const term of queryTokens) {
      const termIdf = idf[term]
      if (!termIdf) continue
      const tf = doc.tokens.filter(t => t === term).length
      score += termIdf * (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * dl / avgdl))
    }
    return score
  })
}

async function main(params) {
  const query = (params.query || '').trim()
  const topK = Math.min(parseInt(params.top_k || TOP_K, 10), 20)
  const fileType = (params.file_type || '').trim()

  const headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }

  if (!query) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: 'query parameter is required' }) }
  }

  const store = loadIndex()
  const queryTokens = tokenize(query)
  const scores = bm25Scores(queryTokens, store)

  const results = scores
    .map((score, idx) => ({ score, idx }))
    .sort((a, b) => b.score - a.score)
    .filter(r => r.score > 0)
    .filter(r => !fileType || store.docs[r.idx].file_type === fileType)
    .slice(0, topK)
    .map(({ score, idx }) => {
      const d = store.docs[idx]
      return {
        score: Math.round(score * 100) / 100,
        repo: d.repo,
        file_type: d.file_type,
        path: d.path,
        content: d.content
      }
    })

  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({ query, count: results.length, results })
  }
}

module.exports = { main }
