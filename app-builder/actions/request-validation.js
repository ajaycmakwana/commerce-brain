function validateQuery(value) {
  if (typeof value !== 'string' || value.trim().length === 0) {
    return { error: 'query parameter is required' }
  }
  return { value: value.trim() }
}

function validateTopK(value, defaultValue, maximum) {
  if (value === undefined) {
    return { value: defaultValue }
  }
  const parsed = typeof value === 'number'
    ? value
    : typeof value === 'string' && /^\d+$/.test(value.trim())
      ? Number(value.trim())
      : NaN
  if (!Number.isSafeInteger(parsed) || parsed < 1 || parsed > maximum) {
    return { error: `top_k must be an integer between 1 and ${maximum}` }
  }
  return { value: parsed }
}

module.exports = { validateQuery, validateTopK }
