import logging
import time

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile

from src.handlers.error_handler import (
    FileMissingError,
    InternalServerError,
    UnsupportedDocumentError,
    register_exception_handlers,
)
from src.llm.provider_factory import create_llm_client
from src.llm.utils import pdf_to_images

load_dotenv()

logger = logging.getLogger(__name__)

VALID_DOCUMENT_TYPES = {"receipt", "medical_certificate", "referral_letter"}

app = FastAPI(title="Fullerton Health OCR API", version="1.0.0")
register_exception_handlers(app)

llm_client = create_llm_client()


def _get_media_type(filename: str) -> str:
    """Determine the MIME type based on file extension.

    Args:
        filename: Name of the uploaded file.

    Returns:
        A MIME type string (e.g. "application/pdf", "image/png").
    """
    ext = filename.lower().rsplit(".", maxsplit=1)[-1] if "." in filename else ""
    mime_map = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    return mime_map.get(ext, "application/octet-stream")


@app.post("/ocr")
async def process_document(file: UploadFile | None = None) -> dict:
    """Accept a document upload, classify it, extract structured fields, and return JSON.

    Args:
        file: An uploaded file (PDF or image) via multipart/form-data.

    Returns:
        A dict with "document_type", "total_time", and "finalJson".

    Raises:
        FileMissingError: If no file is provided in the request.
        UnsupportedDocumentError: If the document type is not recognised.
        InternalServerError: If any unhandled exception occurs.
    """
    try:
        if not file or not file.filename:
            raise FileMissingError()

        file_bytes = await file.read()
        media_type = _get_media_type(file.filename)

        logger.info(
            "Received file: %s (%s, %d bytes)", file.filename, media_type, len(file_bytes)
        )

        if media_type == "application/pdf":
            pages = pdf_to_images(file_bytes)
            image_bytes, img_mime = pages[0]
        else:
            image_bytes = file_bytes
            img_mime = media_type

        start_time = time.time()

        result = await llm_client.classify_and_extract(image_bytes, img_mime)

        elapsed = round(time.time() - start_time, 2)

        document_type = result.get("document_type", "").strip().lower()

        if document_type not in VALID_DOCUMENT_TYPES:
            logger.warning("Unrecognised document_type from LLM: %s", document_type)
            raise UnsupportedDocumentError()

        extracted_fields = result.get("extracted_fields", {})

        return {
            "document_type": document_type,
            "total_time": elapsed,
            "finalJson": extracted_fields,
        }
    except (FileMissingError, UnsupportedDocumentError):
        raise
    except Exception as e:
        logger.error("Unhandled exception in process_document: %s", e, exc_info=True)
        raise InternalServerError()
