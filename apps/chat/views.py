# apps/chat/views.py
"""聊天与会话 API（引擎 V1 线性流水线）。"""
import json
import threading

from django.core.paginator import Paginator
from django.utils import timezone
from rest_framework.views import APIView

from chat.auth import ensure_access, get_chat_application
from chat.cache import ChatInfoService
from chat.engine.v1.builder import build_simple_pipeline
from chat.engine.v1.context import PipelineContext
from chat.models import Chat, ChatRecord
from chat.serializers import ChatRecordSerializer, ChatSerializer
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


class ChatOpenView(APIView):
    """POST /api/chat/{app_id}/chat/open —— 创建/返回会话。"""

    def post(self, request, app_id):
        app = get_chat_application(request, app_id)
        client_id = request.data.get("client_id") or ""
        user = request.user if getattr(request, "user", None) and getattr(request.user, "is_authenticated", False) else None
        chat = Chat.objects.create(application=app, client_id=client_id, user=user,
                                   name=request.data.get("name", "新会话"))
        return Result.success(ChatSerializer(chat).data)


class ChatListView(APIView):
    """GET /api/chat/{app_id}/chat/list —— 会话列表（侧栏用，支持搜索/分页）。"""

    def get(self, request, app_id):
        app = get_chat_application(request, app_id)
        qs = Chat.objects.filter(application=app, is_deleted=False)
        if client_id := request.query_params.get("client_id"):
            qs = qs.filter(client_id=client_id)
        if keyword := request.query_params.get("keyword"):
            qs = qs.filter(name__icontains=keyword)
        qs = qs.order_by("-update_time")
        page = int(request.query_params.get("page", 1))
        size = int(request.query_params.get("page_size", 20))
        pg = Paginator(qs, size)
        items = [ChatSerializer(c).data for c in pg.page(min(page, pg.num_pages or 1))]
        return Result.success({"items": items, "total": pg.count})


class ChatHistoryView(APIView):
    """GET /api/chat/{app_id}/chat/history?chat_id=&page= —— 会话记录分页（按时间正序）。"""

    def get(self, request, app_id):
        app = get_chat_application(request, app_id)
        chat = self._get_chat(app, request.query_params.get("chat_id"))
        page = int(request.query_params.get("page", 1))
        size = int(request.query_params.get("page_size", 10))
        qs = chat.records.order_by("create_time")
        pg = Paginator(qs, size)
        items = [ChatRecordSerializer(r).data for r in pg.page(min(page, pg.num_pages or 1))]
        return Result.success({"items": items, "total": pg.count, "page": page, "page_size": size})

    def _get_chat(self, app, chat_id):
        chat = Chat.objects.filter(id=chat_id, application=app, is_deleted=False).first()
        if not chat:
            raise AppApiException("会话不存在", code=404)
        return chat


class ChatDetailView(APIView):
    """GET /api/chat/{app_id}/chat_record/{record_id} —— 单条记录详情。"""

    def get(self, request, app_id, record_id):
        app = get_chat_application(request, app_id)
        rec = ChatRecord.objects.filter(id=record_id, chat__application=app).first()
        if not rec:
            raise AppApiException("记录不存在", code=404)
        return Result.success(ChatRecordSerializer(rec).data)

class ChatUpdateView(APIView):
    """PUT /api/chat/{app_id}/chat/{chat_id} —— 改标题/摘要。"""

    def put(self, request, app_id, chat_id):
        app = get_chat_application(request, app_id)
        chat = Chat.objects.filter(id=chat_id, application=app, is_deleted=False).first()
        if not chat:
            raise AppApiException("会话不存在", code=404)
        fields = []
        if "name" in request.data:
            chat.name, fields = request.data["name"], fields + ["name"]
        if "abstract" in request.data:
            chat.abstract, fields = request.data["abstract"], fields + ["abstract"]
        fields.append("update_time")
        chat.save(update_fields=fields)
        return Result.success(ChatSerializer(chat).data)


class ChatDeleteView(APIView):
    """DELETE /api/chat/{app_id}/chat/{chat_id}/delete —— 逻辑删除。"""

    def delete(self, request, app_id, chat_id):
        app = get_chat_application(request, app_id)
        Chat.objects.filter(id=chat_id, application=app, is_deleted=False).update(
            is_deleted=True, delete_time=timezone.now())
        return Result.success()


class ChatVoteView(APIView):
    """PUT /api/chat/{app_id}/chat_record/{record_id}/vote —— 点赞/点踩（含原因）。"""

    def put(self, request, app_id, record_id):
        app = get_chat_application(request, app_id)
        rec = ChatRecord.objects.filter(id=record_id, chat__application=app).first()
        if not rec:
            raise AppApiException("记录不存在", code=404)
        rec.vote_status = request.data.get("vote_status") or ChatRecord.VoteStatus.UN_VOTE
        rec.vote_reason = request.data.get("vote_reason", "") or ""
        rec.save(update_fields=["vote_status", "vote_reason", "update_time"])
        return Result.success(ChatRecordSerializer(rec).data)


class ChatShareView(APIView):
    """GET /api/chat/{app_id}/chat_record/{record_id}/share —— 分享信息（简化版，无签名 token）。"""

    def get(self, request, app_id, record_id):
        app = get_chat_application(request, app_id)
        rec = ChatRecord.objects.filter(id=record_id, chat__application=app).first()
        if not rec:
            raise AppApiException("记录不存在", code=404)
        return Result.success({"share_id": str(rec.id), "question": rec.question, "answer": rec.answer})