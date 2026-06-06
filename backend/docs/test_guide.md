# 🧪 GitHub Integration & Webhook Testing Guide

This guide explains how to connect your local PRobot instance to a real GitHub repository for live end-to-end testing using `ngrok` and GitHub Webhooks.

---

## 🎛️ Step 1: Create an ngrok Tunnel

Since GitHub webhooks need to send HTTP POST requests to a publicly accessible URL, you need to expose your local FastAPI port (`8000`) to the internet.

1. **Install ngrok:**
   If you don't have ngrok installed, download it from [ngrok.com](https://ngrok.com/) or install it via package managers:
   * Windows (winget): `winget install ngrok.ngrok`
   * macOS (Homebrew): `brew install ngrok/ngrok/ngrok`

2. **Start the tunnel:**
   In a new terminal window, start a tunnel to port `8000`:
   ```bash
   ngrok http 8000
   ```

3. **Copy the HTTPS URL:**
   Locate the `Forwarding` URL in the ngrok terminal output. It should look like:
   `https://a1b2-34-56-78-90.ngrok-free.app`

---

## ⚙️ Step 2: Configure the GitHub Webhook

1. Navigate to your testing GitHub repository on [github.com](https://github.com).
2. Go to **Settings** -> **Webhooks** -> Click **Add webhook**.
3. Configure the following settings:
   * **Payload URL:** Paste your ngrok HTTPS URL and append `/webhooks/github` (e.g., `https://a1b2-34-56-78-90.ngrok-free.app/webhooks/github`).
   * **Content type:** Select `application/json`.
   * **Secret:** Enter a secure random string (e.g., `my_probot_webhook_secret_key`). Keep this string handy.
   * **Which events to trigger:** Select **Let me select individual events** and check:
     * `Issues`
     * `Issue comments`
     * `Pull requests`
   * **Active:** Keep this checked.
4. Click **Add webhook**.

---

## 🔐 Step 3: Configure Local Environment

Open your `.env` file in the `backend/` directory and configure the secrets:

```env
# GitHub Webhook Validation Secret (Must match the Secret entered in Step 2)
GITHUB_WEBHOOK_SECRET=my_probot_webhook_secret_key

# GitHub Personal Access Token (PAT) with 'repo' and 'write:discussion' permissions
GITHUB_TOKEN=ghp_yourActualGitHubTokenHere

# Groq API Key
GROQ_API_KEY=gsk_yourActualGroqApiKeyHere
```

---

## 🚀 Step 4: Run the Application

1. Make sure your services (PostgreSQL, Redis) and API/Worker containers are running:
   ```bash
   docker-compose up -d
   ```
2. Monitor application logs to see webhook logs in real-time:
   ```bash
   docker-compose logs -f web worker
   ```

---

## 🧪 Step 5: Test Autotasks

### Test 1: Intelligent Issue Triage & Auto Labeling
1. Go to your repository on GitHub and click **New Issue**.
2. Write a minimal bug description missing standard debugging parameters:
   * **Title:** `Login button is broken`
   * **Body:** `The login button doesn't respond when I click it. Please fix.`
3. **Observe the result:**
   * In a few seconds, PRobot will parse the issue via webhook.
   * The **Labeling Engine** will call Groq, classify the issue, and apply labels (like `bug` or `question`).
   * The **Triage Engine** will detect missing details (OS, Language version, reproduction steps) and post a structured comment asking the user for these details:
     ```text
     🤖 **PRobot Triage Assistant**
     Thanks for opening this issue! To help us reproduce...
     - [ ] Operating System (OS)
     - [ ] Clear steps to reproduce...
     ```

### Test 2: PR Quality Guardian
1. Create a branch and modify a source code file (e.g. `app/main.py`), but do **not** add or modify any test files.
2. Open a Pull Request. Provide a short description (less than 15 characters) like: `update main`.
3. **Observe the result:**
   * The **PR Guardian** task will run, check the PR description length, linked issues, and file modifications.
   * It will post a structured checklist table review as a comment:
     * **PR Description:** `❌ FAILED` (too short)
     * **Linked Issue:** `⚠️ WARNING` (none linked)
     * **Test Verification:** `❌ FAILED` (modified source but no test files modified)
