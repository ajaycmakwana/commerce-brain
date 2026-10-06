const { findTableDocuments, validateTableName } = require('../actions/schema-lookup')
const { validateQuery, validateTopK } = require('../actions/request-validation')

describe('exact schema lookup', () => {
  const docs = [
    { file_type: 'db_schema', path: 'module-a/etc/db_schema.xml :: catalog_product_entity', repo: 'module-a' },
    { file_type: 'db_schema', path: 'module-b/etc/db_schema.xml :: catalog_product_entity', repo: 'module-b' },
    { file_type: 'db_schema', path: 'module-c/etc/db_schema.xml :: catalog_product_entity_varchar', repo: 'module-c' },
    { file_type: 'command', path: 'module-a/Command.php :: catalog_product_entity', repo: 'module-a' }
  ]

  test('returns every exact matching module declaration and not similarly named tables', () => {
    expect(findTableDocuments(docs, 'catalog_product_entity').map(doc => doc.repo))
      .toEqual(['module-a', 'module-b'])
    expect(findTableDocuments(docs, 'missing_table')).toEqual([])
  })

  test.each(['', 'table name', 'table-name', 'table.name', 'table;drop'])(
    'rejects an invalid table identifier: %s',
    tableName => expect(validateTableName(tableName).error).toBeTruthy()
  )

  test('trims valid table names and rejects non-string values', () => {
    expect(validateTableName(' catalog_product_entity ')).toEqual({ value: 'catalog_product_entity' })
    expect(validateTableName(null).error).toBeTruthy()
  })
})

describe('search request validation', () => {
  test('requires a non-empty string query', () => {
    expect(validateQuery(' feed schema ')).toEqual({ value: 'feed schema' })
    expect(validateQuery('  ').error).toBeTruthy()
    expect(validateQuery(42).error).toBeTruthy()
  })

  test('accepts bounded integer top_k and rejects invalid values', () => {
    expect(validateTopK(undefined, 5, 10)).toEqual({ value: 5 })
    expect(validateTopK('10', 5, 10)).toEqual({ value: 10 })
    for (const value of [0, -1, 11, 1.5, '1.5', 'abc', true]) {
      expect(validateTopK(value, 5, 10).error).toBeTruthy()
    }
  })
})
