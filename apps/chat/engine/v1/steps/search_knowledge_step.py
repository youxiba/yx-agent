# apps/chat/engine/v1/steps/search_knowledge_step.py
"""知识库检索步骤：调用 Phase 3 检索引擎，产出命中段落并判定直接返回。"""
from chat.sse import EVT_NODE_END, EVT_NODE_START, SSEEvent
from knowledge.services.search import knowledge_search   # Phase 3 检索引擎入口
from ..context import PipelineContext
from ..pipeline import IBaseStep


class SearchKnowledgeStep(IBaseStep):
    step_type = "search_knowledge"

    def execute(self, ctx: PipelineContext) -> None:
        ks = ctx.knowledge_setting or {}
        knowledge_ids = ks.get("knowledge_ids") or []
        if not knowledge_ids:
            return                                      # 未挂知识库：跳过检索，不产段落
        if ctx.emitter:
            ctx.emitter.emit(SSEEvent(EVT_NODE_START, node_id="search", node_type="search-knowledge-node"))

        hits = knowledge_search(
            query_text=ctx.optimized_question,
            knowledge_ids=knowledge_ids,
            mode=ks.get("search_mode", "embedding"),
            top_n=ks.get("top_n", 3),
            similarity=ks.get("similarity", 0.3),
        )
        # 命中段落：优先 to_dict（Hit 对象），否则兼容 dict/SimpleNamespace（测试 fake）
        ctx.paragraph_list = [h.to_dict() if hasattr(h, "to_dict") else vars(h) for h in hits]
        ctx.source = ctx.paragraph_list
        # 直接返回判定：最高相似度 ≥ 阈值则后续跳过 LLM（Day 6 在 ChatStep 生效）
        direct_th = ks.get("direct_return_similarity", 0.9)
        ctx.directly_return = bool(ctx.paragraph_list) and \
            (ctx.paragraph_list[0].get("similarity", 0) >= direct_th)

        if ctx.emitter:
            ctx.emitter.emit(SSEEvent(EVT_NODE_END, node_id="search", node_type="search-knowledge-node"))