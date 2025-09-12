import { Controller, Post, Get, Param, UploadedFile, UseInterceptors } from '@nestjs/common'
import { FileInterceptor } from '@nestjs/platform-express'
import { DocumentsService } from './documents.service'

@Controller('tenants/:tenantId/documents')
export class DocumentsController {
  constructor(private readonly svc: DocumentsService) {}

  @Post()
  @UseInterceptors(FileInterceptor('file'))
  upload(@Param('tenantId') tenantId: string, @UploadedFile() file: any) {
    return this.svc.upload(tenantId, file)
  }

  @Get(':documentId')
  download(@Param('tenantId') tenantId: string, @Param('documentId') documentId: string) {
    return this.svc.download(tenantId, documentId)
  }
}
