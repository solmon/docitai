# storage-adapter

Cloud storage provider abstraction layer supporting S3, Azure Blob, and Google Cloud Storage.

## Features

- **Multi-Cloud Support**: S3, Azure Blob Storage, Google Cloud Storage
- **Provider Pattern**: Pluggable storage implementations
- **Credential Encryption**: Secure credential management
- **Connection Validation**: Provider-specific connection testing

## Installation

```bash
uv pip install -e .
```

## Supported Providers

- AWS S3
- Azure Blob Storage
- Google Cloud Storage
