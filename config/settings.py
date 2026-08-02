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
        "BACKEND":"django_redis.cache.RedisCache",
        "LOCATION":f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
    }
}

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER":"common.exceptions.handle_exception",
    "DEFAULT_AUTHENTICATION_CLASSES":[]
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
