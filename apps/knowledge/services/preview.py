# coding=utf-8
from common.exceptions import AppApiException
from ..splitter.file import File
from ..splitter.spi import get_handler, SplitOptions
from ..splitter.split_model import SplitModel


class PreviewService:
    """上传文件→按指定参数切分→返回分段预览（不落库）"""

    def split(self, upload, limit: int = 256) -> list[dict]:
        from ..file import file_storage
        path = file_storage.save(upload)
        try:
            file = File(name=upload.name, path=path)
            handler = get_handler(file)
            if handler is None:
                raise AppApiException(f"不支持的文件格式: {file.suffix}", code=400)
            opts = SplitOptions(limit=limit)
            raws = handler.handle(file, opts)
            return [{"title": r.title, "content": r.content, "char_length": len(r.content)} for r in raws]
        finally:
            import os
            if path and os.path.exists(path):
                os.remove(path)