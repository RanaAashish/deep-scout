import logging
import sys
from typing import Optional

try:
    from rich.console import Console
    from rich.logging import RichHandler
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

def setup_logging(
    level: str = "INFO",
    verbose: bool = False,
    log_file: Optional[str] = None
):
    """
    Configure logging for the application.
    Uses RichHandler if 'rich' is installed, otherwise falls back to standard logging.
    """
    log_level = logging.DEBUG if verbose else getattr(logging, level.upper(), logging.INFO)
    
    # Root logger configuration
    handlers = []
    
    if HAS_RICH:
        console = Console()
        handlers.append(RichHandler(
            console=console,
            rich_tracebacks=True,
            markup=True,
            show_path=False # Hide path for cleaner logs in terminal
        ))
    else:
        # Fallback to standard stream handler
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        handlers.append(handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(message)s" if HAS_RICH else None,
        datefmt="[%X]" if HAS_RICH else None,
        handlers=handlers,
        force=True # Ensure our config overrides any existing ones
    )

    # Suppress noisy logs from third-party libraries
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    if HAS_RICH:
        logger.debug("Logging initialized with [bold blue]Rich[/bold blue]")
    else:
        logger.debug("Logging initialized with standard library")
