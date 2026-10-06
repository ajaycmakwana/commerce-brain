const { bm25Scores, tokenize } = require('../actions/bm25')

function legacyBm25Scores(queryTokens, store) {
  const { docs, idf, avgdl } = store
  return docs.map(doc => {
    const dl = doc.tokens.length
    let score = 0
    for (const term of queryTokens) {
      const termIdf = idf[term]
      if (!termIdf) continue
      const tf = doc.tokens.filter(token => token === term).length
      score += termIdf * (tf * 2.5) / (tf + 1.5 * (1 - 0.75 + 0.75 * dl / avgdl))
    }
    return score
  })
}

describe('shared BM25 scoring', () => {
  const docs = [
    { tokens: ['product', 'feed', 'feed', 'schema'] },
    { tokens: ['product', 'indexer', 'schema'] },
    { tokens: ['catalog', 'price', 'schema'] },
    { tokens: ['product', 'feed', 'indexer', 'feed'] }
  ]
  const store = {
    docs: docs.map(doc => ({
      ...doc,
      term_freqs: doc.tokens.reduce((freqs, term) => {
        freqs[term] = (freqs[term] || 0) + 1
        return freqs
      }, {})
    })),
    idf: { product: 0.7, feed: 1.1, schema: 0.5, indexer: 0.9, price: 1.3 },
    avgdl: docs.reduce((sum, doc) => sum + doc.tokens.length, 0) / docs.length
  }

  test.each([
    'product feed',
    'schema indexer',
    'feed feed product',
    'price catalog unknown'
  ])('preserves scores and ranking for query %s', query => {
    const queryTokens = tokenize(query)
    const actual = bm25Scores(queryTokens, store)
    const expected = legacyBm25Scores(queryTokens, store)
    expect(actual).toEqual(expected)
    expect(actual.map((score, idx) => ({ score, idx })).sort((a, b) => b.score - a.score))
      .toEqual(expected.map((score, idx) => ({ score, idx })).sort((a, b) => b.score - a.score))
  })

  test('falls back to token counting for older bundled indexes', () => {
    const olderStore = { ...store, docs }
    expect(bm25Scores(tokenize('feed product'), olderStore))
      .toEqual(legacyBm25Scores(tokenize('feed product'), olderStore))
  })
})
