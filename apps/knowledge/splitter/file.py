from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class File:
    """解析器输入： 支持磁盘路径或内存字节两种形态"""
    name: str
    path: str = ""   # 磁盘路径
    bytes: bytes = b""   #内存字节
    meta: dict =field(default_factory=dict)  # source_type=qa/table ,limit等

    def open_bytes(self) -> bytes:
        if self.bytes:
            return self.bytes
        with open(self.path, "rb") as f:
            return f.read()

    @property
    def suffix(self) -> str:
        """扩展名（带点，如 .xlsx）；handlers 以 file.suffix 属性方式使用"""
        return Path(self.name).suffix

    def open_workbook_source(self):
        """openpyxl 可加载的源：内存 bytes → BytesIO，否则磁盘路径"""
        import io
        if self.bytes:
            return io.BytesIO(self.bytes)
        return self.path
