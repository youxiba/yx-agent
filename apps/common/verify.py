import random
from .cache import cache_get,cache_set


_CODE_TTL = 300

def send_verify_code(email: str) -> str:
    code = f"{random.randint(100000,999999)}"
    cache_set(f"verify:{email}", code,ttl=_CODE_TTL)
    from .mail import mail_sender
    mail_sender.send(email,"验证码",f"你的验证码是{code},5分钟内有效")

    return code

def check_verify_code(email: str, code: str) -> bool:
    return cache_get(f"verify:{email}") == code

