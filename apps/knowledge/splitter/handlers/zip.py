# coding=utf-8
import zipfile
from pathlib import Path
from django.conf import settings
from ..file import File
from ..spi import BaseSplitHandle, ParagraphRaw, SplitOptions, get_handler


class ZipSplitHandle(BaseSplitHandle):
    def support(self, file: File) -> bool:
        return file.suffix == ".zip"

    def get_content(self, file: File, save_image: bool = False) -> str:
        return ""

    def handle(self, file: File, opts: SplitOptions) -> list[ParagraphRaw]:
        raws: list[ParagraphRaw] = []
        with zipfile.ZipFile(file.path) as zf:
            for name in zf.namelist():
                if name.endswith("/"):      # 跳过目录项
                    continue
                data = zf.read(name)
                tmp = File(name=Path(name).name, bytes=data, meta=file.meta)
                handler = get_handler(tmp)
                if handler is not None and not isinstance(handler, ZipSplitHandle):
                    raws.extend(handler.handle(tmp, opts))
                else:
                    # 未知类型成员按文本兜底
                    text = data.decode("utf-8", errors="ignore")
                    raws.append(ParagraphRaw(title=Path(name).stem, content=text.strip()))
        return raws