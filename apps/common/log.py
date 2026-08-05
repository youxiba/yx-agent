import logging
import re
from pydoc import text

logger = logging.getlogger("yx")

_SENSITIVE = re.compile(r'("?(?:api_key | password| secret)"?\s*[:=]\s*")([^"]+)')

def sanitize(text: str)-> str:
    """把日志/异常里的api_key/password打码，防止凭据进日志"""
    return _SENSITIVE.sub(lambda m: f"{m.group(1)}***",text)

def log_warn_credential(content:str, text:str) -> None:
    logger.warning("%s: %s", content,sanitize(text))



