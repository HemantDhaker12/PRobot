import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class PRobotException(Exception):
    """Base exception class for all PRobot errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DatabaseException(PRobotException):
    """Exception raised for database-related failures."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class GitHubException(PRobotException):
    """Exception raised when GitHub API interaction fails."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, status_code=status_code)


class LLMException(PRobotException):
    """Exception raised when Groq API or LLM operations fail."""

    def __init__(self, message: str):
        super().__init__(message, status_code=502)


class VectorStoreException(PRobotException):
    """Exception raised when ChromaDB operations fail."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers on the FastAPI application instance.
    """

    @app.exception_handler(PRobotException)
    async def probot_exception_handler(request: Request, exc: PRobotException):
        logging.error(f"Exception on {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                },
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logging.critical(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "type": "UnhandledException",
                    "message": "An unexpected error occurred.",
                },
            },
        )
