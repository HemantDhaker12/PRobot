import logging
import re
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.pull_request import PullRequest
from app.repositories.repository_repo import repository_repo
from app.services.github_service import github_service


class PRReviewEngine:
    """
    Validates quality standards on incoming Pull Requests (PRs).
    Performs checks on description length, linked issues, tests modification, and breaking changes.
    """

    # Match github keywords for closing issues: e.g. "fixes #12" or "resolves owner/repo#3"
    ISSUE_LINK_REGEX = re.compile(
        r"\b(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+(?:#\d+|[a-zA-Z0-9\-_\.]+/[a-zA-Z0-9\-_\.]+#\d+)\b",
        re.IGNORECASE,
    )

    # File extensions representing production source code changes
    SRC_CODE_EXTENSIONS = (
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".go",
        ".java",
        ".cpp",
        ".h",
        ".c",
        ".rs",
        ".rb",
        ".php",
    )

    def review_pr(self, db: Session, pr: PullRequest) -> None:
        repository = repository_repo.get(db, pr.repository_id)
        if not repository:
            logging.error(f"Repository {pr.repository_id} not found for PR review.")
            return

        settings = repository.settings or {}
        enabled = settings.get("pr_guardian_enabled", True)
        if not enabled:
            logging.info(f"PR Guardian disabled for repository {repository.full_name}")
            return

        logging.info(f"PR Guardian evaluating {repository.full_name}#{pr.number}")

        # Check 1: Description Exists & Length
        description = pr.body or ""
        desc_exists = len(description.strip()) > 15
        desc_status = "✅ PASSED" if desc_exists else "❌ FAILED"
        desc_details = (
            f"PR description is {len(description.strip())} chars."
            if desc_exists
            else "PR description is missing or too short (must be > 15 chars)."
        )

        # Check 2: Linked Issue
        linked_issue_match = self.ISSUE_LINK_REGEX.search(description)
        issue_status = "✅ PASSED" if linked_issue_match else "⚠️ WARNING"
        issue_details = (
            f"Linked issue reference detected: `{linked_issue_match.group(0)}`"
            if linked_issue_match
            else "No closing issue keyword detected (e.g. 'fixes #10'). Please link an issue."
        )

        # Check 3: Tests Added if source files are changed
        has_src_changes = False
        has_test_changes = False
        files_modified = []

        try:
            pr_files = github_service.fetch_pr_files(repository.full_name, pr.number)
            for file_info in pr_files:
                filename = file_info.get("filename", "")
                files_modified.append(filename)

                # Check if it is a source file
                if filename.endswith(self.SRC_CODE_EXTENSIONS):
                    # Exclude typical test directories/files from source counts
                    if not any(t_path in filename.lower() for t_path in ("test", "tests", "spec", "mock")):
                        has_src_changes = True

                # Check if it is a test file
                if any(t_path in filename.lower() for t_path in ("test", "tests", "spec", "mock")):
                    has_test_changes = True
        except Exception as e:
            logging.error(f"Failed to fetch PR files for evaluation: {str(e)}")
            # We don't fail the entire review, just report N/A or warning
            has_src_changes = True
            has_test_changes = False

        if has_src_changes:
            test_status = "✅ PASSED" if has_test_changes else "❌ FAILED"
            test_details = (
                "Tests were added or updated alongside source code changes."
                if has_test_changes
                else "Source code files were modified but no test files were added/edited."
            )
        else:
            test_status = "➖ N/A"
            test_details = "No source code modifications detected in this PR."

        # Check 4: Breaking Changes
        breaking_patterns = [
            r"breaking\s+change",
            r"breaking-change",
            r"\bbc\b",
            r"\[x\]\s*breaking",
        ]
        has_breaking = any(re.search(pat, description, re.IGNORECASE) for pat in breaking_patterns)
        breaking_status = "⚠️ ATTENTION" if has_breaking else "➖ NONE DETECTED"
        breaking_details = (
            "PR description explicitly mentions breaking changes. Maintainers, please review carefully."
            if has_breaking
            else "No breaking changes declaration found in description."
        )

        # Construct Markdown review feedback
        overall_passed = desc_exists and (not has_src_changes or has_test_changes)
        shield = "🟢" if overall_passed else "🔴"

        comment_body = (
            f"### {shield} **PRobot Quality Guardian Review**\n\n"
            f"PRobot has completed automated checks for this pull request. Review summary:\n\n"
            f"| Check | Status | Details |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **PR Description** | {desc_status} | {desc_details} |\n"
            f"| **Linked Issue** | {issue_status} | {issue_details} |\n"
            f"| **Test Verification** | {test_status} | {test_details} |\n"
            f"| **Breaking Changes** | {breaking_status} | {breaking_details} |\n\n"
        )

        if not overall_passed:
            comment_body += (
                "⚠️ **Action Required**: Please address the failed checks above. "
                "Ensure a detailed description is provided, and if you modified source code, "
                "include corresponding unit tests."
            )
        else:
            comment_body += "✨ Great job! All mandatory quality checks have passed."

        # Post the review comment to GitHub
        github_service.post_comment(repository.full_name, pr.number, comment_body)


pr_review_engine = PRReviewEngine()
