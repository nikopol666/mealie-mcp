#!/bin/bash
set -e

echo "🚀 Setting up CI/CD for Mealie MCP Server"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository. Please run 'git init' first.${NC}"
    exit 1
fi

# Check if .github directory exists
if [ ! -d ".github" ]; then
    echo -e "${RED}❌ .github directory not found. Are you in the project root?${NC}"
    exit 1
fi

echo -e "${YELLOW}Validating workflow files...${NC}"

# Validate YAML files
for file in .github/workflows/*.yml .github/*.yml; do
    if [ -f "$file" ]; then
        echo "  Checking $file..."
        if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
            echo -e "    ✅ Valid YAML"
        else
            echo -e "    ❌ Invalid YAML"
            exit 1
        fi
    fi
done

echo -e "${YELLOW}Checking required secrets...${NC}"

cat << 'EOF'
📋 Required GitHub settings:

Repository Settings > Secrets and Variables > Actions

This repository publishes to GitHub Container Registry (GHCR) with
GITHUB_TOKEN. No Docker Hub secret is required.

Required repository setting:

1. Actions > General > Workflow permissions:
   - Read and write permissions

EOF

echo -e "${YELLOW}Testing Docker setup...${NC}"

# Test Docker build if Docker is available
if command -v docker &> /dev/null; then
    echo "  Testing Docker build..."
    if docker build -t mealie-mcp:setup-test . > /dev/null 2>&1; then
        echo -e "  ✅ Docker build successful"
        docker rmi mealie-mcp:setup-test > /dev/null 2>&1 || true
    else
        echo -e "  ❌ Docker build failed"
        echo -e "  ${RED}Please fix Docker issues before pushing${NC}"
    fi
else
    echo -e "  ⚠️  Docker not available, skipping build test"
fi

echo -e "${YELLOW}Checking Python environment...${NC}"

# Check if requirements can be installed
if command -v python3 &> /dev/null; then
    if python3 -c "
import sys
try:
    import fastapi, uvicorn, mcp, httpx, pydantic
    print('  ✅ All dependencies available')
except ImportError as e:
    print(f'  ⚠️  Missing dependency: {e}')
    print('  Run: pip install -r requirements.txt')
"; then
        echo -e "  Dependencies check completed"
    fi
else
    echo -e "  ⚠️  Python3 not available"
fi

echo -e "${YELLOW}Repository configuration recommendations:${NC}"

cat << 'EOF'
📋 Recommended GitHub Repository Settings:

1. Branch Protection Rules (Settings > Branches):
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Require pull request reviews before merging

2. Actions Settings (Settings > Actions > General):
   - Allow all actions and reusable workflows
   - Workflow permissions: Read and write permissions

3. Security Settings (Settings > Security):
   - Enable Dependabot alerts
   - Enable Dependabot security updates
   - Enable secret scanning

4. Notifications (Watch button):
   - Watch for releases and security alerts

EOF

echo -e "${GREEN}✅ CI/CD setup validation complete!${NC}"
echo -e "${GREEN}🎉 Ready to push and trigger workflows!${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "1. Confirm GitHub Actions has read/write package permissions"
echo -e "2. Push to main branch or create a PR"
echo -e "3. Monitor the Actions tab for workflow execution"
echo -e "4. Tag a release (e.g., git tag v1.0.0 && git push --tags)"
