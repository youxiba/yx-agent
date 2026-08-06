# apps/chat/engine/v1/steps/reset_problem_step.py
"""问题优化步骤：规整用户问题（去空白/截断）；LLM 改写由 Phase 5 question-node 承担。"""
from chat.sse import EVT_NODE_END, EVT_NODE_START, SSEEvent
from common.exceptions import AppApiException
from ..context import PipelineContext
from ..pipeline import IBaseStep

MAX_QUESTION_LEN = 2000


class ResetProblemStep(IBaseStep):
    step_type = "reset_problem"

    def valid_args(self, ctx: PipelineContext) -> None:
        if not ctx.question or not ctx.question.strip():
            raise AppApiException("问题不能为空", code=400)

    def execute(self, ctx: PipelineContext) -> None:
        # 规整：合并连续空白、截断超长问题
        ctx.optimized_question = " ".join(ctx.question.split())[:MAX_QUESTION_LEN]
        if ctx.emitter:
            ctx.emitter.emit(SSEEvent(EVT_NODE_START, node_type="reset-problem-node"))
            ctx.emitter.emit(SSEEvent(EVT_NODE_END, node_type="reset-problem-node"))