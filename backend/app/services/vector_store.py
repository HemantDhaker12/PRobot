import logging
from typing import Any, Dict, List, Optional
import chromadb
from app.core.config import settings


class VectorStoreService:
    """
    Service wrapper for ChromaDB. Manages persistence, collections,
    indexing, and metadata-filtered vector semantic search.
    """

    def __init__(self):
        self._client: Optional[chromadb.ClientAPI] = None

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            logging.info(f"Initializing ChromaDB PersistentClient at: {settings.CHROMA_PATH}")
            try:
                self._client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
            except Exception as e:
                logging.error(f"Failed to initialize ChromaDB PersistentClient: {str(e)}")
                raise
        return self._client

    def _get_collection(self, collection_name: str) -> chromadb.Collection:
        """
        Gets or creates a collection. Configured with Cosine space for normalized similarity metrics.
        """
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_embeddings(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: List[str],
    ) -> None:
        """
        Inserts or updates vector records in the specified collection.
        """
        if not ids:
            return
        try:
            collection = self._get_collection(collection_name)
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )
            logging.info(f"Successfully upserted {len(ids)} vectors to {collection_name}")
        except Exception as e:
            logging.error(f"Error upserting to ChromaDB collection {collection_name}: {str(e)}")
            raise

    def query_similar(
        self,
        collection_name: str,
        query_embedding: List[float],
        repository_id: str,
        limit: int = 5,
        similarity_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform a vector similarity search in the collection, filtered by repository_id.
        Calculates cosine similarity from Chroma's distance: similarity = 1.0 - distance.
        """
        try:
            collection = self._get_collection(collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"repository_id": repository_id},
            )

            matched_records = []
            if not results or "ids" not in results or not results["ids"][0]:
                return []

            # Chroma query returns results grouped inside a list of queries. We query 1 vector, so take index 0.
            ids = results["ids"][0]
            distances = results["distances"][0] if "distances" in results and results["distances"] else []
            metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []
            documents = results["documents"][0] if "documents" in results and results["documents"] else []

            for i in range(len(ids)):
                distance = distances[i] if i < len(distances) else 1.0
                similarity = 1.0 - distance  # Since space is configured as "cosine"

                if similarity_threshold is not None and similarity < similarity_threshold:
                    continue

                matched_records.append(
                    {
                        "id": ids[i],
                        "similarity": similarity,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "document": documents[i] if i < len(documents) else "",
                    }
                )

            # Sort by similarity descending
            matched_records.sort(key=lambda x: x["similarity"], reverse=True)
            return matched_records
        except Exception as e:
            logging.error(f"Error querying ChromaDB collection {collection_name}: {str(e)}")
            raise

    def delete_embeddings(self, collection_name: str, ids: List[str]) -> None:
        """
        Delete specific records from a collection by their IDs.
        """
        if not ids:
            return
        try:
            collection = self._get_collection(collection_name)
            collection.delete(ids=ids)
            logging.info(f"Deleted {len(ids)} vectors from {collection_name}")
        except Exception as e:
            logging.error(f"Error deleting from ChromaDB collection {collection_name}: {str(e)}")
            raise

    def delete_by_repository(self, collection_name: str, repository_id: str) -> None:
        """
        Delete all records belonging to a repository from a collection.
        """
        try:
            collection = self._get_collection(collection_name)
            collection.delete(where={"repository_id": repository_id})
            logging.info(f"Deleted vectors for repository {repository_id} from {collection_name}")
        except Exception as e:
            logging.error(f"Error deleting repository {repository_id} from {collection_name}: {str(e)}")
            raise


vector_store = VectorStoreService()
