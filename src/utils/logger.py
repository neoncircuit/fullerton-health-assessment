import logging
import logging.config
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOGGING_CONFIG_PATH = _PROJECT_ROOT / "config" / "logging_config.yaml"
_LOGS_DIR = _PROJECT_ROOT / "logs"


def _load_logging_config(config_path: Optional[Path] = None) -> None:
    """Load and apply logging configuration from a YAML file.

    Args:
        config_path: Path to the logging configuration YAML file.
            Defaults to config/logging_config.yaml relative to project root.

    Returns:
        None
    """
    import yaml

    path = config_path or _LOGGING_CONFIG_PATH
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)


if not logging.getLogger().handlers:
    _load_logging_config()


def get_logger(name: str) -> logging.Logger:
    """Return a named logger configured via the project logging config.

    Args:
        name: The name for the logger, typically __name__ of the calling module.

    Returns:
        A configured logging.Logger instance.
    """
    return logging.getLogger(name)
