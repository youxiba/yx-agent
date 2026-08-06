# coding=utf-8
import uuid
from pathlib import Path
from django.conf import settings


class LocalFileStorage:
    """Phase 3 文档暂存（本地磁盘）；Phase 7 换 StorageBackend 抽象"""

    def save(self, upload) -> str:
        target = Path(settings.KNOWLEDGE_FILE_DIR)
        target.mkdir(parents=True, exist_ok=True)
        suffix = Path(upload.name).suffix.lower()
        path = target / f"{uuid.uuid4()}{suffix}"
        with open(path, "wb") as f:
            for chunk in upload.chunks():
                f.write(chunk)
        return str(path)


file_storage = LocalFileStorage()