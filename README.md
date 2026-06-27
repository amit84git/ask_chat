# AskChat - AI-Powered Natural Language to SQL Platform

AskChat converts plain English questions into executable PostgreSQL queries using a modular, cost-free architecture. It runs entirely locally using **Ollama with open-source models** (Llama 3.1, Mistral, Phi-3), with optional AWS Bedrock integration when needed.

---

## Clean Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                        USER / API CLIENT                            │
│                                                                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (FastAPI + Uvicorn)                    │
│                                                                      │
│  /health  /query/nl2sql  /metadata/load  /graph/visualize            │
│  /rules/apply  /graph/schema  /schema/tables                         │
└──────┬─────────────┬──────────────┬──────────────────────┬───────────┘
       │             │              │                      │
       ▼             ▼              ▼                      ▼
┌───────────┐ ┌───────────┐ ┌──────────────┐ ┌──────────────────────┐
│  QUERY    │ │ SEMANTIC  │ │  RULES       │ │   VISUALIZATION      │
│  LAYER    │ │ LAYER     │ │  ENGINE      │ │   LAYER              │
│           │ │           │ │              │ │                      │
│ /query/   ││ /metadata/ ││ /rules/apply ││ /graph/visualize     │
│ nl2sql    ││ load       ││              ││                      │
└─────┬─────┘ └─────┬─────┘ └──────┬───────┘ └──────────┬───────────┘
      │             │              │                    │
      ▼             ▼              ▼                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        LLM PROVIDER SELECTOR                         │
│                                                                      │
│  ┌──────────────────┐   ┌──────────────────┐   ┌─────────────────┐  │
│  │   LOCAL LLM      │   │   AWS BEDROCK    │   │    NONE         │  │
│  │   (Ollama)       │   │   (Claude/Titan) │   │  (Heuristic     │  │
│  │   llama3.1:8b    │   │                  │   │   Only)         │  │
│  │   mistral        │   │   Cost: $0.01-   │   │                 │  │
│  │   phi3:mini      │   │   0.08/1K tok    │   │  100% offline   │  │
│  │                  │   │                  │   │                 │  │
│  │   100% Free!     │   │   Internet req.  │   │  Lightest       │  │
│  └──────────────────┘   └──────────────────┘   └─────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
             │                    │                    │
             ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         FUZZY MATCHER                                │
│                                                                      │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  spaCy   │  │ RapidFuzz │  │ FlashText │  │  Regex Patterns  │   │
│  │ (NLP)    │  │ (Similar) │  │ (Keyword) │  │  (Fallback)      │   │
│  └──────────┘  └───────────┘  └──────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     SEMANTIC GRAPH (NetworkX)                        │
│                                                                      │
│   tables ──contains──▶ columns ──references──▶ other columns        │
│   keywords ──maps_to──▶ tables/columns                               │
│   Domain knowledge graph for intelligent schema understanding        │
└──────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  QUERY GENERATION PIPELINE                           │
│                                                                      │
│  ┌────────────┐   ┌────────────────┐   ┌───────────────────────┐    │
│  │  1. Extract │   │  2. Generate    │   │  3. Apply Business   │    │
│  │  Keywords & │──▶│  SQL via LLM   │──▶│  Rules (Filters,     │    │
│  │  Candidates │   │  or Heuristics  │   │  Ordering, Limits)   │    │
│  └────────────┘   └────────────────┘   └───────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                                 │
│                                                                      │
│        SQLAlchemy ──▶ PostgreSQL (local or RDS via Floci)            │
│        Schema introspection, parameterized queries, result sets      │
└──────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     OUTPUT / VISUALIZATION                           │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐    │
│  │  Pyvis Graph     │  │  Altair Charts   │  │  Matplotlib     │    │
│  │  (HTML, inter-   │  │  (Vega-Lite,     │  │  (Static SVG    │    │
│  │   active nodes)  │  │   interactive)   │  │   fallback)     │    │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘

                       AWS INFRASTRUCTURE (Optional)
┌──────────────────────────────────────────────────────────────────────┐
│  CloudFormation ──▶ Floci (local) or Real AWS                       │
│  S3 │ Lambda │ API Gateway │ IAM │ Secrets Manager │ CloudWatch     │
└──────────────────────────────────────────────────────────────────────┘
```

## Key Components

| Layer               | Technology                      | Purpose                                  |
| ------------------- | ------------------------------- | ---------------------------------------- |
| **API Gateway**     | FastAPI + Uvicorn               | REST endpoints with Pydantic validation  |
| **LLM Selector**    | Ollama / Bedrock / None         | Auto-detects best available LLM provider |
| **Fuzzy Matcher**   | spaCy + RapidFuzz + FlashText   | Maps user terms to schema objects        |
| **Semantic Graph**  | NetworkX + Pyvis                | Graph-based schema understanding         |
| **Query Generator** | Local LLM + Heuristic Fallback  | Dual-path SQL generation                 |
| **Rules Engine**    | Custom rule DSL                 | Business logic enforcement               |
| **Database**        | SQLAlchemy + PostgreSQL         | Data storage and query execution         |
| **Visualization**   | Pyvis / Altair / Matplotlib     | Interactive HTML outputs                 |
| **Infrastructure**  | CloudFormation + Floci + Docker | Deployable to local emulator or real AWS |

## Repository Structure

```
ask_chat/
├── app/                          # Application code
│   ├── main.py                   # FastAPI entry point (8 endpoints)
│   ├── config.py                 # Pydantic Settings (env-based)
│   ├── aws_utils.py              # Boto3 clients + S3/Secrets/Bedrock
│   ├── database.py               # SQLAlchemy DB manager
│   ├── local_llm.py              # Ollama local LLM provider (NEW)
│   ├── semantic_graph.py         # NetworkX graph + Pyvis HTML
│   ├── fuzzy_matcher.py          # spaCy + RapidFuzz + FlashText
│   ├── rules_engine.py           # 6 default business rules
│   ├── query_generator.py        # LLM + Heuristic SQL generation
│   ├── visualization.py          # Altair/Matplotlib/Pyvis
│   ├── metadata.py               # JSON/Excel/RDS ingestion
│   └── models/
│       └── schemas.py            # 13 Pydantic models
├── cloudformation/
│   └── askchat-main.yaml         # Full AWS CloudFormation stack
├── scripts/
│   └── generate_excel.py         # Sample Excel metadata generator
├── sample_data/
│   ├── schema.json               # 4 tables, 20 domain keywords
│   ├── seed.sql                  # 50 customers, 100 orders, 20 products
│   └── example_prompts.md        # 17 example Q&A pairs
├── tests/
│   ├── test_fuzzy_matcher.py     # 10 unit tests
│   ├── test_rules_engine.py      # 10 unit tests
│   ├── test_query_generator.py   # 9 unit tests
│   ├── test_semantic_graph.py    # 8 unit tests
│   └── test_integration.py       # 10 integration tests
├── docker-compose.yml            # PostgreSQL + Ollama + Floci + App
├── Dockerfile                    # Python 3.11 container
├── requirements.txt              # Python dependencies
├── .env.example                  # Configuration template
└── README.md                     # This file
```

---

## Startup Paths: Choose Your Setup

AskChat can run in **three different ways** depending on what software you have installed.

### Prerequisites Quick Check

| Software                   | PATH 1: Docker Compose | PATH 2: Floci CFN   | PATH 3: Native Python |
| -------------------------- | ---------------------- | ------------------- | --------------------- |
| **Docker Desktop** running | ✅ Required            | ✅ Required         | ❌ Not needed         |
| **Python 3.11+** installed | ❌ Not needed          | ❌ Not needed       | ✅ Required           |
| **PostgreSQL**             | ⚡ Auto-started        | ⚡ Via Floci        | 🔧 Must provide       |
| **LLM Model**              | ⚡ Auto via Ollama     | ⚡ Via Floci        | 🔧 Must start Ollama  |
| **AWS CLI**                | ❌ Not needed          | ✅ Required         | ❌ Not needed         |
| **Internet**               | Only for first pull    | Only for first pull | Only for first pull   |
| **Cost**                   | **$0**                 | **$0**              | **$0**                |

> ✅ = Already installed & running needed | ⚡ = Started automatically | 🔧 = You provide/start manually

---

### PATH 1: Docker Compose (Easiest — 3 Commands)

**What gets started:** PostgreSQL + Ollama (local LLM) + Floci (AWS emulator) + AskChat app  
**You need:** Docker Desktop **running** on your machine. That's it.

```bash
# Step 1 — Start everything
cd ask_chat
docker compose up -d

# Step 2 — Load a local LLM model (one-time, ~2 min download)
docker exec askchat-ollama ollama pull phi3:mini

# Step 3 — Test it
curl http://localhost:8000/health
```

Then load data and ask questions:

```bash
curl -X POST http://localhost:8000/metadata/load \
  -H "Content-Type: application/json" \
  -d '{"source_type": "json", "source_path": "sample_data/schema.json"}'

curl -X POST http://localhost:8000/query/nl2sql \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all customers", "max_results": 10}'
```

**To stop:** `docker compose down`

---

### PATH 2: CloudFormation + Floci (AWS Infrastructure Validation)

**What this does:** Deploys the CloudFormation stack (S3, RDS, Lambda, API Gateway, IAM) to Floci  
**You need:** Docker Desktop **running** + AWS CLI **installed**

```bash
# Step 1 — Start Floci emulator
docker run -d --name floci -p 4566:4566 \
  -e SERVICES=s3,lambda,apigateway,stepfunctions,iam,sts,secretsmanager,rds,logs,bedrock \
  -e DEFAULT_REGION=us-east-1 \
  floci/floci:latest

# Step 2 — Deploy CloudFormation to Floci
aws cloudformation deploy \
  --template-file cloudformation/askchat-main.yaml \
  --stack-name askchat-stack \
  --parameter-overrides UseFloci=true VpcId=vpc-123456 SubnetIds=subnet-123456,subnet-789012 \
  --endpoint-url http://localhost:4566 --region us-east-1

# Step 3 — Verify deployed resources
aws cloudformation describe-stacks \
  --stack-name askchat-stack \
  --endpoint-url http://localhost:4566

# Step 4 — Start AskChat app pointing to Floci
# (Run PATH 3 without starting PostgreSQL — use Floci's RDS instead)
```

---

### PATH 3: Native Python (Zero Docker Required)

**What this needs:** Python 3.11+ installed manually + a running PostgreSQL somewhere  
**You need:** Just Python. PostgreSQL can be local, remote, or in a single Docker container.

```bash
# Step 1 — Create Python environment
cd ask_chat
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Step 2 — Install packages
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Step 3 — Make sure PostgreSQL is available
# Option A: Connect to existing PostgreSQL
psql -U postgres -c "CREATE DATABASE askchat;"
psql -d askchat -f sample_data/seed.sql

# Option B: Start minimal PostgreSQL container (single command)
docker run -d --name askchat-pg -p 5432:5432 \
  -e POSTGRES_DB=askchat \
  -e POSTGRES_USER=askchat \
  -e POSTGRES_PASSWORD=askchat_secret_2024 \
  -v "%CD%/sample_data/seed.sql:/docker-entrypoint-initdb.d/01-seed.sql" \
  postgres:15-alpine

# Step 4 — (Optional) Start Ollama for local LLM
# Install from https://ollama.com or use Docker:
docker run -d --name askchat-ollama -p 11434:11434 ollama/ollama serve
docker exec askchat-ollama ollama pull phi3:mini

# Step 5 — Configure environment
cp .env.example .env
# Edit .env: set DB_HOST=localhost, LLM_PROVIDER=ollama

# Step 6 — Start AskChat
uvicorn app.main:app --reload --port 8000

# Step 7 — Verify
curl http://localhost:8000/health
```

---

### Summary: Which Path Should I Use?

| Your Situation             | Recommended Path                  | Commands                    |
| -------------------------- | --------------------------------- | --------------------------- |
| Docker Desktop is running  | **PATH 1** (Docker Compose)       | `docker compose up -d`      |
| Building CI/CD pipeline    | **PATH 1** (Docker Compose)       | Same as above               |
| Testing AWS infrastructure | **PATH 2** (Floci CFN)            | `aws cloudformation deploy` |
| No Docker, just Python     | **PATH 3** (Native)               | `uvicorn app.main:app`      |
| Want fastest startup       | **PATH 3** (Native)               | ~10 seconds                 |
| Don't care about LLM       | Any path, set `LLM_PROVIDER=none` | Heuristic-only mode         |

---

## Local LLM Options (Zero Cost)

Set `LLM_PROVIDER` in `.env` to choose your model:

| Provider   | Model                 | Size  | RAM | Quality      |
| ---------- | --------------------- | ----- | --- | ------------ |
| `phi`      | `phi3:mini` (default) | 2.2GB | 4GB | Good         |
| `llama`    | `llama3.1:8b`         | 4.7GB | 8GB | Very Good    |
| `mistral`  | `mistral`             | 4.1GB | 8GB | Very Good    |
| `gemma`    | `gemma2:2b`           | 1.6GB | 4GB | Fair         |
| `qwen`     | `qwen2.5:7b`          | 4.4GB | 8GB | Excellent    |
| `deepseek` | `deepseek-coder:6.7b` | 3.8GB | 8GB | Best for SQL |
| `none`     | Heuristic only        | 0GB   | 0GB | Basic        |

Pull a model with: `ollama pull <model-name>`

---

## API Reference

| Method | Endpoint           | Description                          |
| ------ | ------------------ | ------------------------------------ |
| `GET`  | `/`                | API overview with all endpoints      |
| `GET`  | `/health`          | Health check (DB, LLM, Graph status) |
| `POST` | `/query/nl2sql`    | Natural language → SQL → execute     |
| `POST` | `/metadata/load`   | Load schema from JSON/Excel/RDS      |
| `POST` | `/graph/visualize` | Interactive HTML schema graph        |
| `POST` | `/rules/apply`     | Apply business rules to SQL          |
| `GET`  | `/graph/schema`    | Schema graph as JSON                 |
| `GET`  | `/schema/tables`   | List database tables                 |

### Sample NL2SQL Request/Response

**Request:**

```json
POST /query/nl2sql
{
    "question": "How many customers are from New York?",
    "use_llm": true
}
```

**Response:**

```json
{
  "question": "How many customers are from New York?",
  "generated_sql": "SELECT COUNT(*) FROM customers WHERE city = 'New York'",
  "explanation": "Generated by AI (ollama)\nQuery: SELECT COUNT(*) FROM customers WHERE city = 'New York'",
  "results": [{ "count": 1 }],
  "row_count": 1,
  "execution_time_ms": 1420.5,
  "llm_used": true,
  "rules_applied": ["limit_safe_results"],
  "tables_used": ["customers"],
  "confidence_score": 0.95
}
```

---

## Deploying to Floci (Local AWS Emulator)

```bash
# 1. Start Floci with all required services
docker run -d --name floci -p 4566:4566 \
  -e SERVICES=s3,lambda,apigateway,stepfunctions,iam,sts,secretsmanager,rds,logs,bedrock \
  -e DEFAULT_REGION=us-east-1 \
  floci/floci:latest

# 2. Deploy CloudFormation
aws cloudformation deploy \
  --template-file cloudformation/askchat-main.yaml \
  --stack-name askchat-stack \
  --parameter-overrides UseFloci=true VpcId=vpc-123456 SubnetIds=subnet-123456,subnet-789012 \
  --endpoint-url http://localhost:4566 --region us-east-1

# 3. Run application with Floci endpoint
uvicorn app.main:app --reload --port 8000
```

## Switching Between Local / Floci / Real AWS

| Config                  | Local Only  | Floci                   | Real AWS            |
| ----------------------- | ----------- | ----------------------- | ------------------- |
| `AWS_ENDPOINT_URL`      | Comment out | `http://localhost:4566` | Comment out         |
| `LLM_PROVIDER`          | `ollama`    | `ollama`                | `claude` or `titan` |
| `AWS_ACCESS_KEY_ID`     | N/A         | `dummy`                 | Real key            |
| `AWS_SECRET_ACCESS_KEY` | N/A         | `dummy`                 | Real secret         |
| `FEATURE_BEDROCK`       | `false`     | `false`                 | `true`              |
| Cost                    | **$0**      | **$0**                  | Pay-as-you-go       |

---

## Running Tests

```bash
# Unit tests only (no dependencies required)
pytest tests/ -v -k "not integration"

# All tests including integration (requires API running)
pytest tests/ -v
```

## Cost Savings with Local Validation

Running on Floci + Ollama before deploying to real AWS saves:

| Area                  | Local Cost                     | AWS Cost                       |
| --------------------- | ------------------------------ | ------------------------------ |
| LLM Inference         | **$0** (Ollama, local CPU/GPU) | $0.01-0.08/1K tokens (Bedrock) |
| CloudFormation        | **$0** (Floci emulator)        | ~$0.90/stack/hour              |
| Database              | **$0** (local PostgreSQL)      | $15-50/month (RDS)             |
| S3 / Lambda / API GW  | **$0** (Floci emulator)        | Pay-per-request                |
| Development Iteration | **$0** (instant feedback)      | Minutes per deploy cycle       |

**Total monthly PoC cost: $0** vs $50-200+ on real AWS.

---

## Sample Questions

| #   | Question                        | SQL Pattern                                                                  |
| --- | ------------------------------- | ---------------------------------------------------------------------------- |
| 1   | "Show me all customers"         | `SELECT * FROM customers`                                                    |
| 2   | "How many orders are pending?"  | `SELECT COUNT(*) FROM orders WHERE status = 'pending'`                       |
| 3   | "Find customers from New York"  | `SELECT * FROM customers WHERE city = 'New York'`                            |
| 4   | "What is the total revenue?"    | `SELECT SUM(total_amount) FROM orders`                                       |
| 5   | "Show top 10 products by price" | `SELECT * FROM products ORDER BY price DESC LIMIT 10`                        |
| 6   | "List active customers"         | `SELECT * FROM customers WHERE status = 'active'`                            |
| 7   | "Orders from last 30 days"      | `SELECT * FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'` |
| 8   | "Unique product categories"     | `SELECT DISTINCT category FROM products`                                     |
| 9   | "Average order amount"          | `SELECT AVG(total_amount) FROM orders`                                       |
| 10  | "Orders with customer names"    | `SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.id`  |

See `sample_data/example_prompts.md` for 17 detailed examples.

---

## How to Run on Floci

```
1. docker-compose up -d               # Start all services
2. docker exec askchat-ollama ollama pull phi3:mini   # Load local model
3. curl localhost:8000/health         # Verify all services healthy
4. POST /metadata/load                # Load schema from JSON
5. POST /query/nl2sql                 # Ask natural language questions
6. POST /graph/visualize              # View interactive schema graph
7. POST /rules/apply                  # Test business rules
```

**License:** MIT - PoC project for demonstration purposes.
#   a s k _ c h a t  
 