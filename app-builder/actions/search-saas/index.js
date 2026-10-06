/*
 * Commerce Brain — SaaS Schema Search Action (App Builder)
 * BM25 search over CS GraphQL, gRPC, and PREX REST schema.
 */

const TOP_K = 5
const INDEX = require('./index.json')
const { tokenize, bm25Scores } = require('../bm25')
const { validateQuery, validateTopK } = require('../request-validation')

async function main(params = {}) {
  const headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
  if (!params || typeof params !== 'object' || Array.isArray(params)) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: 'request parameters must be an object' }) }
  }
  const queryInput = validateQuery(params.query)
  if (queryInput.error) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: queryInput.error }) }
  }
  const topKInput = validateTopK(params.top_k, TOP_K, 10)
  if (topKInput.error) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: topKInput.error }) }
  }

  const query = queryInput.value
  const topK = topKInput.value
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
