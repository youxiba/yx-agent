import hashlib
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps"))
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """12 factor 配置：环境变量带"""
    model_config = {"env_file":".env","env_prefix":"YX_"}
    debug: bool = False
    secret_key: str = "dev-insecure-change-me"
    db_name: str = "yx-agent"
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    model_credential_key: str = "0123456789abcdef0123456789abcdef"
    local_model_host: str = "127.0.0.1"
    local_model_port: int = 11636

settings = Settings()

SECRET_KEY = settings.secret_key
DEBUG = settings.debug
ALLOWED_HOSTS = ["*"]
STATIC_URL = "static/"

INSTALLED_APPS = [
    "django.contrib.auth",          # 需要（identity.User 继承 AbstractUser，且 AUTH_USER_MODEL 指向它）
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "common.apps.CommonConfig",
    "identity.apps.IdentityConfig",
    "rest_framework_simplejwt.token_blacklist",
    "model_platform.apps.ModelPlatformConfig",
    "knowledge.apps.KnowledgeConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "common.middleware.AuthenticationMiddleware",

]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.debug",
        ]}
    }
]

WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default":{
    "ENGINE":"django.db.backends.postgresql",
    "NAME":settings.db_name,
    "HOST":settings.db_host,
    "PORT":settings.db_port,
    "USER":settings.db_user,
    "PASSWORD":settings.db_password,
}}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # 旧版 Redis(<6) 不支持 RESP3 的 HELLO 命令，强制走 RESP2
            "CONNECTION_POOL_KWARGS": {"protocol": 2},
        },
    }
}

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "common.exceptions.handle_exception",
    # 复用中间件解析的用户，避免 DRF 把 request.user 覆盖为 AnonymousUser
    "DEFAULT_AUTHENTICATION_CLASSES": ["common.auth.backends.MiddlewareUserAuthentication"],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":
        __import__("datetime").timedelta(minutes=settings.access_token_minutes),
    "REFRESH_TOKEN_LIFETIME":
        __import__("datetime").timedelta(days=settings.refresh_token_days)
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher",
                    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher"]

# AUTH_USER_MODEL 在第 3 天创建 User 模型后放开
AUTH_USER_MODEL = "identity.User"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler", "level": "DEBUG"},
    },
    "loggers": {
        # 应用日志（含 common.mail 的 [MAIL] 验证码输出）打到控制台
        "maxkb": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
MODEL_CREDENTIAL_KEY = hashlib.sha256(settings.model_credential_key.encode()).digest()

KNOWLEDGE_FILE_DIR=str(Path(BASE_DIR) /"var" / "knowledge_files")
LOCAL_MODEL_URL ="http://127.0.0.1:11636"

# --- Celery ---
CELERY_BROKER_URL = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ALWAYS_EAGER = settings.debug          # 开发期本地执行，便于调试
CELERY_ONCE_REDIS_URL = CELERY_BROKER_URL
