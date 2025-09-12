const request = require('supertest')

describe('Contract: Documents API', () => {
  test('POST /tenants/:tenantId/documents should accept multipart upload (201/400)', async () => {
    const res = await request('http://localhost:3000')
      .post('/tenants/test-tenant/documents')
      .field('folderId', 'root')
      .attach('file', Buffer.from('test'), 'test.txt')
    expect([201,400]).toContain(res.status)
  })

  test('GET /tenants/:tenantId/documents/:documentId should return 200 or 404', async () => {
    const res = await request('http://localhost:3000')
      .get('/tenants/test-tenant/documents/test-doc')
    expect([200,404]).toContain(res.status)
  })
})
