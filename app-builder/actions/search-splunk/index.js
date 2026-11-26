const INDEX = require('./index.json')
const { tokenize, bm25Scores } = require('../bm25')
const { validateQuery, validateTopK } = require('../request-validation')

const SERVICES = ['live-search', 'product-recommendations', 'payment-services']
const PLATFORMS = ['paas', 'cell']

async function main(params = {}) {
  const headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
  const respond = (statusCode, body) => ({ statusCode, headers, body: JSON.stringify(body) })
  if (!params || typeof params !== 'object' || Array.isArray(params)) {
    return respond(400, { error: 'request parameters must be an object' })
  }
  const query = validateQuery(params.query)
  const topK = validateTopK(params.top_k, 5, 10)
  if (query.error || topK.error) return respond(400, { error: query.error || topK.error })
  if (params.service !== undefined && !SERVICES.includes(params.service)) {
    return respond(400, { error: `service must be one of: ${SERVICES.join(', ')}` })
  }
  if (params.platform !== undefined && !PLATFORMS.includes(params.platform)) {
    return respond(400, { error: `platform must be one of: ${PLATFORMS.join(', ')}` })
  }
  const scores = bm25Scores(tokenize(query.value), INDEX)
  const results = scores.map((score, idx) => ({ score, idx }))
    .filter(({ score, idx }) => score > 0 &&
      (!params.service || INDEX.docs[idx].services.includes(params.service)) &&
      (!params.platform || INDEX.docs[idx].platform === params.platform || INDEX.docs[idx].platform === 'any'))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK.value)
    .map(({ score, idx }) => {
      const doc = INDEX.docs[idx]
      const reference = Object.fromEntries(Object.entries(doc).filter(([key]) => key !== 'tokens' && key !== 'term_freqs'))
      return { ...reference, score: Math.round(score * 100) / 100 }
    })
  return respond(200, {
    query: query.value,
    count: results.length,
    results,
    reference_only: true,
    ...(results.length ? {} : { message: 'No matching bundled reference; this does not mean no logs exist.' })
  })
}

module.exports = { main }
