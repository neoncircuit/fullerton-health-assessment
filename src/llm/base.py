from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients used in document classification and extraction."""

    @abstractmethod
    async def classify_and_extract(self, image_content: bytes, media_type: str) -> dict:
        """Send a document image to the LLM and return parsed JSON.

        Args:
            image_content: Raw image bytes to send to the LLM.
            media_type: MIME type of the image (e.g. "image/png", "image/jpeg").

        Returns:
            A dictionary containing "document_type" and "extracted_fields".

        """
        ...
