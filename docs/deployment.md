# 🚀 Deployment Guide

This guide details how to deploy **PRobot** to cloud platforms and virtual private servers (VPS).

---

## 1. Deploying to Render

Render offers easy deployment for containerized apps and web services.

### Step 1: PostgreSQL & Redis Databases
1. Create a **Render PostgreSQL** database instance. Save the external connection URL.
2. Create a **Render Redis** instance. Save the connection URL.

### Step 2: Deploy Backend Web Service
1. Create a new **Web Service** on Render connected to your PRobot Git repository.
2. Configure settings:
   - **Environment**: `Docker`
   - **Docker Path**: `backend/Dockerfile`
   - **Start Command**: (Vite and Dockerfile set this automatically to run Uvicorn)
3. Add environment variables:
   - `POSTGRES_URL`: Set to your Render PostgreSQL connection URL.
   - `REDIS_URL`: Set to your Render Redis connection URL.
   - `GITHUB_TOKEN`: Your GitHub PAT.
   - `GITHUB_WEBHOOK_SECRET`: Secure HMAC string.
   - `GROQ_API_KEY`: Groq API Key.

### Step 3: Deploy Celery Background Worker
1. Create a new **Background Worker** service on Render.
2. Set the environment to `Docker` pointing to `backend/Dockerfile`.
3. Set the custom Start Command:
   ```bash
   celery -A app.core.celery_app.celery_app worker --loglevel=info
   ```
4. Copy the same environment variables from the web service.

---

## 2. Deploying to Koyeb

Koyeb is a high-performance developer platform for serverless deployments.

1. Create a new App on Koyeb.
2. Link your GitHub repository.
3. Configure the **Web Service**:
   - **Builder**: `Docker`
   - **Docker directory**: `backend`
   - Set ports and expose `8000`.
4. Configure the **Worker Service**:
   - Link the same repository.
   - Set builder to `Docker` and directory to `backend`.
   - Set build args or start command overrides to launch the Celery task queue:
     `celery -A app.core.celery_app.celery_app worker --loglevel=info`
5. Configure environment variables in Koyeb settings for both services.

---

## 3. Deploying to a Docker VPS

Deploying directly to a virtual private server (e.g. DigitalOcean, Linode, AWS EC2).

1. Clone the repository on your VPS:
   ```bash
   git clone https://github.com/your-username/PRobot.git
   cd PRobot/backend
   ```
2. Create your production `.env` file containing genuine credentials.
3. Run docker compose in detached mode:
   ```bash
   docker compose -f docker-compose.yml up -d --build
   ```
4. Set up an Nginx reverse proxy to forward traffic from port `80` / `443` (SSL) to local port `8000`.
5. Point your GitHub Webhook URL to `https://your-vps-ip/api/v1/webhooks/github`.
