# 🏗️ Detailed System Architecture

This document outlines the detailed system architecture, concurrency pipelines, and data flow of **PRobot**.

---

## 1. System Overview

PRobot is designed with a high-throughput, event-driven architecture that ensures webhooks are answered within milliseconds while heavy LLM logic, vector calculations, and GitHub API interactions execute in isolated background tasks.

```
       [ GitHub Event ]
               │
               ▼ (Secure signed POST)
     [ FastAPI Web Server ]
               │
               ├── 1. Verify HMAC Signature
               ├── 2. Save WebhookEvent (PostgreSQL)
               ├── 3. Enqueue Tasks via Redis Broker
               ▼
     [ HTTP 202 Accepted ] (Returned in <10ms)
               │
      (Asynchronous Dispatch)
               ▼
       [ Redis Broker ]
               │
               ▼ (Task fetched by worker)
       [ Celery Workers ]
               │
       ┌───────┼──────────────────────────────┐
       ▼       ▼                              ▼
    [RAG]   [LLM Triage]             [Duplicate Checks]
  ChromaDB  Groq Llama             FastEmbed + Vector Store
       │       │                              │
       └───────┼──────────────────────────────┘
               ▼
     [ GitHub REST Update ]
```

---

## 2. Component Explanations

### Webhook Intake & Verification
- **Entrypoint**: `app/api/endpoints/webhooks.py`.
- **HMAC Check**: Incoming payloads are encrypted with a secret. The FastAPI route recalculates the HMAC-SHA256 signature using `GITHUB_WEBHOOK_SECRET` and matches it using timing-attack-safe `hmac.compare_digest`.
- **Task Offloading**: Immediately upon validation, the payload is inserted as a record in PostgreSQL with status `pending`. The task is enqueued using `process_webhook_event.delay(event_id)`. FastAPI then immediately returns `HTTP 202 Accepted` to GitHub.

### Task Queue Isolation
- **Queue Broker**: Managed by **Redis** (running on port `6379`).
- **Worker Execution**: Celery workers run concurrently in separate thread pools. They fetch the event ID, retrieve the payload from PostgreSQL, and execute the event router.

### Background AI Processors
1. **Intelligent Triage**: Instructs Llama-3.3 on Groq to audit the issue text, outputting a structured JSON checklist of missing information (like versions, OS, commands, or tracebacks).
2. **Auto Labeling**: Classifies text using Groq's high-speed LLM context parsing and updates label nodes.
3. **Duplicate Detection**: Computes embeddings using FastEmbed and updates the ChromaDB vector database. Checks the cosine distance threshold; if it exceeds `0.90`, it flags a duplicate.
4. **Knowledge Assistant**: Extracts RAG contextual markdown guidelines to comment helpful guidance.
5. **PR Quality Guardian**: Inspects PR descriptions and compares file diff metrics.

---

## 3. Concurrency & Performance Design
- **Sub-10ms Webhook Reply**: By avoiding synchronous LLM connections or DB calls during the HTTP request cycle, we eliminate webhook timeouts.
- **Worker Scalability**: The Celery worker daemon can scale horizontally to handle high event concurrency, preventing bottlenecking on heavy AI workloads.
