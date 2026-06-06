import json
import logging
from typing import List, Union
from sqlalchemy.orm import Session
from app.models.issue import Issue
from app.models.pull_request import PullRequest
from app.repositories.repository_repo import repository_repo
from app.services.llm_service import llm_service
from app.services.github_service import github_service


class LabelEngine:
    """
    Classifies issues and pull requests using Groq LLM against configured labels,
    and applies them using the GitHub API.
    """

    DEFAULT_LABELS = [
        "bug",
        "feature-request",
        "documentation",
        "enhancement",
        "question",
        "help-wanted",
        "good-first-issue",
    ]

    def classify_and_label(self, db: Session, item: Union[Issue, PullRequest], is_pr: bool) -> None:
        repository = repository_repo.get(db, item.repository_id)
        if not repository:
            logging.error(f"Repository {item.repository_id} not found for labeling.")
            return

        settings = repository.settings or {}
        enabled = settings.get("labeling_enabled", True)
        if not enabled:
            logging.info(f"Labeling disabled for repository {repository.full_name}")
            return

        # Fetch allowed labels from settings or defaults
        allowed_labels = settings.get("labels", self.DEFAULT_LABELS)

        item_type = "Pull Request" if is_pr else "Issue"
        logging.info(f"Classifying {item_type} {repository.full_name}#{item.number}")

        system_prompt = (
            "You are a repository maintainer bot. Your job is to classify GitHub issues and pull requests.\n"
            f"You MUST select one or more labels from this exact list: {allowed_labels}.\n\n"
            "Respond ONLY with a JSON object containing a 'labels' list, for example:\n"
            '{\n  "labels": ["bug", "help-wanted"]\n}'
        )

        user_content = (
            f"{item_type} Title: {item.title}\n\n" f"{item_type} Description:\n{item.body or 'No description.'}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            raw_response = llm_service.chat_completion(
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            classification = json.loads(raw_response)
            labels_to_apply = classification.get("labels", [])
        except Exception as e:
            logging.error(f"Error classifying {item_type}: {str(e)}")
            return

        # Sanitize to match only configured labels
        labels_to_apply = [lbl for lbl in labels_to_apply if lbl in allowed_labels]

        if labels_to_apply:
            logging.info(f"Applying labels {labels_to_apply} to {repository.full_name}#{item.number}")

            # Apply labels via GitHub API
            github_service.add_labels(repository.full_name, item.number, labels_to_apply)
            logging.info(f"Labels applied: {labels_to_apply} to {repository.full_name}#{item.number}")

            # Sync local PostgreSQL cache
            if not is_pr and isinstance(item, Issue):
                # We save labels as JSONB list
                current_labels = list(item.labels or [])
                updated_labels = list(set(current_labels + labels_to_apply))
                item.labels = updated_labels
                db.commit()
        else:
            logging.info(f"No labels matched for {repository.full_name}#{item.number}")


label_engine = LabelEngine()
