# Support Guide

If you need help or have questions about using **PRobot**, please refer to this guide to find the best channel for your needs.

---

## 1. Where to Get Help

### GitHub Discussions
For general questions, design feedback, architecture ideas, or custom integrations:
- Join the conversation on **GitHub Discussions** under the Q&A tab.
- This is the best place to talk to other maintainers and contributors.

### GitHub Issues
For reporting bugs or requesting enhancements:
- Search existing issues to verify it hasn't been discussed.
- Open a ticket using our templates. *Remember that PRobot's AI will assist with initial issue triage.*

---

## 2. FAQ (Frequently Asked Questions)

### Q: Which AI models does PRobot support?
PRobot is configured with the **Groq SDK** to run `llama-3.3-70b-versatile` by default. It can be adjusted in `config.py` to point to OpenAI, Anthropic, or local Ollama instances.

### Q: Does duplicate detection store my issue text off-site?
No. All embedding generation (`FastEmbed`) is executed locally inside your Python runtime, and vector records are saved in your local **ChromaDB** container namespace.

### Q: Why am I receiving Webhook Signature Verification errors?
Verify that your webhook secret in the local `.env` matches the secret key entered in your GitHub Repository settings exactly. If they match, ensure there are no trailing spaces or newline characters in your environment file.
