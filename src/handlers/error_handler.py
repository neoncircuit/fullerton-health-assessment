import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class FileMissingError(HTTPException):
    """Raised when no file is provided in the upload request."""

    def __init__(self) -> None:
        super().__init__(status_code=400, detail="file_missing")


class UnsupportedDocumentError(HTTPException):
    """Raised when the uploaded document type cannot be classified."""

    def __init__(self) -> None:
        super().__init__(status_code=422, detail="unsupported_document_type")


class InternalServerError(HTTPException):
    """Raised when an unhandled internal error occurs."""

    def __init__(self) -> None:
        super().__init__(status_code=500, detail="internal_server_error")


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application.

    Registers handlers for FileMissingError, UnsupportedDocumentError,
    InternalServerError, and a catch-all Exception handler.

    Args:
        app: The FastAPI application instance to register handlers on.

    Returns:
        None
    """

    @app.exception_handler(FileMissingError)
    async def file_missing_handler(
        request: object, exc: FileMissingError
    ) -> JSONResponse:
        """Handle FileMissingError by returning a 400 JSON response.

        Args:
            request: The incoming request object.
            exc: The caught FileMissingError instance.

        Returns:
            JSONResponse with status 400 and error detail.
        """
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    @app.exception_handler(UnsupportedDocumentError)
    async def unsupported_document_handler(
        request: object, exc: UnsupportedDocumentError
    ) -> JSONResponse:
        """Handle UnsupportedDocumentError by returning a 422 JSON response.

        Args:
            request: The incoming request object.
            exc: The caught UnsupportedDocumentError instance.

        Returns:
            JSONResponse with status 422 and error detail.
        """
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    @app.exception_handler(InternalServerError)
    async def internal_server_error_handler(
        request: object, exc: InternalServerError
    ) -> JSONResponse:
        """Handle InternalServerError by returning a 500 JSON response.

        Args:
            request: The incoming request object.
            exc: The caught InternalServerError instance.

        Returns:
            JSONResponse with status 500 and error detail.
        """
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: object, exc: Exception
    ) -> JSONResponse:
        """Handle any unhandled exception by logging and returning a 500 JSON response.

        Args:
            request: The incoming request object.
            exc: The caught Exception instance.

        Returns:
            JSONResponse with status 500 and internal_server_error detail.
        """
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error"},
        )
