#!/bin/bash
# =========================================================================
# AskChat Startup Guide
# =========================================================================
# This script explains and assists with starting AskChat.
#
# TWO PATHS:
#   PATH 1: Docker Compose (full stack, requires Docker Desktop)
#   PATH 2: CloudFormation → Floci (AWS emulator, Docker + AWS CLI)
#   PATH 3: Native Python (no Docker at all)
#
# PREREQUISITES CHECK:
#   PATH 1 & 2 require: Docker Desktop (or Docker Engine on Linux)
#   PATH 3 requires: Python 3.11+, PostgreSQL
# =========================================================================

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              AskChat Startup Guide                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# -------------------------------------------------------------------------
# Prerequisites Check
# -------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " CHECKING PREREQUISITES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Docker
if command -v docker &> /dev/null; then
    echo " ✓ Docker found: $(docker --version)"
    if docker info &> /dev/null; then
        echo " ✓ Docker Engine is running"
        DOCKER_AVAILABLE=true
    else
        echo " ✗ Docker Engine is NOT running. Start Docker Desktop first."
        DOCKER_AVAILABLE=false
    fi
else
    echo " ✗ Docker not found. Install from: https://www.docker.com/products/docker-desktop/"
    DOCKER_AVAILABLE=false
fi

# Check Python
if command -v python3 &> /dev/null; then
    echo " ✓ Python found: $(python3 --version)"
    PYTHON_AVAILABLE=true
else
    echo " ✗ Python 3 not found"
    PYTHON_AVAILABLE=false
fi

# Check AWS CLI (for CloudFormation path)
if command -v aws &> /dev/null; then
    echo " ✓ AWS CLI found: $(aws --version 2>&1 | head -1)"
    AWS_CLI_AVAILABLE=true
else
    AWS_CLI_AVAILABLE=false
fi

echo ""

# -------------------------------------------------------------------------
# PATH 1: Docker Compose (Recommended - Full Stack)
# -------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " PATH 1: DOCKER COMPOSE (Full Stack - Recommended)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo " Starts: PostgreSQL + Ollama (local LLM) + AskChat"
echo " Requires: Docker Desktop running"
echo ""

if [ "$DOCKER_AVAILABLE" = true ]; then
    echo " To start:"
    echo "   cd ask_chat"
    echo "   docker compose up -d"
    echo ""
    echo " To pull a local LLM model (after startup):"
    echo "   docker exec askchat-ollama ollama pull phi3:mini"
    echo ""
    echo " To check health:"
    echo "   curl http://localhost:8000/health"
    echo ""
    echo " To view logs:"
    echo "   docker compose logs -f app"
    echo ""
    echo " To stop:"
    echo "   docker compose down"
else
    echo " ⚠ Docker not available. Use PATH 3 instead."
fi

echo ""

# -------------------------------------------------------------------------
# PATH 2: CloudFormation → Floci (AWS Emulator)
# -------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " PATH 2: CLOUDFORMATION + FLOCI (AWS Emulator)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo " Deploys: S3, RDS, Lambda, API Gateway, IAM, Secrets Manager"
echo " Requires: Docker Desktop + AWS CLI"
echo ""

if [ "$DOCKER_AVAILABLE" = true ] && [ "$AWS_CLI_AVAILABLE" = true ]; then
    echo " Step 1 - Start Floci:"
    echo "   docker run -d --name floci -p 4566:4566 \\"
    echo "     -e SERVICES=s3,lambda,apigateway,stepfunctions,iam,sts,\\"
    echo "              secretsmanager,rds,logs,bedrock \\"
    echo "     -e DEFAULT_REGION=us-east-1 \\"
    echo "     floci/floci:latest"
    echo ""
    echo " Step 2 - Deploy CloudFormation:"
    echo "   aws cloudformation deploy \\"
    echo "     --template-file cloudformation/askchat-main.yaml \\"
    echo "     --stack-name askchat-stack \\"
    echo "     --parameter-overrides UseFloci=true \\"
    echo "     --endpoint-url http://localhost:4566 \\"
    echo "     --region us-east-1"
    echo ""
    echo " Step 3 - Verify stack:"
    echo "   aws cloudformation describe-stacks \\"
    echo "     --stack-name askchat-stack \\"
    echo "     --endpoint-url http://localhost:4566"
else
    echo " ⚠ Docker ($DOCKER_AVAILABLE) and/or AWS CLI ($AWS_CLI_AVAILABLE) not available."
fi

echo ""

# -------------------------------------------------------------------------
# PATH 3: Native Python (No Docker)
# -------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " PATH 3: NATIVE PYTHON (Zero Docker Required)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo " Requires: Python 3.11+ installed, PostgreSQL running externally,"
echo "           optionally Ollama for local LLM"
echo ""

if [ "$PYTHON_AVAILABLE" = true ]; then
    echo " Step 1 - Create virtual environment:"
    echo "   cd ask_chat"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate   # Linux/Mac"
    echo "   venv\\Scripts\\activate     # Windows"
    echo ""
    echo " Step 2 - Install dependencies:"
    echo "   pip install -r requirements.txt"
    echo "   python -m spacy download en_core_web_sm"
    echo ""
    echo " Step 3 - Set up PostgreSQL (choose one):"
    echo "   Option A - Use existing PostgreSQL:"
    echo "     psql -U postgres -c \"CREATE DATABASE askchat;\""
    echo "     psql -d askchat -f sample_data/seed.sql"
    echo ""
    echo "   Option B - Start PostgreSQL via Docker (single container):"
    echo "     docker run -d --name askchat-pg -p 5432:5432 \\"
    echo "       -e POSTGRES_DB=askchat \\"
    echo "       -e POSTGRES_USER=askchat \\"
    echo "       -e POSTGRES_PASSWORD=askchat_secret_2024 \\"
    echo "       -v $(pwd)/sample_data/seed.sql:/docker-entrypoint-initdb.d/01-seed.sql \\"
    echo "       postgres:15-alpine"
    echo ""
    echo " Step 4 - (Optional) Start Ollama for local LLM:"
    echo "   docker run -d --name askchat-ollama -p 11434:11434 \\"
    echo "     ollama/ollama serve"
    echo "   docker exec askchat-ollama ollama pull phi3:mini"
    echo ""
    echo " Step 5 - Configure environment:"
    echo "   cp .env.example .env"
    echo "   # Edit .env if needed (DB_HOST, LLM_PROVIDER, etc.)"
    echo ""
    echo " Step 6 - Start the application:"
    echo "   uvicorn app.main:app --reload --port 8000"
    echo ""
    echo " Step 7 - Verify:"
    echo "   curl http://localhost:8000/health"
    echo "   curl http://localhost:8000/"
else
    echo " ⚠ Python not available."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " CHOOSE YOUR PATH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  PATH 1: Docker Compose"
echo "    ├── Starts everything automatically"
echo "    ├── Requires: Docker Desktop running"
echo "    └── Best for: Quick start, full local stack"
echo ""
echo "  PATH 2: CloudFormation + Floci"
echo "    ├── Simulates real AWS deployment"
echo "    ├── Requires: Docker Desktop + AWS CLI"
echo "    └── Best for: Validating infrastructure code"
echo ""
echo "  PATH 3: Native Python"
echo "    ├── No Docker required (except for DB/LLM)"
echo "    ├── Requires: Python 3.11+ manually installed"
echo "    └── Best for: Development, debugging, CI/CD"
echo ""

# -------------------------------------------------------------------------
# QUICK SUMMARY
# -------------------------------------------------------------------------
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " QUICK START (Docker Compose - 3 commands)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   cd ask_chat"
    echo "   docker compose up -d"
    echo "   curl http://localhost:8000/health"
    echo ""
fi