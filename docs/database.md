# 🗄️ Database Schema & Data Models Guide

This document describes the PostgreSQL database schemas, indexes, relationships, and metadata caches used by **PRobot**.

---

## 1. Database Schema Diagram

```
  ┌─────────────────┐             ┌─────────────────┐
  │  repositories   │             │ webhook_events  │
  ├─────────────────┤             ├─────────────────┤
  │ id (PK)         │             │ id (PK)         │
  │ full_name (UQ)  │             │ delivery_id (UQ)│
  │ github_id       │             │ event_type      │
  │ settings        │             │ payload         │
  └────────┬────────┘             │ status          │
           │                      │ error_message   │
           │ 1                    └─────────────────┘
           │
           ├──────────────────────────────┐
           │ Many                         │ Many
           ▼                              ▼
  ┌─────────────────┐            ┌─────────────────┐
  │     issues      │            │  pull_requests  │
  ├─────────────────┤            ├─────────────────┤
  │ id (PK)         │            │ id (PK)         │
  │ repository_idFK │            │ repository_idFK │
  │ number          │            │ number          │
  │ title           │            │ title           │
  │ state           │            │ state           │
  └────────┬────────┘            └─────────────────┘
           │ 1
           │
           │ Many
           ▼
  ┌─────────────────┐
  │ issue_comments  │
  ├─────────────────┤
  │ id (PK)         │
  │ issue_id (FK)   │
  │ github_id       │
  │ body            │
  └─────────────────┘
```

---

## 2. PostgreSQL Relational Models

### 1. `Repository` Model
Stores settings for each monitored repository (e.g. toggle switches for RAG checks, duplicate checks, and checklist templates).
- **Columns**:
  - `id`: `UUID` (Primary Key)
  - `full_name`: `String(255)` (Unique index, e.g., `HeavenHill/PRobot`)
  - `github_id`: `BigInteger` (GitHub repository ID)
  - `settings`: `JSONB` (Stores flags like `enable_duplicate_detection: true`)

### 2. `WebhookEvent` Model
Audits raw incoming payload payloads, event types, and processing statuses.
- **Columns**:
  - `id`: `UUID` (Primary Key)
  - `delivery_id`: `String(100)` (Unique index, matches `X-GitHub-Delivery`)
  - `event_type`: `String(50)` (e.g., `issues`, `pull_request`, `issue_comment`)
  - `payload`: `JSONB` (Raw webhook payload JSON)
  - `status`: `String` (Options: `pending`, `processed`, `failed`)
  - `error_message`: `Text` (Saved if processing throws an exception)

### 3. `Issue` & `PullRequest` Models
Local database caches representing GitHub issues and pull request statuses.
- **Columns**:
  - `id`: `UUID` (Primary Key)
  - `repository_id`: `UUID` (Foreign key referencing `repositories.id`)
  - `number`: `Integer` (GitHub ID number)
  - `title`: `String(255)`
  - `state`: `String(50)` (e.g., `open`, `closed`)

---

## 3. ChromaDB Vector Metadata Schema
Duplicate check embeddings and RAG document partitions are indexed in **ChromaDB**. 

To isolate repositories and speed up vector searches, we index embeddings under the following schema:
- **Embedding**: 384-dimensional vector (`BAAI/bge-small-en-v1.5`).
- **Metadata**:
  - `repository_uuid`: Identifies the parent repository.
  - `type`: Either `issue_body` or `doc_chunk`.
  - `github_number`: The issue number.
  - `chunk_index`: The chunk index for markdown page slices.
