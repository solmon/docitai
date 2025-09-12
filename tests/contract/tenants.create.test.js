const request = require('supertest')

describe('Contract: Tenants API', () => {
  test('POST /tenants should return 201 or 400 for invalid payload', async () => {
    const res = await request('http://localhost:3000')
      .post('/tenants')
      .send({ name: 'test-tenant' })
    expect([201,400]).toContain(res.status)
  })
})
