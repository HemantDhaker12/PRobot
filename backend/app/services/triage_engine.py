import json
import logging
from sqlalchemy.orm import Session
from app.models.issue import Issue
from app.repositories.repository_repo import repository_repo
from app.services.llm_service import llm_service
from app.services.github_service import github_service


class TriageEngine:
    """
    Analyzes issues for missing debugging metadata using Groq LLM.
    Posts a checklist request comment if crucial info is absent.
    """

    def process_issue(self, db: Session, issue: Issue) -> None:
        repository = repository_repo.get(db, issue.repository_id)
        if not repository:
            logging.error(f"Repository {issue.repository_id} not found for issue triage.")
            return

        settings = repository.settings or {}
        enabled = settings.get("triage_enabled", True)
        if not enabled:
            logging.info(f"Triage disabled for repository {repository.full_name}")
            return

        author = issue.html_url.split("/")[-3] if issue.html_url else "reporter"

        # Prepare messages for LLM analysis
        system_prompt = (
            "You are a professional open-source repository maintainer assistant.\n"
            "Your job is to classify the GitHub issue and identify any missing triage information.\n\n"
            "1. Categorize the issue into one or more of the following categories:\n"
            "   - 'documentation' (e.g., README typos, documentation errors)\n"
            "   - 'installation' (e.g., installation command failures, setup errors, incorrect install instructions)\n"
            "   - 'bug' (e.g., runtime exceptions, crashes, unexpected logic errors)\n"
            "   - 'enhancement' (e.g., new feature requests, improvements like dark mode)\n"
            "   - 'question' (e.g., configuration queries, how-to questions)\n\n"
            "2. Assign a confidence score (between 0.0 and 1.0) representing your confidence in this categorization.\n\n"
            "3. For each category predicted, identify which of the following standard information is MISSING or not addressed in the issue title and description:\n"
            "   - For 'documentation':\n"
            "     * 'Which section is incorrect?'\n"
            "     * 'Expected behavior?'\n"
            "     * 'Suggested correction?'\n"
            "   - For 'installation':\n"
            "     * 'Exact command executed'\n"
            "     * 'Command output'\n"
            "     * 'OS'\n"
            "     * 'Error message'\n"
            "   - For 'bug':\n"
            "     * 'Reproduction steps'\n"
            "     * 'Logs'\n"
            "     * 'Environment details'\n"
            "   - For 'question':\n"
            "     * 'What are you trying to achieve?'\n"
            "   - For 'enhancement':\n"
            "     No additional triage details are required.\n\n"
            "4. Generate a friendly, tailored introductory sentence ('custom_intro') based on the issue topic.\n\n"
            "You MUST respond ONLY in a JSON object with the following schema:\n"
            "{\n"
            "  \"categories\": [\"category1\", \"category2\"],\n"
            "  \"confidence\": 0.95,\n"
            "  \"missing_questions\": [\"Question 1\", \"Question 2\"],\n"
            "  \"custom_intro\": \"A tailored, context-aware introductory sentence.\"\n"
            "}"
        )

        user_content = f"Issue Title: {issue.title}\n\nIssue Description:\n{issue.body or 'No description provided.'}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            # Request JSON structured output from Groq
            raw_response = llm_service.chat_completion(
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            analysis = json.loads(raw_response)
        except Exception as e:
            logging.error(f"Error calling LLM for issue triage: {str(e)}")
            return

        # Parse results with backward compatibility fallback
        categories = analysis.get("categories", ["bug"])
        confidence = analysis.get("confidence", 1.0)
        custom_intro = analysis.get("custom_intro")

        if "missing_questions" in analysis:
            missing_fields = analysis["missing_questions"]
        else:
            # Old format fallback
            missing_fields = []
            if not analysis.get("os", {}).get("present", True):
                missing_fields.append("Operating System (OS)")
            if not analysis.get("language_version", {}).get("present", True):
                missing_fields.append("Programming language version (e.g. Python 3.11)")
            if not analysis.get("package_version", {}).get("present", True):
                missing_fields.append("Package / Library version")
            if not analysis.get("error_logs", {}).get("present", True):
                desc = (issue.body or "").lower()
                if "error" in desc or "fail" in desc or "crash" in desc or "exception" in desc:
                    missing_fields.append("Error logs / Stack trace")
            if not analysis.get("reproduction_steps", {}).get("present", True):
                missing_fields.append("Clear steps to reproduce (code snippet or script)")

        # Log predicted category, confidence and template
        logging.info(f"Triage Analysis for {repository.full_name}#{issue.number}:")
        logging.info(f"Predicted Categories: {categories}")
        logging.info(f"Confidence: {confidence}")

        if missing_fields:
            # Format checklist
            checklist_items = "\n".join(f"- [ ] {field}" for field in missing_fields)

            if not custom_intro:
                custom_intro = f"Thanks for opening this issue @{author}! To help the maintainers reproduce and diagnose this issue faster, please edit your description and provide the following missing information:"

            comment_body = (
                f"🤖 **PRobot Triage Assistant**\n\n"
                f"{custom_intro}\n\n"
                f"{checklist_items}\n\n"
                f"Once you update these details, we'll continue reviewing your report. Thank you!"
            )

            # Log the generated triage template
            logging.info(f"Generated Triage Template:\n{comment_body}")

            github_service.post_comment(repository.full_name, issue.number, comment_body)
        else:
            logging.info(f"Triage complete for {repository.full_name}#{issue.number}. No info missing.")


triage_engine = TriageEngine()
