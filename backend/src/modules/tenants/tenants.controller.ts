import { Controller, Post, Body } from '@nestjs/common'

@Controller('tenants')
export class TenantsController {
  @Post()
  create(@Body() body: any) {
    // Minimal stub: return 201 with created tenant id
    return { id: 'tenant-' + Math.random().toString(36).slice(2, 8), ...body }
  }
}
