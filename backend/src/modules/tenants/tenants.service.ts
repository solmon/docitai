import { Injectable } from '@nestjs/common'

@Injectable()
export class TenantsService {
  create(data: any) {
    return { id: 'tenant-' + Math.random().toString(36).slice(2, 8), ...data }
  }
}
