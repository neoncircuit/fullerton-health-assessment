import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml
from openai import AsyncOpenAI

from src.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_CONFIG_PATH = PROJECT_ROOT / "config" / "model_config.yaml"
PROMPT_TEMPLATES_PATH = PROJECT_ROOT / "config" / "prompt_templates.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary.

    Args:
        path: Path to the YAML file.

    Returns:
        A dictionary representing the parsed YAML contents.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
    """
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class GeminiClient(BaseLLMClient):
    """Google Gemini model client for document classification and extraction via OpenAI-compatible API.

    Reads provider-specific configuration from config/model_config.yaml and the
    system prompt from config/prompt_templates.yaml. Requires the GEMINI_API_KEY
    environment variable to be set.
    """

    def __init__(self) -> None:
        """Initialise GeminiClient from the provider config and prompt template."""
        model_cfg = _load_yaml(MODEL_CONFIG_PATH)
        prompt_cfg = _load_yaml(PROMPT_TEMPLATES_PATH)

        provider_cfg = model_cfg["providers"]["gemini"]
        self.model_name: str = provider_cfg["model"]["name"]
        self.max_tokens: int = provider_cfg["model"]["max_tokens"]
        self.temperature: float = provider_cfg["model"]["temperature"]
        self.system_prompt: str = prompt_cfg["system_prompt"]
        self.timeout: int = provider_cfg["timeout"]
        self.max_retries: int = provider_cfg["max_retries"]

        api_key_env: str = provider_cfg["api_key_env"]
        self.api_key: str = os.environ.get(api_key_env, "")
        self.base_url: str = provider_cfg.get(
            "base_url", "https://generativelanguage.googleapis.com/v1beta/openai/"
        )

    async def classify_and_extract(self, image_content: bytes, media_type: str) -> dict:
        """Send a document image to the Gemini API and return the parsed classification and extraction JSON.

        Args:
            image_content: Raw image bytes of the document page.
            media_type: MIME type of the image (e.g. "image/png", "image/jpeg").

        Returns:
            A dictionary with "document_type" and "extracted_fields".

        Raises:
            openai.APIError: If the Gemini API call fails.
            ValueError: If the response cannot be parsed as valid JSON.
        """
        import base64

        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

        image_data = base64.standard_b64encode(image_content).decode("utf-8")

        try:
            response = await client.chat.completions.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}",
                                },
                            },
                            {
                                "type": "text",
                                "text": "Please classify this document and extract all relevant fields.",
                            },
                        ],
                    },
                ],
            )
        except Exception as exc:
            logger.error("Gemini API error during classify_and_extract: %s", exc)
            raise RuntimeError(
                f"Gemini API call failed for model '{self.model_name}': {exc}"
            ) from exc

        response_text: str = response.choices[0].message.content

        # Strip markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as exc:
            logger.error(
                "Failed to parse Gemini response as JSON: %s", response_text[:200]
            )
            raise ValueError("Gemini response could not be parsed as valid JSON.") from exc
