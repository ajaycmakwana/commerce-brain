jest.mock('../actions/search/index.json', () => ({
  n: 3,
  avgdl: 2,
  idf: { sample_table: 1, query: 0.5 },
  docs: [
    {
      repo: 'module-a',
      file_type: 'db_schema',
      path: 'module-a/etc/db_schema.xml :: sample_table',
      content: '<table name="sample_table"><column name="first"/></table>',
      tokens: ['sample_table', 'column'],
      term_freqs: { sample_table: 1, column: 1 }
    },
    {
      repo: 'module-b',
      file_type: 'db_schema',
      path: 'module-b/etc/db_schema.xml :: sample_table',
      content: '<table name="sample_table"><column name="second"/></table>',
      tokens: ['sample_table', 'column'],
      term_freqs: { sample_table: 1, column: 1 }
    },
    {
      repo: 'module-c',
      file_type: 'db_schema',
      path: 'module-c/etc/db_schema.xml :: sample_table_suffix',
      content: '<table name="sample_table_suffix"/>',
      tokens: ['sample_table', 'suffix'],
      term_freqs: { sample_table: 1, suffix: 1 }
    }
  ]
}), { virtual: true })

const action = require('../actions/search/index.js')

describe('Commerce search action', () => {
  test('exact table lookup returns all exact declarations without BM25 top-K truncation', async () => {
    const response = await action.main({ table_name: 'sample_table', top_k: 1 })
    const body = JSON.parse(response.body)
    expect(response.statusCode).toBe(200)
    expect(body.count).toBe(2)
    expect(body.results.map(result => result.repo)).toEqual(['module-a', 'module-b'])
    expect(body.results[0].content).toContain('<column name="first"/>')
    expect(body.results[1].content).toContain('<column name="second"/>')
  })

  test('returns no match distinctly and rejects invalid lookup names', async () => {
    const missing = await action.main({ table_name: 'unknown_table' })
    expect(JSON.parse(missing.body).results).toEqual([])
    const invalid = await action.main({ table_name: 'bad;name' })
    expect(invalid.statusCode).toBe(400)
  })

  test('validates regular-search query and top_k', async () => {
    expect((await action.main({ query: '  ' })).statusCode).toBe(400)
    expect((await action.main({ query: 'query', top_k: 21 })).statusCode).toBe(400)
    expect((await action.main({ query: 'query', top_k: 1 })).statusCode).toBe(200)
  })
})
