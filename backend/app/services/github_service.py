import base64
import logging
from typing import Any, Dict, List, Optional
import requests
from app.core.config import settings
from app.core.exceptions import GitHubException


class GitHubService:
    """
    Communicates with the GitHub REST API (v3) using authentication tokens.
    Provides wrappers for repository maintenance tasks (comments, labels, status).
    """

    def __init__(self):
        self.base_url = "https://api.github.com"

    @property
    def _headers(self) -> Dict[str, str]:
        if not settings.GITHUB_TOKEN:
            logging.error("GITHUB_TOKEN is missing in settings config.")
            raise GitHubException("GitHub Service is unconfigured: GITHUB_TOKEN is missing.")

        return {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PRobot-AI-Maintainer-Agent",
        }

    def post_comment(self, repo_full_name: str, issue_number: int, body: str) -> Dict[str, Any]:
        """
        Post a comment on a GitHub issue or pull request.
        """
        url = f"{self.base_url}/repos/{repo_full_name}/issues/{issue_number}/comments"
        try:
            logging.info(f"Posting comment on {repo_full_name}#{issue_number}")
            response = requests.post(url, json={"body": body}, headers=self._headers, timeout=10)
            if response.status_code != 201:
                raise GitHubException(
                    f"Failed to post comment. Status: {response.status_code}, Body: {response.text}",
                    status_code=response.status_code,
                )
            logging.info(f"Comment posted: {repo_full_name}#{issue_number}")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Request exception posting comment: {str(e)}")
            raise GitHubException(f"Connection to GitHub failed: {str(e)}")

    def add_labels(self, repo_full_name: str, number: int, labels: List[str]) -> List[Dict[str, Any]]:
        """
        Add one or more labels to a GitHub issue or pull request.
        """
        if not labels:
            return []
        url = f"{self.base_url}/repos/{repo_full_name}/issues/{number}/labels"
        try:
            logging.info(f"Adding labels {labels} to {repo_full_name}#{number}")
            response = requests.post(url, json={"labels": labels}, headers=self._headers, timeout=10)
            if response.status_code != 200:
                raise GitHubException(
                    f"Failed to add labels. Status: {response.status_code}, Body: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Request exception adding labels: {str(e)}")
            raise GitHubException(f"Connection to GitHub failed: {str(e)}")

    def remove_label(self, repo_full_name: str, number: int, label: str) -> None:
        """
        Remove a specific label from a GitHub issue or pull request.
        """
        url = f"{self.base_url}/repos/{repo_full_name}/issues/{number}/labels/{label}"
        try:
            logging.info(f"Removing label '{label}' from {repo_full_name}#{number}")
            response = requests.delete(url, headers=self._headers, timeout=10)
            if response.status_code not in (200, 404):  # Ignore 404 if it wasn't there
                raise GitHubException(
                    f"Failed to remove label. Status: {response.status_code}, Body: {response.text}",
                    status_code=response.status_code,
                )
        except requests.RequestException as e:
            logging.error(f"Request exception removing label: {str(e)}")
            raise GitHubException(f"Connection to GitHub failed: {str(e)}")

    def close_issue(self, repo_full_name: str, issue_number: int) -> Dict[str, Any]:
        """
        Close a GitHub issue.
        """
        url = f"{self.base_url}/repos/{repo_full_name}/issues/{issue_number}"
        try:
            logging.info(f"Closing issue {repo_full_name}#{issue_number}")
            response = requests.patch(
                url,
                json={"state": "closed", "state_reason": "completed"},
                headers=self._headers,
                timeout=10,
            )
            if response.status_code != 200:
                raise GitHubException(
                    f"Failed to close issue. Status: {response.status_code}, Body: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Request exception closing issue: {str(e)}")
            raise GitHubException(f"Connection to GitHub failed: {str(e)}")

    def fetch_pr_files(self, repo_full_name: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Fetch the list of files modified in a pull request.
        """
        url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/files"
        try:
            logging.info(f"Fetching files for PR {repo_full_name}#{pr_number}")
            response = requests.get(url, headers=self._headers, timeout=15)
            if response.status_code != 200:
                raise GitHubException(
                    f"Failed to fetch PR files. Status: {response.status_code}, Body: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Request exception fetching PR files: {str(e)}")
            raise GitHubException(f"Connection to GitHub failed: {str(e)}")

    def fetch_file_content(self, repo_full_name: str, path: str, ref: str = "main") -> Optional[str]:
        """
        Fetch and base64 decode a file's content from a repository.
        Returns None if the file does not exist (404).
        """
        url = f"{self.base_url}/repos/{repo_full_name}/contents/{path}"
        try:
            logging.info(f"Fetching file {path} from {repo_full_name} (ref={ref})")
            response = requests.get(url, params={"ref": ref}, headers=self._headers, timeout=15)
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise GitHubException(
                    f"Failed to fetch file {path}. Status: {response.status_code}, Body: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            if "content" in data and data.get("encoding") == "base64":
                decoded_bytes = base64.b64decode(data["content"])
                return decoded_bytes.decode("utf-8", errors="ignore")
            elif isinstance(data, list):
                # If it's a directory
                raise GitHubException(f"Path {path} is a directory, not a file.")

            return ""
        except requests.RequestException as e:
            logging.error(f"Request exception fetching file content: {str(e)}")
            raise GitHubException(f"Connection to GitHub failed: {str(e)}")

    def fetch_repo_directory(self, repo_full_name: str, path: str, ref: str = "main") -> List[Dict[str, Any]]:
        """
        Fetch the listing of a directory in the repository.
        Returns an empty list if not found.
        """
        url = f"{self.base_url}/repos/{repo_full_name}/contents/{path}"
        try:
            logging.info(f"Listing directory {path} in {repo_full_name} (ref={ref})")
            response = requests.get(url, params={"ref": ref}, headers=self._headers, timeout=15)
            if response.status_code == 404:
                return []
            if response.status_code != 200:
                raise GitHubException(
                    f"Failed to list directory {path}. Status: {response.status_code}, Body: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            if isinstance(data, list):
                return data
            return []
        except requests.RequestException as e:
            logging.error(f"Request exception fetching repo directory listing: {str(e)}")
            raise GitHubException(f"Connection to GitHub failed: {str(e)}")

    def create_comment(self, repo_full_name: str, number: int, body: str) -> Dict[str, Any]:
        """
        Post a comment on a GitHub issue or pull request (required API wrapper).
        """
        return self.post_comment(repo_full_name, number, body)

    def get_issue(self, repo_full_name: str, number: int) -> Dict[str, Any]:
        """
        Retrieve a single issue details from GitHub.
        """
        url = f"{self.base_url}/repos/{repo_full_name}/issues/{number}"
        try:
            logging.info(f"Fetching issue {repo_full_name}#{number} from GitHub")
            response = requests.get(url, headers=self._headers, timeout=10)
            if response.status_code != 200:
                raise GitHubException(
                    f"Failed to fetch issue. Status: {response.status_code}, Body: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Request exception fetching issue: {str(e)}")
            raise GitHubException(f"Connection to GitHub failed: {str(e)}")

    def get_pull_request(self, repo_full_name: str, number: int) -> Dict[str, Any]:
        """
        Retrieve a single pull request details from GitHub.
        """
        url = f"{self.base_url}/repos/{repo_full_name}/pulls/{number}"
        try:
            logging.info(f"Fetching pull request {repo_full_name}#{number} from GitHub")
            response = requests.get(url, headers=self._headers, timeout=10)
            if response.status_code != 200:
                raise GitHubException(
                    f"Failed to fetch pull request. Status: {response.status_code}, Body: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Request exception fetching pull request: {str(e)}")
            raise GitHubException(f"Connection to GitHub failed: {str(e)}")


github_service = GitHubService()
