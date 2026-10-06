/*
 * Commerce Brain — Search Action (App Builder)
 * BM25 search over bundled Adobe Commerce source references.
 *
 * Index is bundled with the action (index.json).
 * Loaded once on cold start and cached in memory.
 */

const TOP_K = 5
// Bundled by webpack at build time — no runtime file I/O needed
const INDEX = require('./index.json')
const { tokenize, bm25Scores } = require('../bm25')
const { validateQuery, validateTopK } = require('../request-validation')
const { findTableDocuments, validateTableName } = require('../schema-lookup')

function loadIndex() {
  return INDEX
}

async function main(params = {}) {
  const headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }

  if (!params || typeof params !== 'object' || Array.isArray(params)) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: 'request parameters must be an object' }) }
  }

  if (params.table_name !== undefined) {
    const validatedTable = validateTableName(params.table_name)
    if (validatedTable.error) {
      return { statusCode: 400, headers, body: JSON.stringify({ error: validatedTable.error }) }
    }
    const matches = findTableDocuments(INDEX.docs, validatedTable.value).map(doc => ({
      repo: doc.repo,
      file_type: doc.file_type,
      path: doc.path,
      content: doc.content
    }))
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        query: validatedTable.value,
        count: matches.length,
        results: matches,
        ...(matches.length ? {} : { error: `Table '${validatedTable.value}' not found in the bundled Commerce schema index` })
      })
    }
  }

  const queryInput = validateQuery(params.query)
  if (queryInput.error) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: queryInput.error }) }
  }
  const topKInput = validateTopK(params.top_k, TOP_K, 20)
  if (topKInput.error) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: topKInput.error }) }
  }
  if (params.file_type !== undefined && typeof params.file_type !== 'string') {
    return { statusCode: 400, headers, body: JSON.stringify({ error: 'file_type must be a string' }) }
  }

  const query = queryInput.value
  const topK = topKInput.value
  const fileType = (params.file_type || '').trim()
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
