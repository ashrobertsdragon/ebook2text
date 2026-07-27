from ._logger import logger, set_logger
from .ai_providers import OCRProvider, get_ocr_provider
from .convert_file import convert_file
from .VERSION import __version__

__version__ = __version__
__all__ = [
    "OCRProvider",
    "convert_file",
    "get_ocr_provider",
    "logger",
    "set_logger",
]
