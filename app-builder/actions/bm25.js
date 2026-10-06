const K1 = 1.5
const B = 0.75

function tokenize(text) {
  return text.toLowerCase().split(/[^a-zA-Z0-9_]+/).filter(token => token.length > 2)
}

function bm25Scores(queryTokens, store) {
  const { docs, idf, avgdl } = store
  return docs.map(doc => {
    const length = doc.tokens.length
    let score = 0
    for (const term of queryTokens) {
      const termIdf = idf[term]
      if (!termIdf) continue
      const termFrequency = doc.term_freqs
        ? (doc.term_freqs[term] || 0)
        : doc.tokens.filter(token => token === term).length
      score += termIdf * (termFrequency * (K1 + 1)) /
        (termFrequency + K1 * (1 - B + B * length / avgdl))
    }
    return score
  })
}

module.exports = { tokenize, bm25Scores }
