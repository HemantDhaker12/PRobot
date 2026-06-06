import os
import sys
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to sys.path to resolve app imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, SessionLocal
from app.models import Base, Repository, Issue, PullRequest, IssueComment, EmbeddingRecord
from app.services.duplicate_detector import duplicate_detector
from app.services.triage_engine import triage_engine
from app.services.label_engine import label_engine
from app.services.pr_review_engine import pr_review_engine
from app.services.knowledge_engine import knowledge_engine
from app.services.github_service import github_service
from app.services.llm_service import llm_service

# Determine if credentials are actual values or placeholders
groq_key = os.getenv("GROQ_API_KEY", "")
github_token = os.getenv("GITHUB_TOKEN", "")

is_groq_configured = bool(groq_key and "your_groq" not in groq_key.lower() and "placeholder" not in groq_key.lower())
is_github_configured = bool(github_token and "your_github" not in github_token.lower() and "placeholder" not in github_token.lower())

from unittest.mock import MagicMock
import json

# Setup Global Mock Interceptors if credentials are not configured
if not is_github_configured:
    print("⚠️  GITHUB_TOKEN is a placeholder. Mocking GitHub API calls to prevent 401 errors.")
    github_service.post_comment = MagicMock(side_effect=lambda repo, num, body: print(f"      [Mock GitHub Comment Posted on #{num}]:\n      {body.replace(chr(10), chr(10)+'      ')}\n"))
    github_service.add_labels = MagicMock(side_effect=lambda repo, num, labels: print(f"      [Mock GitHub Labels Added on #{num}]: {labels}"))
    github_service.remove_label = MagicMock(side_effect=lambda repo, num, label: print(f"      [Mock GitHub Label Removed on #{num}]: {label}"))
    github_service.close_issue = MagicMock(side_effect=lambda repo, num: print(f"      [Mock GitHub Issue #{num} Closed]"))
    github_service.fetch_pr_files = MagicMock(return_value=[
        {"filename": "app/main.py", "status": "modified"},
        {"filename": "app/core/config.py", "status": "modified"}
    ])
    github_service.fetch_file_content = MagicMock(return_value="# Demo Repository\nWe use Postgres port 5432 and run with 'make run'.")
    github_service.fetch_repo_directory = MagicMock(return_value=[])

if not is_groq_configured:
    print("⚠️  GROQ_API_KEY is a placeholder. Mocking Groq LLM API responses.")
    # Mock triage analysis
    triage_mock_res = {
        "os": {"present": False, "explanation": "Not mentioned"},
        "language_version": {"present": True, "explanation": "Python 3"},
        "package_version": {"present": True, "explanation": "v1.0"},
        "error_logs": {"present": True, "explanation": "Logs included"},
        "reproduction_steps": {"present": False, "explanation": "No steps"},
    }
    # Mock label classification
    label_mock_res = {"labels": ["documentation", "question"]}
    
    def mock_chat_completion(messages, **kwargs):
        system_content = messages[0]["content"].lower()
        if "triage" in system_content or "reproduce" in system_content:
            return json.dumps(triage_mock_res)
        elif "classify" in system_content or "label" in system_content:
            return json.dumps(label_mock_res)
        elif "synthesis" in system_content or "knowledge" in system_content:
            return "Based on the README, to start the server you must run `make run`. PostgreSQL is bound on port 5432."
        return "{}"
        
    llm_service.chat_completion = MagicMock(side_effect=mock_chat_completion)


def setup_demo_db():
    """Create schemas and populate with a dummy repository inside the database."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if repository already exists
    repo = db.query(Repository).filter(Repository.github_id == 987654321).first()
    if repo:
        repo_id = repo.id
        # Purge old demo records from tables to ensure clean run
        db.query(IssueComment).filter(IssueComment.repository_id == repo_id).delete()
        db.query(Issue).filter(Issue.repository_id == repo_id).delete()
        db.query(PullRequest).filter(PullRequest.repository_id == repo_id).delete()
        db.query(EmbeddingRecord).filter(EmbeddingRecord.repository_id == repo_id).delete()
        db.commit()
        db.close()
        return repo_id

    # Create dummy repository
    repo = Repository(
        id=uuid4(),
        github_id=987654321,
        full_name="demo-org/demo-repo",
        owner="demo-org",
        name="demo-repo",
        settings={
            "duplicate_detection_enabled": True,
            "duplicate_similarity_threshold": 0.80,
            "duplicate_auto_close": True,
            "triage_enabled": True,
            "labeling_enabled": True,
            "pr_guardian_enabled": True,
            "knowledge_assistant_enabled": True,
            "labels": ["bug", "feature-request", "documentation", "question"],
        },
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    repo_id = repo.id
    db.close()
    return repo_id


def run_duplicate_demo(repo_id):
    """Simulates duplicate issue checks."""
    print("\n--- 🔍 TESTING FEATURE 1: DUPLICATE ISSUE DETECTION ---")
    db = SessionLocal()

    # Create base issue
    issue1 = Issue(
        id=uuid4(),
        repository_id=repo_id,
        number=1,
        title="Web server crashes on login request",
        body="When sending a POST request to /login, the backend server crashes with a segmentation fault.",
        state="open",
        html_url="https://github.com/demo-org/demo-repo/issues/1",
        labels=[],
    )
    db.add(issue1)
    db.commit()

    print("[1/2] Indexing original issue #1 in ChromaDB vector store...")
    duplicate_detector.process_issue(db, issue1)
    print("      Original issue registered successfully.")

    # Create duplicate issue (or similar issue)
    issue2 = Issue(
        id=uuid4(),
        repository_id=repo_id,
        number=2,
        title="Backend fails when posting to login route",
        body="Posting to the /login endpoint triggers a core dump. The application goes down immediately.",
        state="open",
        html_url="https://github.com/demo-org/demo-repo/issues/2",
        labels=[],
    )
    db.add(issue2)
    db.commit()

    print("[2/2] Running semantic search for issue #2...")
    duplicate_detector.process_issue(db, issue2)

    db.refresh(issue2)
    print(f"      Result: Is Duplicate? {issue2.is_duplicate}")
    print(f"      Result State: {issue2.state}")
    db.close()


def run_triage_demo(repo_id):
    """Simulates checking issues for missing context information."""
    print("\n--- 📝 TESTING FEATURE 2: INTELLIGENT ISSUE TRIAGE ---")
    db = SessionLocal()

    issue = Issue(
        id=uuid4(),
        repository_id=repo_id,
        number=3,
        title="Cannot install library",
        body="I ran pip install and it throws an error in python.",
        state="open",
        html_url="https://github.com/demo-org/demo-repo/issues/3",
        labels=[],
    )
    db.add(issue)
    db.commit()

    print("Analyzing issue #3 content for missing fields (OS, language/package versions, traceback, steps)...")
    triage_engine.process_issue(db, issue)
    db.close()


def run_label_demo(repo_id):
    """Simulates labeling issues."""
    print("\n--- 🏷️ TESTING FEATURE 3: SMART AUTO LABELING ---")
    db = SessionLocal()

    issue = Issue(
        id=uuid4(),
        repository_id=repo_id,
        number=4,
        title="Documentation request for database config",
        body="The README lacks configuration parameters for PostgreSQL port bindings. Please document this.",
        state="open",
        html_url="https://github.com/demo-org/demo-repo/issues/4",
        labels=[],
    )
    db.add(issue)
    db.commit()

    print("Classifying issue #4 using LLM classifier...")
    label_engine.classify_and_label(db, issue, is_pr=False)

    db.refresh(issue)
    print(f"      Applied Labels: {issue.labels}")
    db.close()


def run_pr_demo(repo_id):
    """Simulates pull request guardian rules."""
    print("\n--- 🛡️ TESTING FEATURE 4: PR QUALITY GUARDIAN ---")
    db = SessionLocal()

    pr = PullRequest(
        id=uuid4(),
        repository_id=repo_id,
        number=10,
        title="Refactor auth middleware",
        body="This is my PR.",  # Missing issue reference, short body, source code changes but no tests changed
        state="open",
        html_url="https://github.com/demo-org/demo-repo/pull/10",
        is_draft=False,
    )
    db.add(pr)
    db.commit()

    print("Running quality check validators on PR #10...")
    pr_review_engine.review_pr(db, pr)
    db.close()


def run_rag_demo(repo_id):
    """Simulates RAG documentation index and search assistant."""
    print("\n--- 📖 TESTING FEATURE 5: REPOSITORY KNOWLEDGE ASSISTANT (RAG) ---")
    db = SessionLocal()

    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    print("Indexing documentation chunks (README.md mock)...")
    readme_mock = (
        "# Demo Repository\n\n"
        "## Setup Guide\n"
        "To start the server, configure GITHUB_TOKEN and run `make run`.\n"
        "Ensure PostgreSQL is bound on port 5432 and Redis is bound on port 6379."
    )

    knowledge_engine._index_document_text(db, repo, "README.md", readme_mock)
    print("      README.md indexed successfully.")

    # Create question issue
    issue = Issue(
        id=uuid4(),
        repository_id=repo_id,
        number=15,
        title="How do I start the server and what port does PostgreSQL use?",
        body="I am struggling to set up. What is the database port?",
        state="open",
        html_url="https://github.com/demo-org/demo-repo/issues/15",
        labels=["question"],
    )
    db.add(issue)
    db.commit()

    print("Executing RAG retrieval and synthesis on question #15...")
    knowledge_engine.answer_question_issue(db, issue)
    db.close()


if __name__ == "__main__":
    print("==================================================")
    print("🤖 PRobot Foundation - Local Interactive Demo 🤖")
    print("==================================================")

    # 1. Setup Database
    repo_id = setup_demo_db()
    print("Database initializations completed.")

    # 2. Let user choose option or run all
    print("\nSelect the demo option to run:")
    print("1. Duplicate Issue Detector")
    print("2. Intelligent Issue Triage")
    print("3. Auto Labeling Classifier")
    print("4. PR Quality Guardian")
    print("5. Knowledge RAG Assistant")
    print("6. Run all features sequentially")

    try:
        choice = input("\nEnter choice (1-6): ").strip()
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting.")
        sys.exit(0)

    if choice == "1":
        run_duplicate_demo(repo_id)
    elif choice == "2":
        run_triage_demo(repo_id)
    elif choice == "3":
        run_label_demo(repo_id)
    elif choice == "4":
        run_pr_demo(repo_id)
    elif choice == "5":
        run_rag_demo(repo_id)
    elif choice == "6":
        run_duplicate_demo(repo_id)
        run_triage_demo(repo_id)
        run_label_demo(repo_id)
        run_pr_demo(repo_id)
        run_rag_demo(repo_id)
    else:
        print("Invalid choice. Running all features sequentially:")
        run_duplicate_demo(repo_id)
        run_triage_demo(repo_id)
        run_label_demo(repo_id)
        run_pr_demo(repo_id)
        run_rag_demo(repo_id)

    print("\n==================================================")
    print("🎉 Demo complete! Check chroma_db/ folder for vector indices.")
    print("==================================================")
