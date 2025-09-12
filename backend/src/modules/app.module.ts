import { Module } from '@nestjs/common'
import { TenantsModule } from './tenants/tenants.module'
import { DocumentsModule } from './documents/documents.module'

@Module({
  imports: [TenantsModule, DocumentsModule],
})
export class AppModule {}
