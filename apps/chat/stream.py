# apps/chat/stream.py
"""SSE 响应封装：统一响应头 + 生成器 → StreamingHttpResponse。"""
from django.http import StreamingHttpResponse


def sse_response(generator) -> StreamingHttpResponse:
    """包装任意帧生成器为标准 SSE 响应。"""
    resp = StreamingHttpResponse(generator, content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"                  # 禁止缓存
    resp["X-Accel-Buffering"] = "no"                    # 关闭 nginx 缓冲，保证实时
    resp["Connection"] = "keep-alive"
    return resp