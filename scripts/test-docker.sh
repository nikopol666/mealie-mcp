#!/bin/bash
set -e

echo "🐳 Testing Docker build locally"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Build image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t mealie-mcp:test .

# Test image
echo -e "${YELLOW}Testing image functionality...${NC}"
docker run --rm \
  -e MEALIE_BASE_URL=http://test:9000 \
  -e MEALIE_API_TOKEN=test-token \
  --entrypoint python \
  mealie-mcp:test \
  -c "
import sys
sys.path.append('/app/src')
try:
    from config import settings
    from main import mcp
    print('✓ All imports successful')
    print(f'✓ Server name: {settings.mcp_server_name}')
    print('✓ MCP server initialized')
    print('✅ Docker image test PASSED')
except Exception as e:
    print(f'❌ Test failed: {e}')
    sys.exit(1)
"

# Check image size
echo -e "${YELLOW}Image information:${NC}"
docker images mealie-mcp:test --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Security scan (if trivy is available)
if command -v trivy &> /dev/null; then
    echo -e "${YELLOW}Running security scan...${NC}"
    trivy image --severity HIGH,CRITICAL mealie-mcp:test
else
    echo -e "${YELLOW}Trivy not installed, skipping security scan${NC}"
fi

echo -e "${GREEN}✅ Docker test completed successfully${NC}"