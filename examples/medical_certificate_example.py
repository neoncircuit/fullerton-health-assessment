"""Example demonstrating document classification and extraction using a medical certificate.

This example processes the medical certificate from the sample data and shows
how the API extracts the required fields for this document type.

Usage:
    python examples/medical_certificate_example.py
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from src.llm.claude_client import ClaudeClient
from src.llm.utils import pdf_to_images

load_dotenv()


async def main() -> None:
    """Run classification and extraction on the medical certificate sample."""
    # Use the medical certificate from the sample data
    mc_pdf_path = (
        Path(__file__).parent.parent / "data" / "raw" / "medical_certificate.pdf"
    )

    file_bytes = mc_pdf_path.read_bytes()
    pages = pdf_to_images(file_bytes)
    image_bytes, media_type = pages[0]

    client = ClaudeClient()
    result = await client.classify_and_extract(image_bytes, media_type)

    print("Medical Certificate Processing Results")
    print("=" * 50)
    print(f"Document type: {result.get('document_type')}")
    print(f"Processing time: {result.get('processing_time', 'N/A')}")
    print("\nExtracted fields:")
    for key, value in result.get("extracted_fields", {}).items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
