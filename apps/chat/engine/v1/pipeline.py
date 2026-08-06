# apps/chat/engine/v1/pipeline.py
"""线性执行链路（引擎 V1）：严格线性，为 Phase 5 引擎 V2 保留统一 step 形态。"""
from abc import ABC, abstractmethod

from .context import PipelineContext


class IBaseStep(ABC):
    """步骤 SPI：valid_args 校验 + execute 执行。"""
    step_type: str = ""

    def valid_args(self, ctx: PipelineContext) -> None:
        """执行前校验（可选覆盖）；参数非法抛 AppApiException。"""

    @abstractmethod
    def execute(self, ctx: PipelineContext) -> None:
        """执行步骤，读/写 ctx。"""


class Pipeline:
    """严格线性执行器。"""

    def __init__(self, steps: list[IBaseStep]):
        self.steps = steps

    def run(self, ctx: PipelineContext) -> PipelineContext:
        for step in self.steps:
            step.valid_args(ctx)
            step.execute(ctx)
        return ctx