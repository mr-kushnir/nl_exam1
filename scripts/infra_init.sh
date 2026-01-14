#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Infrastructure Init Script
# Creates: Service Account, YDB, S3, Container Registry,
#          Wildcard Certificate, API Gateway with subdomain
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
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Copy .env.example to .env and fill in the values"
    exit 1
fi

# Validate required vars
if [ -z "$YC_FOLDER_ID" ] || [ -z "$YANDEX_DOMAIN" ]; then
    echo -e "${RED}❌ Required: YC_FOLDER_ID and YANDEX_DOMAIN in .env${NC}"
    exit 1
fi

# Extract base domain for wildcard (e.g., rapidapp.ru from podcast.rapidapp.ru)
SUBDOMAIN=$(echo $YANDEX_DOMAIN | cut -d. -f1)
BASE_DOMAIN=$(echo $YANDEX_DOMAIN | cut -d. -f2-)

APP_NAME="${1:-$(basename $(pwd))}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🏗️  Infrastructure Init: $APP_NAME${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Subdomain: ${GREEN}$SUBDOMAIN${NC}"
echo -e "Base domain: ${GREEN}$BASE_DOMAIN${NC}"
echo -e "Full domain: ${GREEN}$YANDEX_DOMAIN${NC}"
echo ""

# ─────────────────────────────────────────────────────────────
# 1. Service Account
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}[1/7] Creating Service Account...${NC}"

SA_NAME="${APP_NAME}-sa"
SA_EXISTS=$(yc iam service-account list --format json | jq -r ".[] | select(.name==\"$SA_NAME\") | .id")

if [ -z "$SA_EXISTS" ]; then
    yc iam service-account create --name $SA_NAME --description "Service account for $APP_NAME"
    SA_ID=$(yc iam service-account get $SA_NAME --format json | jq -r '.id')
    
    # Grant roles
    for ROLE in \
        serverless.containers.invoker \
        storage.editor \
        ydb.editor \
        certificate-manager.certificates.downloader \
        api-gateway.editor
    do
        yc resource-manager folder add-access-binding $YC_FOLDER_ID \
            --role $ROLE \
            --subject serviceAccount:$SA_ID 2>/dev/null || true
    done
    
    echo -e "${GREEN}✓ Created SA: $SA_ID${NC}"
else
    SA_ID=$SA_EXISTS
    echo -e "${GREEN}✓ SA exists: $SA_ID${NC}"
fi

# Save SA ID
grep -v "^YC_SERVICE_ACCOUNT_ID=" .env > .env.tmp 2>/dev/null || true
echo "YC_SERVICE_ACCOUNT_ID=$SA_ID" >> .env.tmp
mv .env.tmp .env

# ─────────────────────────────────────────────────────────────
# 2. Container Registry
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}[2/7] Creating Container Registry...${NC}"

REGISTRY_NAME="${APP_NAME}-registry"
REGISTRY_EXISTS=$(yc container registry list --format json | jq -r ".[] | select(.name==\"$REGISTRY_NAME\") | .id")

if [ -z "$REGISTRY_EXISTS" ]; then
    yc container registry create --name $REGISTRY_NAME
    REGISTRY_ID=$(yc container registry get $REGISTRY_NAME --format json | jq -r '.id')
    echo -e "${GREEN}✓ Created Registry: $REGISTRY_ID${NC}"
else
    REGISTRY_ID=$REGISTRY_EXISTS
    echo -e "${GREEN}✓ Registry exists: $REGISTRY_ID${NC}"
fi

# Save Registry ID
grep -v "^YC_REGISTRY_ID=" .env > .env.tmp 2>/dev/null || true
echo "YC_REGISTRY_ID=$REGISTRY_ID" >> .env.tmp
mv .env.tmp .env

# ─────────────────────────────────────────────────────────────
# 3. YDB Database
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}[3/7] Creating YDB Database...${NC}"

DB_NAME="${APP_NAME}-db"
DB_EXISTS=$(yc ydb database list --format json | jq -r ".[] | select(.name==\"$DB_NAME\") | .name")

if [ -z "$DB_EXISTS" ]; then
    yc ydb database create --name $DB_NAME --serverless
    
    # Wait for ready
    echo "Waiting for database..."
    sleep 10
    
    echo -e "${GREEN}✓ Created YDB: $DB_NAME${NC}"
else
    echo -e "${GREEN}✓ YDB exists: $DB_NAME${NC}"
fi

# Get connection info
YDB_INFO=$(yc ydb database get $DB_NAME --format json)
YDB_ENDPOINT=$(echo $YDB_INFO | jq -r '.endpoint')
YDB_DATABASE=$(echo $YDB_INFO | jq -r '.database_path')

# Save to .env
grep -v "^YDB_ENDPOINT=" .env > .env.tmp && mv .env.tmp .env
grep -v "^YDB_DATABASE=" .env > .env.tmp && mv .env.tmp .env
echo "YDB_ENDPOINT=$YDB_ENDPOINT" >> .env
echo "YDB_DATABASE=$YDB_DATABASE" >> .env

# ─────────────────────────────────────────────────────────────
# 4. Object Storage
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}[4/7] Creating Object Storage...${NC}"

BUCKET_NAME="${APP_NAME}-files"
BUCKET_EXISTS=$(yc storage bucket list --format json 2>/dev/null | jq -r ".[] | select(.name==\"$BUCKET_NAME\") | .name")

if [ -z "$BUCKET_EXISTS" ]; then
    yc storage bucket create --name $BUCKET_NAME --default-storage-class standard
    echo -e "${GREEN}✓ Created Bucket: $BUCKET_NAME${NC}"
else
    echo -e "${GREEN}✓ Bucket exists: $BUCKET_NAME${NC}"
fi

# Create S3 access keys if needed
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "Creating S3 access keys..."
    KEY_INFO=$(yc iam access-key create --service-account-name $SA_NAME --format json)
    AWS_ACCESS_KEY_ID=$(echo $KEY_INFO | jq -r '.access_key.key_id')
    AWS_SECRET_ACCESS_KEY=$(echo $KEY_INFO | jq -r '.secret')
    
    echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" >> .env
    echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> .env
fi

grep -v "^S3_BUCKET=" .env > .env.tmp && mv .env.tmp .env
echo "S3_BUCKET=$BUCKET_NAME" >> .env

# ─────────────────────────────────────────────────────────────
# 5. Wildcard Certificate (Let's Encrypt)
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}[5/7] Creating Wildcard Certificate...${NC}"

CERT_NAME="${APP_NAME}-wildcard-cert"
CERT_EXISTS=$(yc certificate-manager certificate list --format json | jq -r ".[] | select(.name==\"$CERT_NAME\") | .id")

if [ -z "$CERT_EXISTS" ]; then
    echo -e "${YELLOW}Creating Let's Encrypt wildcard certificate for *.${BASE_DOMAIN}${NC}"
    
    # Create certificate request
    CERT_RESULT=$(yc certificate-manager certificate request \
        --name $CERT_NAME \
        --domains "*.$BASE_DOMAIN,$BASE_DOMAIN" \
        --challenge dns \
        --format json)
    
    CERT_ID=$(echo $CERT_RESULT | jq -r '.id')
    
    echo ""
    echo -e "${YELLOW}⚠️  DNS Challenge Required!${NC}"
    echo ""
    echo "Add these DNS records to validate the certificate:"
    echo ""
    
    # Get challenge records
    sleep 3
    CERT_INFO=$(yc certificate-manager certificate get $CERT_ID --format json)
    
    echo $CERT_INFO | jq -r '.challenges[] | "Type: \(.type)\nName: \(.dns_challenge.name)\nValue: \(.dns_challenge.value)\n"'
    
    echo ""
    echo -e "${YELLOW}After adding DNS records, certificate will be issued automatically.${NC}"
    echo -e "Check status: ${GREEN}yc certificate-manager certificate get $CERT_ID${NC}"
    echo ""
    
    CERT_ID=$CERT_ID
else
    CERT_ID=$CERT_EXISTS
    CERT_STATUS=$(yc certificate-manager certificate get $CERT_ID --format json | jq -r '.status')
    echo -e "${GREEN}✓ Certificate exists: $CERT_ID (status: $CERT_STATUS)${NC}"
fi

# Save cert ID
grep -v "^YC_CERT_ID=" .env > .env.tmp 2>/dev/null || true
echo "YC_CERT_ID=$CERT_ID" >> .env.tmp
mv .env.tmp .env

# ─────────────────────────────────────────────────────────────
# 6. Serverless Container (placeholder)
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}[6/7] Creating Serverless Container...${NC}"

CONTAINER_NAME=$APP_NAME
CONTAINER_EXISTS=$(yc serverless container list --format json | jq -r ".[] | select(.name==\"$CONTAINER_NAME\") | .id")

if [ -z "$CONTAINER_EXISTS" ]; then
    yc serverless container create --name $CONTAINER_NAME
    CONTAINER_ID=$(yc serverless container get $CONTAINER_NAME --format json | jq -r '.id')
    echo -e "${GREEN}✓ Created Container: $CONTAINER_ID${NC}"
else
    CONTAINER_ID=$CONTAINER_EXISTS
    echo -e "${GREEN}✓ Container exists: $CONTAINER_ID${NC}"
fi

# ─────────────────────────────────────────────────────────────
# 7. API Gateway with Custom Domain
# ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}[7/7] Creating API Gateway with subdomain...${NC}"

GATEWAY_NAME="${APP_NAME}-gateway"
GATEWAY_EXISTS=$(yc serverless api-gateway list --format json | jq -r ".[] | select(.name==\"$GATEWAY_NAME\") | .id")

if [ -z "$GATEWAY_EXISTS" ]; then
    # Create API Gateway spec
    cat > /tmp/api-gateway-spec.yaml << EOF
openapi: 3.0.0
info:
  title: $APP_NAME API
  version: 1.0.0
paths:
  /:
    x-yc-apigateway-any-method:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: $CONTAINER_ID
        service_account_id: $SA_ID
  /{path+}:
    x-yc-apigateway-any-method:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: $CONTAINER_ID
        service_account_id: $SA_ID
      parameters:
        - name: path
          in: path
          required: false
          schema:
            type: string
EOF

    yc serverless api-gateway create \
        --name $GATEWAY_NAME \
        --spec /tmp/api-gateway-spec.yaml
    
    GATEWAY_ID=$(yc serverless api-gateway get $GATEWAY_NAME --format json | jq -r '.id')
    GATEWAY_DOMAIN=$(yc serverless api-gateway get $GATEWAY_NAME --format json | jq -r '.domain')
    
    echo -e "${GREEN}✓ Created Gateway: $GATEWAY_ID${NC}"
    echo -e "${GREEN}✓ Gateway domain: $GATEWAY_DOMAIN${NC}"
else
    GATEWAY_ID=$GATEWAY_EXISTS
    GATEWAY_DOMAIN=$(yc serverless api-gateway get $GATEWAY_NAME --format json | jq -r '.domain')
    echo -e "${GREEN}✓ Gateway exists: $GATEWAY_ID${NC}"
fi

# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ INFRASTRUCTURE READY${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "📦 Service Account: ${GREEN}$SA_ID${NC}"
echo -e "📦 Registry:        ${GREEN}$REGISTRY_ID${NC}"
echo -e "📊 YDB Database:    ${GREEN}$DB_NAME${NC}"
echo -e "📁 S3 Bucket:       ${GREEN}$BUCKET_NAME${NC}"
echo -e "🔐 Certificate:     ${GREEN}$CERT_ID${NC}"
echo -e "📦 Container:       ${GREEN}$CONTAINER_ID${NC}"
echo -e "🌐 API Gateway:     ${GREEN}$GATEWAY_ID${NC}"
echo ""
echo -e "${YELLOW}📋 DNS Configuration Required:${NC}"
echo ""
echo -e "Add CNAME record:"
echo -e "  ${GREEN}$SUBDOMAIN.$BASE_DOMAIN${NC} → ${GREEN}$GATEWAY_DOMAIN${NC}"
echo ""
echo -e "Or for wildcard (recommended):"
echo -e "  ${GREEN}*.$BASE_DOMAIN${NC} → ${GREEN}$GATEWAY_DOMAIN${NC}"
echo ""

# Check certificate status
CERT_STATUS=$(yc certificate-manager certificate get $CERT_ID --format json 2>/dev/null | jq -r '.status')
if [ "$CERT_STATUS" != "ISSUED" ]; then
    echo -e "${YELLOW}⚠️  Certificate status: $CERT_STATUS${NC}"
    echo -e "Certificate will be issued after DNS validation."
    echo -e "Check: ${GREEN}yc certificate-manager certificate get $CERT_ID${NC}"
else
    echo -e "${GREEN}✅ Certificate: ISSUED${NC}"
    
    # Attach domain to gateway if cert is ready
    echo -e "${YELLOW}Attaching custom domain to API Gateway...${NC}"
    yc serverless api-gateway add-domain \
        --name $GATEWAY_NAME \
        --domain $YANDEX_DOMAIN \
        --certificate-id $CERT_ID 2>/dev/null || true
    
    echo -e "${GREEN}✅ Domain attached: https://$YANDEX_DOMAIN${NC}"
fi

echo ""
echo -e "Next steps:"
echo -e "  1. Add DNS records (see above)"
echo -e "  2. Wait for certificate validation"
echo -e "  3. Run ${GREEN}/agent:business EPIC-ID${NC} to start development"
echo ""
