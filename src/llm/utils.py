import base64
import io

from pdf2image import convert_from_bytes


def pdf_to_images(pdf_bytes: bytes) -> list[tuple[bytes, str]]:
    """Convert a PDF document into a list of PNG image byte tuples.

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        A list of (image_bytes, "image/png") tuples, one per page.

    Raises:
        ValueError: If the conversion fails (e.g. poppler not installed).
    """
    try:
        images = convert_from_bytes(pdf_bytes)
    except Exception as exc:
        raise ValueError(
            "Failed to convert PDF to images. Ensure poppler is installed and the PDF is valid."
        ) from exc

    results: list[tuple[bytes, str]] = []
    for image in images:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        results.append((buffer.getvalue(), "image/png"))
    return results


def encode_image_base64(image_bytes: bytes) -> str:
    """Encode raw image bytes as a base64 string.

    Args:
        image_bytes: Raw image bytes to encode.

    Returns:
        A base64-encoded string representation of the image bytes.
    """
    return base64.b64encode(image_bytes).decode("utf-8")
