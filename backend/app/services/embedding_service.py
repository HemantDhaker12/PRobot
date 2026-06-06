import logging
from typing import List, Optional
from fastembed import TextEmbedding


class EmbeddingService:
    """
    Local embedding generator using FastEmbed for CPU-efficient, dependency-free text embedding.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self._model: Optional[TextEmbedding] = None

    @property
    def model(self) -> TextEmbedding:
        if self._model is None:
            logging.info(f"Initializing FastEmbed TextEmbedding with model: {self.model_name}")
            try:
                self._model = TextEmbedding(model_name=self.model_name)
            except Exception as e:
                logging.error(f"Failed to load FastEmbed model {self.model_name}: {str(e)}")
                raise
        return self._model

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate a single vector embedding for the input text.
        """
        if not text.strip():
            # Return a zero vector if the input text is empty
            return [0.0] * 384
        try:
            embeddings_generator = self.model.embed([text])
            embedding = next(embeddings_generator)
            return [float(x) for x in embedding]
        except Exception as e:
            logging.error(f"Error generating embedding: {str(e)}")
            raise

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate multiple vector embeddings in a batch.
        """
        if not texts:
            return []
        try:
            embeddings_generator = self.model.embed(texts)
            return [[float(x) for x in emb] for emb in embeddings_generator]
        except Exception as e:
            logging.error(f"Error generating batch embeddings: {str(e)}")
            raise


embedding_service = EmbeddingService()
