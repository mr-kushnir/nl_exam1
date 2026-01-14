#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Deploy Script v3.2
# Uses infrastructure created by infra_init.sh
# ═══════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}❌ .env not found${NC}"
    exit 1
fi

APP_NAME="${1:-$(basename $(pwd))}"
VERSION="${2:-$(date +%Y%m%d-%H%M%S)}"

# ─────────────────────────────────────────────────────────────
# Validate infrastructure exists
# ─────────────────────────────────────────────────────────────

echo -e "${BLUE}Checking infrastructure...${NC}"

MISSING=""
[ -z "$YC_REGISTRY_ID" ] && MISSING="$MISSING YC_REGISTRY_ID"
[ -z "$YC_SERVICE_ACCOUNT_ID" ] && MISSING="$MISSING YC_SERVICE_ACCOUNT_ID"
[ -z "$YDB_ENDPOINT" ] && MISSING="$MISSING YDB_ENDPOINT"

if [ -n "$MISSING" ]; then
    echo -e "${RED}❌ Missing in .env:$MISSING${NC}"
    echo -e "${YELLOW}Run /infra:init first${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Infrastructure ready${NC}"

# ─────────────────────────────────────────────────────────────
# Build
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}Building...${NC}"

# Create Dockerfile if not exists
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

IMAGE="cr.yandex/$YC_REGISTRY_ID/$APP_NAME:$VERSION"
docker build -t $IMAGE .
echo -e "${GREEN}✓ Built: $IMAGE${NC}"

# ─────────────────────────────────────────────────────────────
# Push
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}Pushing...${NC}"
yc container registry configure-docker 2>/dev/null || true
docker push $IMAGE
echo -e "${GREEN}✓ Pushed${NC}"

# ─────────────────────────────────────────────────────────────
# Deploy
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}Deploying...${NC}"

# Build env vars
ENV_VARS="BOT_TOKEN=${BOT_TOKEN:-}"
[ -n "$YDB_ENDPOINT" ] && ENV_VARS="$ENV_VARS,YDB_ENDPOINT=$YDB_ENDPOINT"
[ -n "$YDB_DATABASE" ] && ENV_VARS="$ENV_VARS,YDB_DATABASE=$YDB_DATABASE"
[ -n "$S3_BUCKET" ] && ENV_VARS="$ENV_VARS,S3_BUCKET=$S3_BUCKET"
[ -n "$AWS_ACCESS_KEY_ID" ] && ENV_VARS="$ENV_VARS,AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
[ -n "$AWS_SECRET_ACCESS_KEY" ] && ENV_VARS="$ENV_VARS,AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"

yc serverless container revision deploy \
    --container-name $APP_NAME \
    --image $IMAGE \
    --cores 1 \
    --memory 512MB \
    --concurrency 4 \
    --execution-timeout 30s \
    --service-account-id $YC_SERVICE_ACCOUNT_ID \
    --environment "$ENV_VARS"

CONTAINER_URL=$(yc serverless container get $APP_NAME --format json | jq -r '.url')
echo -e "${GREEN}✓ Deployed: $CONTAINER_URL${NC}"

# ─────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}Health check...${NC}"
sleep 5

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CONTAINER_URL/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Healthy${NC}"
    HEALTH="✅ OK"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CONTAINER_URL/" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" != "000" ]; then
        echo -e "${YELLOW}⚠ Responding (HTTP $HTTP_CODE)${NC}"
        HEALTH="⚠ Responding"
    else
        echo -e "${RED}✗ Failed${NC}"
        HEALTH="❌ Failed"
    fi
fi

# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ DEPLOYED${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "📦 Image:   ${GREEN}$IMAGE${NC}"
echo -e "🌐 URL:     ${GREEN}$CONTAINER_URL${NC}"
[ -n "$YANDEX_DOMAIN" ] && echo -e "🔗 Domain:  ${GREEN}https://$YANDEX_DOMAIN${NC}"
echo -e "🏥 Health:  $HEALTH"
echo ""

# Save deploy info
cat > .deploy_info << EOF
DEPLOY_IMAGE=$IMAGE
DEPLOY_URL=$CONTAINER_URL
DEPLOY_DOMAIN=${YANDEX_DOMAIN:-}
DEPLOY_VERSION=$VERSION
DEPLOY_TIME=$(date -Iseconds)
DEPLOY_HEALTH=$HEALTH
EOF
