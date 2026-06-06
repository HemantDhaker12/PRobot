# 🐙 GitHub Webhook Lifecycle & Security Guide

This document explains how webhooks are validated, recorded, queued, and executed.

---

## 1. Webhook Lifecycle Flowchart

```
┌──────────────┐      POST Event (with X-Hub-Signature-256)
│  GitHub API  ├─────────────────────────────────────────────┐
└──────────────┘                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │ HMAC Validation │
                                                    └────────┬────────┘
                                                             │
                                                   ┌─────────▼─────────┐
                                            No     │  Signature Valid? │
                                        ┌──────────┤   (Timing-safe)   │
                                        │          └─────────┬─────────┘
                                        ▼                    │ Yes
                                ┌───────────────┐   ┌────────▼────────┐
                                │ HTTP 401 Auth │   │  Insert Event   │
                                └───────────────┘   │  to PostgreSQL  │
                                                    └────────┬────────┘
                                                             │
                                                    ┌────────▼────────┐
                                                    │ Enqueue Worker  │
                                                    │ Task via Redis  │
                                                    └────────┬────────┘
                                                             │
                                                    ┌────────▼────────┐
                                                    │ HTTP 202 Reply  │
                                                    └─────────────────┘
```

---

## 2. Step-by-Step Lifecycle Details

### 1. Ingestion and Signature Hashing
When GitHub sends a webhook POST request:
1. The FastAPI router retrieves the signature header: `X-Hub-Signature-256`.
2. The router extracts the raw request payload bytes.
3. It computes the SHA256 HMAC of the payload bytes using the configured `GITHUB_WEBHOOK_SECRET` key.
4. It parses the signature string out of the header (stripping the `sha256=` prefix).
5. It performs a timing-attack-safe comparison between the computed hash and the header signature using `hmac.compare_digest`. If they do not match, it returns an immediate `HTTP 401 Unauthorized`.

### 2. Event Persistence (PostgreSQL)
To ensure we have audit records and recoverability for all webhook events:
- A new `WebhookEvent` record is written to PostgreSQL containing the unique `X-GitHub-Delivery` ID, the event type, the raw payload JSON, and is set to `status = "pending"`.

### 3. Task Offloading (Redis)
To bypass network latency:
- FastAPI triggers a background Celery task using `process_webhook_event.delay(event.id)`.
- Redis buffers the task parameters immediately.
- FastAPI returns `HTTP 202 Accepted` to GitHub in under 10ms.

### 4. Background Processing (Celery Worker)
1. The Celery worker daemon pulls the task ID.
2. It fetches the `WebhookEvent` payload from PostgreSQL.
3. The event router checks the event type and executes the corresponding AI engines (smart triage, labeling, duplicate check, RAG search).
4. The worker calls the GitHub REST API to comment or close tickets.
5. The `WebhookEvent` status is updated to `processed` (or `failed` with the traceback text saved to the table if an exception occurs).
