Initialize project infrastructure in Yandex Cloud.

**Run ONCE at project start, before any development.**

## What it creates:

1. **Service Account** with roles:
   - serverless.containers.invoker
   - storage.editor
   - ydb.editor
   - certificate-manager.certificates.downloader
   - api-gateway.editor

2. **Container Registry** for Docker images

3. **YDB Serverless** database

4. **Object Storage** bucket (S3)

5. **Wildcard SSL Certificate** (Let's Encrypt)
   - For `*.your-domain.ru`
   - DNS challenge required

6. **API Gateway** with custom domain

## Usage

```bash
./scripts/infra_init.sh [app-name]
```

Or via Claude Code:
```
/infra:init
```

## Prerequisites

Fill `.env` with:
```
YC_TOKEN=y0_xxx
YC_FOLDER_ID=b1gxxx
YANDEX_DOMAIN=podcast.rapidapp.ru
```

## DNS Setup

After running, add DNS records:

**For wildcard certificate validation:**
```
_acme-challenge.rapidapp.ru  TXT  "xxx"
```

**For subdomain:**
```
podcast.rapidapp.ru  CNAME  xxx.apigw.yandexcloud.net
```

Or wildcard:
```
*.rapidapp.ru  CNAME  xxx.apigw.yandexcloud.net
```

## Output

All IDs saved to `.env`:
- YC_SERVICE_ACCOUNT_ID
- YC_REGISTRY_ID
- YC_CERT_ID
- YDB_ENDPOINT
- YDB_DATABASE
- S3_BUCKET
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
