import json
import logging
import os
from pathlib import Path
from typing import Any

import anthropic
import yaml

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


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude-based LLM client for document classification and extraction.

    Reads provider-specific configuration from config/model_config.yaml and the
    system prompt from config/prompt_templates.yaml. Requires the ANTHROPIC_API_KEY
    environment variable to be set.
    """

    def __init__(self) -> None:
        """Initialise ClaudeClient from the provider config and prompt template."""
        model_cfg = _load_yaml(MODEL_CONFIG_PATH)
        prompt_cfg = _load_yaml(PROMPT_TEMPLATES_PATH)

        provider_cfg = model_cfg["providers"]["claude"]
        self.model_name: str = provider_cfg["model"]["name"]
        self.max_tokens: int = provider_cfg["model"]["max_tokens"]
        self.temperature: float = provider_cfg["model"]["temperature"]
        self.system_prompt: str = prompt_cfg["system_prompt"]
        self.timeout: int = provider_cfg["timeout"]
        self.max_retries: int = provider_cfg["max_retries"]

        api_key_env: str = provider_cfg["api_key_env"]
        self.api_key: str = os.environ.get(api_key_env, "")

    async def classify_and_extract(self, image_content: bytes, media_type: str) -> dict:
        """Send a document image to Claude and return the parsed classification and extraction JSON.

        Args:
            image_content: Raw image bytes of the document page.
            media_type: MIME type of the image (e.g. "image/png", "image/jpeg").

        Returns:
            A dictionary with "document_type" and "extracted_fields".

        Raises:
            anthropic.APIError: If the Anthropic API call fails.
            ValueError: If the response cannot be parsed as valid JSON.
        """
        import base64

        client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            base_url="https://api.anthropic.com",
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

        image_data = base64.standard_b64encode(image_content).decode("utf-8")

        try:
            response = await client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Please classify this document and extract all relevant fields.",
                            },
                        ],
                    }
                ],
            )
        except anthropic.APIError as exc:
            logger.error("Anthropic API error during classify_and_extract: %s", exc)
            raise RuntimeError(
                f"Anthropic API call failed for model '{self.model_name}': {exc}"
            ) from exc

        response_text: str = response.content[0].text

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
                "Failed to parse Claude response as JSON: %s", response_text[:200]
            )
            raise ValueError(
                "Claude response could not be parsed as valid JSON."
            ) from exc
