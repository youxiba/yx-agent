# apps/chat/tests/test_pipeline.py
"""步骤 SPI 契约：四步骤均实现 valid_args + execute，builder 产出固定顺序。"""
import pytest
from application.models import Application
from chat.engine.v1.builder import build_simple_pipeline
from chat.engine.v1.steps.build_messages_step import BuildMessagesStep
from chat.engine.v1.steps.chat_step import ChatStep
from chat.engine.v1.steps.reset_problem_step import ResetProblemStep
from chat.engine.v1.steps.search_knowledge_step import SearchKnowledgeStep


def test_all_steps_have_spi():
    from chat.engine.v1.pipeline import IBaseStep
    for cls in (ResetProblemStep, SearchKnowledgeStep, BuildMessagesStep, ChatStep):
        assert issubclass(cls, IBaseStep)
        assert callable(getattr(cls, "valid_args"))
        assert callable(getattr(cls, "execute"))


@pytest.mark.django_db
def test_pipeline_build(app_factory):
    app = app_factory()
    pipe = build_simple_pipeline(app)
    assert [type(s).__name__ for s in pipe.steps] == [
        "ResetProblemStep", "SearchKnowledgeStep", "BuildMessagesStep", "ChatStep"]