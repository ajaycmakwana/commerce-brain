jest.mock('../actions/search-splunk/index.json', () => ({
  n: 3,
  avgdl: 1,
  idf: { sensei: 1 },
  docs: [
    { id: 'pay', services: ['payment-services'], platform: 'any', tokens: ['sensei'], term_freqs: { sensei: 1 } },
    { id: 'paas', services: ['product-recommendations'], platform: 'paas', tokens: ['sensei'], term_freqs: { sensei: 1 } },
    {
      id: 'cell',
      services: ['product-recommendations'],
      platform: 'cell',
      tokens: ['sensei'],
      term_freqs: { sensei: 1 },
      source_url: 'https://wiki.corp.adobe.com/pages/viewpage.action?pageId=3990723578',
      source_revision: 11,
      validation_status: 'source-reviewed-not-live-tested',
      content: '```spl\nindex=fixture\n```'
    }
  ]
}), { virtual: true })

const { main } = require('../actions/search-splunk')

test('filters service and platform before top K and preserves complete source metadata', async () => {
  const response = await main({ query: 'sensei', service: 'product-recommendations', platform: 'cell', top_k: 1 })
  const body = JSON.parse(response.body)
  expect(response.statusCode).toBe(200)
  expect(body.reference_only).toBe(true)
  expect(body.results.map(doc => doc.id)).toEqual(['cell'])
  expect(body.results[0].source_revision).toBe(11)
  expect(body.results[0].content).toBe('```spl\nindex=fixture\n```')
  expect(body.results[0].tokens).toBeUndefined()
  expect(body.results[0].term_freqs).toBeUndefined()
})

test.each([
  null, [], { query: '' }, { query: 'sensei', top_k: 0 },
  { query: 'sensei', top_k: 11 }, { query: 'sensei', top_k: true },
  { query: 'sensei', service: 'unknown' }, { query: 'sensei', platform: 'unknown' }
])('rejects invalid arguments %p', async params => {
  expect((await main(params)).statusCode).toBe(400)
})

test('missing reference is not reported as missing logs', async () => {
  const response = await main({ query: 'unindexedterm' })
  const body = JSON.parse(response.body)
  expect(body.results).toEqual([])
  expect(body.message).toContain('does not mean no logs exist')
})

test('equal scores retain source order', async () => {
  const body = JSON.parse((await main({ query: 'sensei' })).body)
  expect(body.results.map(doc => doc.id)).toEqual(['pay', 'paas', 'cell'])
})
