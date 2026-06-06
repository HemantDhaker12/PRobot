# 🤝 Contributing to PRobot

Thank you for your interest in contributing to **PRobot**! We welcome contributions from open-source developers, maintainers, and automation enthusiasts.

By contributing to this repository, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 1. Issue Reporting Guidelines
Before opening a new issue:
- Check existing issues to verify it hasn't been reported.
- Ensure you provide a clear description, environment details, reproduction steps, and error logs if applicable.
- Note that PRobot's AI triage assistant will scan open issues and automatically request missing logs, OS details, or tracebacks!

---

## 2. Feature Request Guidelines
We use GitHub issues to track feature requests. When requesting a new feature:
- Clearly describe the use case and why it benefits repository maintainers.
- Provide examples of how the new feature should work.
- Wait for maintainers to review and approve the proposal before writing code.

---

## 3. Contribution Workflow

### Fork & Clone
1. Fork the PRobot repository to your own GitHub account.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/PRobot.git
   cd PRobot
   ```

### Branch Naming Conventions
Create a new feature branch for your changes. Use the following naming structure:
- `feat/feature-name` (for new features)
- `fix/bug-fix-name` (for bug fixes)
- `docs/doc-update-name` (for documentation updates)
- `refactor/refactor-name` (for code refactorings)

Example:
```bash
git checkout -b feat/add-slack-notifications
```

### Commit Message Conventions
We follow clear, readable commit messages. Please structure your commits as:
`<type>(scope): <short description>`

Types include:
- `feat`: A new feature.
- `fix`: A bug fix.
- `docs`: Documentation updates.
- `refactor`: Code restructuring with no behavior changes.
- `test`: Adding or updating test suites.

Example:
```text
feat(worker): add slack webhook dispatch task on duplicate detect
```

---

## 4. Pull Request Guidelines
When submitting a Pull Request (PR):
1. **Sync your fork**: Ensure your branch is updated with the latest `main` branch.
2. **Write tests**: Add or update corresponding unit tests under `backend/tests/` to verify your changes.
3. **Scan PR Quality**: Ensure your description has a linked issue and is descriptive. *Note that PRobot's PR Quality Guardian runs checks immediately on pull requests.*
4. **Submit**: Create the PR on the main repository, referencing the issue number it closes.

Once submitted, a maintainer will review your code. Thank you for making PRobot better!
