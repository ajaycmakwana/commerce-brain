/*
 * Commerce Brain — SaaS Schema Search Action (App Builder)
 * BM25 search over CS GraphQL, gRPC, and PREX REST schema.
 */

const TOP_K = 5
const K1 = 1.5
const B = 0.75

const INDEX = require('./index.json')

function tokenize(text) {
  return text.toLowerCase().split(/[^a-zA-Z0-9_]+/).filter(t => t.length > 2)
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
  const topK = Math.min(parseInt(params.top_k || TOP_K, 10), 10)

  const headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }

  if (!query) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: 'query parameter is required' }) }
  }

  const store = INDEX
  const queryTokens = tokenize(query)
  const scores = bm25Scores(queryTokens, store)

  const results = scores
    .map((score, idx) => ({ score, idx }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK)
    .filter(r => r.score > 0)
    .map(({ score, idx }) => {
      const d = store.docs[idx]
      return {
        score: Math.round(score * 100) / 100,
        source: d.source,
        title: d.title,
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
