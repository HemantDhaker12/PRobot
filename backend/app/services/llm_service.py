import logging
from typing import Any, Dict, List, Optional
from groq import Groq
from app.core.config import settings
from app.core.exceptions import LLMException


class LLMService:
    """
    LLM service client integrated with Groq API.
    Handles system instructions, context retrieval, and structured JSON output requests.
    """

    def __init__(self, default_model: str = "llama-3.3-70b-versatile"):
        self.default_model = default_model
        self._client: Optional[Groq] = None

    @property
    def client(self) -> Groq:
        if self._client is None:
            if not settings.GROQ_API_KEY:
                logging.error("GROQ_API_KEY is not configured in settings.")
                raise LLMException("LLM Service is unconfigured: GROQ_API_KEY is missing.")
            try:
                self._client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                logging.error(f"Failed to initialize Groq client: {str(e)}")
                raise LLMException(f"Failed to initialize LLM client: {str(e)}")
        return self._client

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Sends a chat request to Groq API and returns the string message payload.
        """
        selected_model = model or self.default_model
        try:
            logging.info(f"Sending LLM chat completion request to model: {selected_model}")
            kwargs: Dict[str, Any] = {
                "messages": messages,
                "model": selected_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format

            completion = self.client.chat.completions.create(**kwargs)
            content = completion.choices[0].message.content
            if not content:
                raise LLMException("LLM returned an empty response.")
            return content
        except Exception as e:
            logging.error(f"Groq API completion failure: {str(e)}")
            raise LLMException(f"LLM Chat Completion failed: {str(e)}")


llm_service = LLMService()
