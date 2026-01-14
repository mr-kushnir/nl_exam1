DEPLOYER Agent: Ready tasks (MCP) → Build → Deploy → Update Docs → Done

**Input:** None (deploys all Ready) or specific task ID

## CRITICAL REQUIREMENTS

⚠️ **MANDATORY ACTIONS** ⚠️

The DEPLOYER agent MUST:
1. **Verify Infrastructure** - Check all resources exist
2. **Build & Push** - Docker image to registry
3. **Deploy** - To Yandex Cloud Serverless Container
4. **Health Check** - Verify deployment is healthy
5. **Update README.md** - Add deployment URLs, version info
6. **Update CLAUDE.md** - Update deployment status
7. **Commit Documentation** - Git commit with deployment info
8. **Mark Done** - Update task states

**NO deployment is complete without documentation updates.**

---

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
Find YouTrack issues in project NLE with state Ready
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

### Step 7: Update README.md

**⚠️ MANDATORY - Update deployment information:**

```bash
# Read current README.md
cat README.md

# Update with deployment info at the end of Deployment section
cat >> README.md << 'EOF'

## Live Deployment

| Environment | URL | Status |
|-------------|-----|--------|
| Production | https://YOUR_DOMAIN | ✅ Active |

**Current Version:** YYYYMMDD-HHMMSS

### Deployment History

| Date | Version | Status |
|------|---------|--------|
| YYYY-MM-DD | YYYYMMDD-HHMMSS | ✅ Deployed |

EOF
```

Or use Edit tool to update existing deployment section with actual values.

### Step 8: Update CLAUDE.md

**⚠️ MANDATORY - Add deployment status:**

```bash
# Append deployment status to CLAUDE.md
cat >> CLAUDE.md << 'EOF'

---

## Deployment Status

| Metric | Value |
|--------|-------|
| Last Deployment | YYYY-MM-DD HH:MM |
| Version | YYYYMMDD-HHMMSS |
| Environment | Production |
| Health Status | ✅ OK |

### Deployed Services

| Service | Endpoint | Status |
|---------|----------|--------|
| API Gateway | https://domain.ru | ✅ Active |
| Container | cr.yandex/xxx/app | ✅ Running |
| Database | YDB | ✅ Connected |
| Storage | S3 | ✅ Available |

EOF
```

### Step 9: Commit Documentation

**⚠️ MANDATORY COMMIT:**

```bash
git add README.md CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(TASK-ID): deployment documentation update

- Updated README.md with live deployment URLs
- Updated CLAUDE.md with deployment status
- Version: YYYYMMDD-HHMMSS
- Health: OK

Refs TASK-ID
EOF
)"

git push origin main
```

### Step 10: Mark Tasks as Done via MCP

For each Ready task:
```
Update YouTrack issue NLE-2 state to "Done"
Add comment to NLE-2:

🚀 **DEPLOYED**

| Item | Value |
|------|-------|
| URL | https://podcast.rapidapp.ru |
| Version | 20260114-153000 |
| Health | ✅ OK |
| Docs | README.md, CLAUDE.md updated |
```

### Step 12: Check Epic Completion

```
Find YouTrack issues that are subtasks of NLE-1
```

If all subtasks are Done:
```
Update YouTrack issue NLE-1 state to "Done"
Add comment to NLE-1:

✅ **EPIC COMPLETE**

All subtasks deployed to production.

**URL:** https://podcast.rapidapp.ru

**Documentation:**
- README.md: Updated with deployment info
- CLAUDE.md: Updated with deployment status
```

---

## Verification Checklist

Before completing:

- [ ] All Ready tasks deployed
- [ ] Health check passed
- [ ] README.md updated with deployment URLs
- [ ] CLAUDE.md updated with deployment status
- [ ] Documentation committed to git
- [ ] Tasks marked as Done
- [ ] Epic completed (if all subtasks done)

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

📝 Documentation:
  README.md: Updated ✅
  CLAUDE.md: Updated ✅
  Commit: docs(NLE-2): deployment documentation update

Tasks:
  NLE-2: ✅ Done
  NLE-3: ✅ Done
  NLE-4: ✅ Done

Epic NLE-1: ✅ Complete
```

Task ID (optional): $ARGUMENTS
