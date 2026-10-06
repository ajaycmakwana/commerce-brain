const TABLE_NAME_PATTERN = /^[A-Za-z0-9_]{1,255}$/

function validateTableName(value) {
  if (typeof value !== 'string') return { error: 'table_name must be a string' }
  const tableName = value.trim()
  if (!TABLE_NAME_PATTERN.test(tableName)) {
    return { error: 'table_name must contain only letters, numbers, and underscores' }
  }
  return { value: tableName }
}

function findTableDocuments(docs, tableName) {
  const suffix = ` :: ${tableName}`
  return docs.filter(doc =>
    doc.file_type === 'db_schema' &&
    typeof doc.path === 'string' &&
    doc.path.endsWith(suffix)
  )
}

module.exports = { findTableDocuments, validateTableName }
