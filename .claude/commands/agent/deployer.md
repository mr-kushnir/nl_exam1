DEPLOYER Agent: Ready tasks (MCP) → Build → Deploy → Done

**Input:** None (deploys all Ready) or specific task ID

## Prerequisites

Infrastructure must be created first:
```
/infra:init
```

This creates:
- Service Account
- Container Registry
- YDB Database
- S3 Bucket
- Wildcard Certificate
- API Gateway with domain

---

## Workflow

### Step 1: Find Ready Tasks via MCP

```
Find YouTrack issues in project POD with state Ready
```

### Step 2: Verify Infrastructure

```bash
# Check .env has required values
grep -q "YC_REGISTRY_ID" .env && echo "Registry: OK"
grep -q "YC_SERVICE_ACCOUNT_ID" .env && echo "SA: OK"
grep -q "YC_CERT_ID" .env && echo "Cert: OK"
```

If missing, run `/infra:init` first.

### Step 3: Build Container

```bash
# Create Dockerfile if needed
if [ ! -f Dockerfile ]; then
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
ENV PYTHONUNBUFFERED=1 PORT=8080
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF
fi

# Build
VERSION=$(date +%Y%m%d-%H%M%S)
docker build -t cr.yandex/$YC_REGISTRY_ID/$APP_NAME:$VERSION .
```

### Step 4: Push to Registry

```bash
yc container registry configure-docker
docker push cr.yandex/$YC_REGISTRY_ID/$APP_NAME:$VERSION
```

### Step 5: Deploy Container

```bash
yc serverless container revision deploy \
    --container-name $APP_NAME \
    --image cr.yandex/$YC_REGISTRY_ID/$APP_NAME:$VERSION \
    --cores 1 \
    --memory 512MB \
    --concurrency 4 \
    --execution-timeout 30s \
    --service-account-id $YC_SERVICE_ACCOUNT_ID \
    --environment "YDB_ENDPOINT=$YDB_ENDPOINT,YDB_DATABASE=$YDB_DATABASE,S3_BUCKET=$S3_BUCKET,BOT_TOKEN=$BOT_TOKEN"
```

### Step 6: Health Check

```bash
CONTAINER_URL=$(yc serverless container get $APP_NAME --format json | jq -r '.url')

sleep 5
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CONTAINER_URL/health")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    # Consider rollback
fi
```

### Step 7: Mark Tasks as Done via MCP

For each Ready task:
```
Update YouTrack issue POD-2 state to "Done"
Add comment to POD-2:

🚀 **DEPLOYED**

| Item | Value |
|------|-------|
| URL | https://podcast.rapidapp.ru |
| Version | 20260114-153000 |
| Health | ✅ OK |
```

### Step 8: Check Epic Completion

```
Find YouTrack issues that are subtasks of POD-1
```

If all subtasks are Done:
```
Update YouTrack issue POD-1 state to "Done"
Add comment to POD-1:

✅ **EPIC COMPLETE**

All subtasks deployed to production.

**URL:** https://podcast.rapidapp.ru
```

---

## Rollback

If deployment fails:

```bash
# List revisions
yc serverless container revision list --container-name $APP_NAME

# Rollback
PREV=$(yc serverless container revision list --container-name $APP_NAME --format json | jq -r '.[1].id')
yc serverless container rollback --container-name $APP_NAME --revision-id $PREV
```

---

## Output Format

```
═══════════════════════════════════════════════════════════
🚀 DEPLOYER Complete
═══════════════════════════════════════════════════════════

📦 Image: cr.yandex/xxx/app:20260114-153000
🌐 URL: https://podcast.rapidapp.ru
🏥 Health: ✅ OK

Tasks:
  POD-2: ✅ Done
  POD-3: ✅ Done
  POD-4: ✅ Done

Epic POD-1: ✅ Complete
```

Task ID (optional): $ARGUMENTS
