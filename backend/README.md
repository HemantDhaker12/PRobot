# ⚙️ PRobot Backend Architecture & Developer Guide

This directory houses the Python FastAPI server, Redis broker, database adapters, integrations, and Celery asynchronous workers.

---

## 1. Backend Overview
PRobot's backend is built to process GitHub webhook events, perform heavy AI operations (LLM analysis, vector queries, RAG context construction), and update GitHub resources in real-time. 

To prevent network timeouts (GitHub webhook delivery expects a response in <10 seconds), the backend adopts an asynchronous, event-driven architecture using **FastAPI** as the intake listener, **Redis** as the task broker, and **Celery** as the worker queue executor.

---

## 2. System Architecture

```
GitHub Webhook
     │ (Signed POST Request)
     ▼
[ FastAPI (Uvicorn / Port 8000) ]
     │
     ├── 1. Signature check (HMAC-SHA256)
     ├── 2. Persist payload (PostgreSQL)
     ├── 3. Enqueue Celery Task (Redis)
     ▼
[ Redis Broker (Port 6379) ]
     │
     ▼ (Pushed Tasks)
[ Celery Workers ]
     │
     ├── Triage Engine (Groq Llama 3.3)
     ├── Duplicate Detector (ChromaDB + FastEmbed)
     ├── PR quality evaluator
     ├── RAG Knowledge assistant
     ▼
GitHub REST API Update (Comment / Label / Close)
```

---

## 3. Core Technologies

### 1. FastAPI Web Server
Located under `app/main.py` and `app/api/`. Provides standard API endpoints, global routers, CORS headers, startup validation diagnostics, and logging request middleware.

### 2. PostgreSQL Models (`app/models/`)
The database schema utilizes UUID keys and consists of:
- **`Repository`**: Stores repository configurations, settings, and scopes.
- **`WebhookEvent`**: Audits incoming payloads (`issues`, `pull_request`, `issue_comment`) and their delivery logs.
- **`Issue`**: Stores local mirrors of issue titles, numbers, and states.
- **`PullRequest`**: Local PR database mirrors.
- **`IssueComment`**: Stores GitHub comments.
- **`EmbeddingRecord`**: Holds vectors metadata chunks and references for RAG content.

### 3. Redis & Celery Queue
- **Celery Broker**: Buffered by Redis (`redis://redis:6379/0`).
- **Coordinator Worker**: Processes incoming events asynchronously, routing the payloads to the 5 active MVP engines.

### 4. Vector Search & Embedding
- **ChromaDB**: Placed under `/chroma_db` or an isolated container path.
- **FastEmbed**: Uses the `BAAI/bge-small-en-v1.5` model to generate 384-dimension embeddings locally on CPU.

### 5. AI Inference
- **Groq Llama 3.3 SDK**: Resolves schema questions, reads pull requests, triages issues contextually, and outputs structured JSON responses.

---

## 4. Database Schema Documentation

### `repositories` Table
- `id`: `UUID` (Primary Key, default: `gen_random_uuid()`)
- `full_name`: `VARCHAR(255)` (Unique, e.g. `owner/repo`)
- `github_id`: `BIGINT` (Unique)
- `settings`: `JSONB` (Repository configuration flags)
- `created_at` / `updated_at`: `TIMESTAMP WITH TIME ZONE`

### `webhook_events` Table
- `id`: `UUID` (Primary Key)
- `delivery_id`: `VARCHAR(100)` (Unique delivery UUID from GitHub header)
- `event_type`: `VARCHAR(50)` (e.g. `issues`, `pull_request`)
- `payload`: `JSONB` (Raw payload JSON)
- `status`: `VARCHAR(50)` (e.g., `pending`, `processed`, `failed`)
- `error_message`: `TEXT`

### `issues` Table
- `id`: `UUID` (Primary Key)
- `repository_id`: `UUID` (Foreign Key referencing `repositories.id`)
- `number`: `INTEGER` (GitHub issue number)
- `title`: `VARCHAR(255)`
- `state`: `VARCHAR(50)`

### `pull_requests` Table
- `id`: `UUID` (Primary Key)
- `repository_id`: `UUID` (Foreign key referencing `repositories.id`)
- `number`: `INTEGER`
- `title`: `VARCHAR(255)`
- `state`: `VARCHAR(50)`

---

## 5. API Endpoints Documentation

### `GET /api/v1/health`
- **Description**: Performs active connection checks on PostgreSQL and Redis.
- **Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "database": "healthy",
    "redis": "healthy"
  }
  ```
- **Response (503 Service Unavailable)**: Returned if any backend service is offline, with details on the offline database.

### `POST /api/v1/webhooks/github`
- **Description**: Webhook ingestion route. Checks the `X-Hub-Signature-256` header using the configured webhook secret.
- **Headers Required**:
  - `X-Hub-Signature-256`: `sha256=<hmac-hash>`
  - `X-GitHub-Delivery`: `<delivery-uuid>`
  - `X-GitHub-Event`: `<event-type>`
- **Response (202 Accepted)**: Webhook successfully queued in background Celery loop.

---

## 6. Setup and Installation

### Environment Variables
Place the following variables inside `backend/.env`:
- `POSTGRES_URL`: PostgreSQL connection string (defaults to `postgresql://postgres:postgres@localhost:5432/probot`).
- `REDIS_URL`: Redis server path (defaults to `redis://localhost:6379/0`).
- `CHROMA_PATH`: ChromaDB store path.
- `GITHUB_TOKEN`: GitHub Personal Access Token (PAT).
- `GITHUB_WEBHOOK_SECRET`: Secure HMAC webhook string.
- `GROQ_API_KEY`: Groq API Token (starts with `gsk_`).

### Manual Build Instructions
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run database migrations:
   ```bash
   alembic upgrade head
   ```
3. Boot the API server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. Boot the Celery worker:
   ```bash
   celery -A app.core.celery_app.celery_app worker --loglevel=info
   ```

---

## 7. Troubleshooting Guide

### 1. Webhook Signature Failures (`401 Unauthorized`)
- **Symptoms**: Logs show `hmac.compare_digest returned False`.
- **Solution**: Check that the webhook secret matches the value entered in GitHub Settings under Webhook Secret. Ensure `GITHUB_WEBHOOK_SECRET` contains no training spaces.

### 2. Celery Worker crashes with NameError / ModuleNotFound
- **Symptoms**: Tasks fail immediately with import exceptions.
- **Solution**: Ensure your PYTHONPATH is configured correctly. Run celery using the absolute module path: `celery -A app.core.celery_app.celery_app worker`.

### 3. Database is locked / Alembic fails
- **Symptoms**: Migrations hang or throw transaction exceptions.
- **Solution**: Ensure that your postgres instance is healthy and accepts connections. You can run database checks using the health endpoint: `curl http://localhost:8000/api/v1/health`.
