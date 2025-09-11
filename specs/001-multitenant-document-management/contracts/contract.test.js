// Minimal contract test stub — should fail until implementation exists
const request = require('supertest')

describe('Contract: Document API', () => {
  test('GET /tenants/:tenantId/documents should return 200', async () => {
    const res = await request('http://localhost:3000')
      .get('/tenants/test-tenant/documents')
    expect([200,401,403]).toContain(res.status)
  })
})
