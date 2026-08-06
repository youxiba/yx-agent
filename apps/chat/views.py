# apps/chat/views.py
"""聊天与会话 API（引擎 V1 线性流水线）。"""
import json
import threading

from rest_framework.views import APIView

from chat.auth import ensure_access, get_chat_application
from chat.cache import ChatInfoService
from chat.engine.v1.builder import build_simple_pipeline
from chat.engine.v1.context import PipelineContext
from chat.models import Chat, ChatRecord
from chat.sse import EventEmitter
from chat.stream import sse_response
from common.exceptions import AppApiException
from common.result import Result


class ChatView(APIView):
    """POST /api/chat/{app_id}/chat —— 主对话（SSE 流式）。"""

    def post(self, request, app_id):
        app = get_chat_application(request, app_id)
        body = json.loads(request.body or "{}")
        question = (body.get("question") or "").strip()
        if not question:
            return Result.error("问题不能为空", code=400)
        identity = body.get("client_id") or str(getattr(request.user, "id", "") or "") or "anon"
        ensure_access(app, identity)                    # 超限抛 AppChatNumOutOfBounds
        chat = self._get_or_create_chat(app, request, body)

        ctx = PipelineContext(
            question=question,
            chat_history=ChatInfoService.get_history(str(chat.id)),
            knowledge_setting=app.knowledge_setting,
            model_setting=app.model_setting,
        )
        emitter = EventEmitter()
        ctx.emitter = emitter
        # 管线在后台线程跑，边产事件边被下方生成器实时消费（真流式）
        threading.Thread(target=self._run_pipeline, args=(app, ctx), daemon=True).start()

        def generate():
            try:
                yield from emitter.stream()
            finally:
                # 流结束（或被打断）后落库 + 回写历史，保证记录完整
                self._save_record(chat, ctx)
                ChatInfoService.push_history(str(chat.id), {"role": "user", "content": question})
                ChatInfoService.push_history(str(chat.id), {"role": "assistant", "content": ctx.answer})

        return sse_response(generate())

    def _run_pipeline(self, app, ctx) -> None:
        try:
            build_simple_pipeline(app).run(ctx)
        finally:
            ctx.emitter.close()                         # 结束哨兵，防消费线程卡死

    def _get_or_create_chat(self, app, request, body) -> Chat:
        chat_id = body.get("chat_id")
        if chat_id:
            chat = Chat.objects.filter(id=chat_id, application=app, is_deleted=False).first()
            if not chat:
                raise AppApiException("会话不存在", code=404)
            return chat
        user = request.user if getattr(request, "user", None) and getattr(request.user, "is_authenticated", False) else None
        return Chat.objects.create(application=app, client_id=body.get("client_id") or "", user=user)

    def _save_record(self, chat: Chat, ctx: PipelineContext) -> ChatRecord:
        if not chat.name or chat.name == "新会话":      # 首轮用首问做会话标题
            chat.name = ctx.question[:20]
            chat.save(update_fields=["name", "update_time"])
        record = ChatRecord.objects.create(
            chat=chat, question=ctx.question, answer=ctx.answer,
            answer_text_list=[ctx.answer], reasoning_content=ctx.reasoning_content,
            tokens=ctx.usage or {}, details=ctx.details, source=ctx.source,
        )
        Chat.objects.filter(id=chat.id).update(current_chat_record_id=str(record.id))
        return record