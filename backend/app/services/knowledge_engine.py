import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.issue import Issue
from app.models.comment import IssueComment
from app.models.repository import Repository
from app.models.embedding_record import EmbeddingRecord
from app.repositories.repository_repo import repository_repo
from app.repositories.base import CRUDBase
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.services.github_service import github_service
from app.utils.helpers import chunk_text


class KnowledgeEngine:
    """
    RAG engine for repository support.
    Indexes markdown documentation and past resolved issues.
    Retrieves relevant context to automatically answer user questions.
    """

    def reindex_repository(self, db: Session, repository: Repository) -> None:
        """
        Clones documentation files and resolved issues, chunks them,
        generates embeddings, and updates persistent collections.
        """
        logging.info(f"Re-indexing knowledge base for repository: {repository.full_name}")

        # 1. Clear existing embeddings for this repository in vector store & PostgreSQL
        vector_store.delete_by_repository("documentation_embeddings", str(repository.id))
        vector_store.delete_by_repository("resolved_issue_embeddings", str(repository.id))

        db.query(EmbeddingRecord).filter(EmbeddingRecord.repository_id == repository.id).delete()
        db.commit()

        # 2. Fetch and index README.md
        readme = github_service.fetch_file_content(repository.full_name, "README.md")
        if readme:
            self._index_document_text(db, repository, "README.md", readme)

        # 3. Fetch and index CONTRIBUTING.md
        contrib = github_service.fetch_file_content(repository.full_name, "CONTRIBUTING.md")
        if contrib:
            self._index_document_text(db, repository, "CONTRIBUTING.md", contrib)

        # 4. Fetch and index files inside docs/ folder
        try:
            docs_directory = github_service.fetch_repo_directory(repository.full_name, "docs")
            for item in docs_directory:
                if item.get("type") == "file" and item.get("name", "").endswith((".md", ".txt")):
                    content = github_service.fetch_file_content(repository.full_name, item.get("path", ""))
                    if content:
                        self._index_document_text(db, repository, item.get("path", ""), content)
        except Exception as e:
            logging.warning(f"Could not fetch docs/ folder directory listing: {str(e)}")

        # 5. Fetch and index previously resolved issues from local PostgreSQL DB
        resolved_issues = (
            db.query(Issue)
            .filter(
                Issue.repository_id == repository.id,
                Issue.state == "closed",
                Issue.is_duplicate == False,
            )
            .all()
        )

        logging.info(f"Indexing {len(resolved_issues)} resolved issues for {repository.full_name}")
        for issue in resolved_issues:
            # Gather comments to capture the actual resolution content
            comments = db.query(IssueComment).filter(IssueComment.issue_id == issue.id).all()
            comments_text = "\n".join([f"- {c.author}: {c.body}" for c in comments])

            resolved_text = (
                f"Resolved Issue #{issue.number}\n"
                f"Title: {issue.title}\n"
                f"Description: {issue.body or ''}\n"
                f"Resolution Comments:\n{comments_text}"
            )

            chunks = chunk_text(resolved_text, chunk_size=800, chunk_overlap=150)
            for idx, chunk in enumerate(chunks):
                vector_id = f"resolved_issue_{str(issue.id)}_{idx}"
                embedding = embedding_service.get_embedding(chunk)

                # Upsert to ChromaDB
                vector_store.upsert_embeddings(
                    collection_name="resolved_issue_embeddings",
                    ids=[vector_id],
                    embeddings=[embedding],
                    metadatas=[{"repository_id": str(repository.id), "issue_number": issue.number}],
                    documents=[chunk],
                )

                # Create metadata record
                db_record = EmbeddingRecord(
                    repository_id=repository.id,
                    entity_type="resolved_issue",
                    entity_id=str(issue.id),
                    chunk_index=idx,
                    text_content=chunk,
                    vector_id=vector_id,
                )
                db.add(db_record)
            db.commit()

        logging.info(f"Knowledge base indexing completed for {repository.full_name}")

    def _index_document_text(self, db: Session, repository: Repository, path: str, content: str) -> None:
        """Helper to index standard document content."""
        chunks = chunk_text(content, chunk_size=1000, chunk_overlap=200)
        logging.info(f"Indexing document '{path}' split into {len(chunks)} chunks.")

        for idx, chunk in enumerate(chunks):
            # Safe unique key for vector store
            vector_id = f"doc_{path.replace('/', '_').replace('.', '_')}_{idx}"
            embedding = embedding_service.get_embedding(chunk)

            # Save to Chroma
            vector_store.upsert_embeddings(
                collection_name="documentation_embeddings",
                ids=[vector_id],
                embeddings=[embedding],
                metadatas=[{"repository_id": str(repository.id), "file_path": path}],
                documents=[chunk],
            )

            # Save metadata reference
            db_record = EmbeddingRecord(
                repository_id=repository.id,
                entity_type="documentation",
                entity_id=path,
                chunk_index=idx,
                text_content=chunk,
                vector_id=vector_id,
            )
            db.add(db_record)
        db.commit()

    def answer_question_issue(self, db: Session, issue: Issue) -> None:
        """
        RAG Q&A retrieval and answering workflow.
        Queries documentation and resolved issues and synthesizes a response.
        """
        repository = repository_repo.get(db, issue.repository_id)
        if not repository:
            logging.error(f"Repository {issue.repository_id} not found for issue Q&A.")
            return

        settings = repository.settings or {}
        enabled = settings.get("knowledge_assistant_enabled", True)
        if not enabled:
            logging.info(f"Knowledge assistant disabled for repository {repository.full_name}")
            return

        # Prepare query search text
        query_text = f"Title: {issue.title}\n\nDescription: {issue.body or ''}"
        query_vector = embedding_service.get_embedding(query_text)

        # Retrieve doc matches & resolved issue matches
        # Similarity threshold: 0.70 is appropriate for context retrieval
        doc_matches = vector_store.query_similar(
            collection_name="documentation_embeddings",
            query_embedding=query_vector,
            repository_id=str(repository.id),
            limit=3,
            similarity_threshold=0.70,
        )

        resolved_matches = vector_store.query_similar(
            collection_name="resolved_issue_embeddings",
            query_embedding=query_vector,
            repository_id=str(repository.id),
            limit=3,
            similarity_threshold=0.70,
        )

        context_chunks = []
        for match in doc_matches:
            context_chunks.append(f"Source Document ({match['metadata'].get('file_path')}):\n{match['document']}")
        for match in resolved_matches:
            context_chunks.append(
                f"Source Closed Issue #{match['metadata'].get('issue_number')}):\n{match['document']}"
            )

        if not context_chunks:
            logging.info(f"No relevant knowledge base context found for {repository.full_name}#{issue.number}.")
            return

        logging.info(f"Retrieved {len(context_chunks)} context blocks. Synthesizing answer using Groq.")
        context_str = "\n\n---\n\n".join(context_chunks)

        system_prompt = (
            f"You are the official AI Repository Knowledge Assistant for {repository.full_name}.\n"
            "Your task is to answer user questions using the provided context from our documentation "
            "and previously resolved issues.\n\n"
            "Context documentation:\n"
            "======================\n"
            f"{context_str}\n"
            "======================\n\n"
            "Guidelines:\n"
            "1. Rely ONLY on the context blocks above to formulate your response.\n"
            "2. If the answer cannot be found or inferred from the context, do not make up facts. Politely tell "
            "the user that you cannot find the exact answer and suggest they wait for a human maintainer.\n"
            "3. Format your response clearly in Markdown. Cite the source files or past issue numbers if used."
        )

        user_content = (
            f"User Question:\n"
            f"Title: {issue.title}\n"
            f"Body: {issue.body or 'No description.'}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            answer = llm_service.chat_completion(
                messages=messages,
                temperature=0.2,
            )

            comment_body = (
                f"🤖 **PRobot Knowledge Assistant**\n\n"
                f"Based on repository documentation and past resolved issues, here is some information that might help:\n\n"
                f"{answer}\n\n"
                f"--- \n*This answer was generated automatically. If this resolved your query, feel free to close the issue!*"
            )

            github_service.post_comment(repository.full_name, issue.number, comment_body)
        except Exception as e:
            logging.error(f"Failed to generate synthesis response: {str(e)}")


knowledge_engine = KnowledgeEngine()
