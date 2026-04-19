import io
from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image
from starlette.testclient import TestClient

from src.api import app

client = TestClient(app)

FAKE_PDF_BYTES = b"%PDF-1.4 fake pdf content"


def _make_fake_png() -> bytes:
    """Create a minimal valid PNG image in memory.

    Returns:
        Raw PNG bytes.
    """
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="white")
    img.save(buf, format="PNG")
    return buf.getvalue()


FAKE_PNG_BYTES = _make_fake_png()

MOCK_RECEIPT_RESPONSE = {
    "document_type": "receipt",
    "extracted_fields": {"vendor": "Test Vendor", "total": "10.00"},
}

MOCK_MEDICAL_CERTIFICATE_RESPONSE = {
    "document_type": "medical_certificate",
    "extracted_fields": {"patient_name": "John Doe", "date": "2026-01-01"},
}

MOCK_REFERRAL_LETTER_RESPONSE = {
    "document_type": "referral_letter",
    "extracted_fields": {"referring_doctor": "Dr Smith", "specialty": "Cardiology"},
}

MOCK_UNKNOWN_TYPE_RESPONSE = {
    "document_type": "passport",
    "extracted_fields": {},
}


@patch("src.api.pdf_to_images", return_value=[(FAKE_PNG_BYTES, "image/png")])
@patch(
    "src.api.llm_client.classify_and_extract",
    new_callable=AsyncMock,
    return_value=MOCK_RECEIPT_RESPONSE,
)
def test_process_receipt_pdf(mock_classify, mock_pdf_to_images):
    """Test that uploading a PDF classified as a receipt returns 200 with the expected structure.

    Args:
        mock_classify: Mocked classify_and_extract returning receipt data.
        mock_pdf_to_images: Mocked pdf_to_images returning a fake PNG tuple.
    """
    response = client.post(
        "/ocr", files={"file": ("receipt.pdf", FAKE_PDF_BYTES, "application/pdf")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "receipt"
    assert "total_time" in body
    assert isinstance(body["total_time"], float)
    assert body["finalJson"] == MOCK_RECEIPT_RESPONSE["extracted_fields"]


@patch("src.api.pdf_to_images", return_value=[(FAKE_PNG_BYTES, "image/png")])
@patch(
    "src.api.llm_client.classify_and_extract",
    new_callable=AsyncMock,
    return_value=MOCK_MEDICAL_CERTIFICATE_RESPONSE,
)
def test_process_medical_certificate(mock_classify, mock_pdf_to_images):
    """Test that uploading a PDF classified as a medical_certificate returns 200 with correct fields.

    Args:
        mock_classify: Mocked classify_and_extract returning medical_certificate data.
        mock_pdf_to_images: Mocked pdf_to_images returning a fake PNG tuple.
    """
    response = client.post(
        "/ocr", files={"file": ("mc.pdf", FAKE_PDF_BYTES, "application/pdf")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "medical_certificate"
    assert body["finalJson"] == MOCK_MEDICAL_CERTIFICATE_RESPONSE["extracted_fields"]


@patch("src.api.pdf_to_images", return_value=[(FAKE_PNG_BYTES, "image/png")])
@patch(
    "src.api.llm_client.classify_and_extract",
    new_callable=AsyncMock,
    return_value=MOCK_REFERRAL_LETTER_RESPONSE,
)
def test_process_referral_letter(mock_classify, mock_pdf_to_images):
    """Test that uploading a PDF classified as a referral_letter returns 200 with correct fields.

    Args:
        mock_classify: Mocked classify_and_extract returning referral_letter data.
        mock_pdf_to_images: Mocked pdf_to_images returning a fake PNG tuple.
    """
    response = client.post(
        "/ocr", files={"file": ("referral.pdf", FAKE_PDF_BYTES, "application/pdf")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "referral_letter"
    assert body["finalJson"] == MOCK_REFERRAL_LETTER_RESPONSE["extracted_fields"]


def test_no_file_returns_400():
    """Test that a POST request without a file returns 400 with file_missing error."""
    response = client.post("/ocr")

    assert response.status_code == 400
    assert response.json() == {"error": "file_missing"}


@patch("src.api.pdf_to_images", return_value=[(FAKE_PNG_BYTES, "image/png")])
@patch(
    "src.api.llm_client.classify_and_extract",
    new_callable=AsyncMock,
    return_value=MOCK_UNKNOWN_TYPE_RESPONSE,
)
def test_unsupported_document_type_returns_422(mock_classify, mock_pdf_to_images):
    """Test that an unrecognised document_type from the LLM returns 422 with unsupported_document_type error.

    Args:
        mock_classify: Mocked classify_and_extract returning an unknown document type.
        mock_pdf_to_images: Mocked pdf_to_images returning a fake PNG tuple.
    """
    response = client.post(
        "/ocr", files={"file": ("doc.pdf", FAKE_PDF_BYTES, "application/pdf")}
    )

    assert response.status_code == 422
    assert response.json() == {"error": "unsupported_document_type"}


@patch("src.api.pdf_to_images", return_value=[(FAKE_PNG_BYTES, "image/png")])
@patch(
    "src.api.llm_client.classify_and_extract",
    new_callable=AsyncMock,
    side_effect=RuntimeError("LLM failure"),
)
def test_internal_error_returns_500(mock_classify, mock_pdf_to_images):
    """Test that an unhandled exception from the LLM client returns 500 with internal_server_error error.

    Args:
        mock_classify: Mocked classify_and_extract that raises RuntimeError.
        mock_pdf_to_images: Mocked pdf_to_images returning a fake PNG tuple.
    """
    response = client.post(
        "/ocr", files={"file": ("broken.pdf", FAKE_PDF_BYTES, "application/pdf")}
    )

    assert response.status_code == 500
    assert response.json() == {"error": "internal_server_error"}


@patch.dict("os.environ", {"LLM_PROVIDER": "gemini"}, clear=False)
def test_provider_factory_respects_env_var():
    """Test that setting LLM_PROVIDER=gemini creates a GeminiClient instance.

    Args:
        None.
    """
    from src.llm.provider_factory import create_llm_client

    gemini_client = create_llm_client("gemini")
    from src.llm.gemini_client import GeminiClient

    assert isinstance(gemini_client, GeminiClient)


@patch.dict("os.environ", {"LLM_PROVIDER": "claude"}, clear=False)
def test_provider_factory_creates_claude():
    """Test that setting LLM_PROVIDER=claude creates a ClaudeClient instance.

    Args:
        None.
    """
    from src.llm.provider_factory import create_llm_client

    claude_client = create_llm_client("claude")
    from src.llm.claude_client import ClaudeClient

    assert isinstance(claude_client, ClaudeClient)


def test_provider_factory_raises_on_unknown():
    """Test that requesting an unknown provider raises ValueError.

    Args:
        None.
    """
    from src.llm.provider_factory import create_llm_client

    with pytest.raises(ValueError, match="Unknown provider"):
        create_llm_client("nonexistent")
