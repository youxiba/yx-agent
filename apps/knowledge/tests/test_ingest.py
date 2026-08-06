# coding=utf-8
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from knowledge.domain.states import transit, StateTransitionError, Status
from knowledge.models import Embedding, Paragraph, DocumentTask, TaskType
from knowledge.services.ingest import DocumentIngestService
from knowledge.splitter.file import File
from knowledge.splitter.spi import get_handler, SplitOptions
from knowledge.splitter.split_model import SplitModel
from .conftest import make_md_bytes, make_pdf_bytes


@pytest.mark.django_db
def test_state_machine():
    assert transit(Status.PENDING, Status.STARTED) == Status.STARTED
    assert transit(Status.STARTED, Status.SUCCESS) == Status.SUCCESS
    with pytest.raises(StateTransitionError):
        transit(Status.PENDING, Status.SUCCESS)   # 跳级非法


@pytest.mark.django_db
def test_pdf_parse():
    file = File(name="a.pdf", bytes=make_pdf_bytes())
    handler = get_handler(file)
    raws = handler.handle(file, SplitOptions())
    assert any("MaxKB" in r.content for r in raws)


@pytest.mark.django_db
def test_split_model_boundary():
    sm = SplitModel(r"^#{1,6} ", 10)
    assert sm.smart_split_paragraph("A。" * 30, 10)[0].endswith("。")


@pytest.mark.django_db
def test_end_to_end_ingest(knowledge, user, fake_gateway):
    upload = SimpleUploadedFile("demo.md", make_md_bytes(), content_type="text/markdown")
    svc = DocumentIngestService()
    doc = svc.upload(knowledge, user, upload)
    svc.split(str(doc.id))
    assert doc.paragraphs.count() >= 2
    assert doc.paragraphs.first().content
    svc.embed_document(str(doc.id))
    assert Paragraph.objects.filter(document=doc, status=Status.SUCCESS).count() == doc.paragraphs.count()
    assert Embedding.objects.filter(knowledge=knowledge).count() == doc.paragraphs.count()
    # document_task 子表记录各阶段进度
    assert DocumentTask.objects.filter(document=doc, type=TaskType.SPLIT, status=Status.SUCCESS).exists()
    assert DocumentTask.objects.filter(document=doc, type=TaskType.EMBED, status=Status.SUCCESS).exists()


@pytest.mark.django_db
def test_document_refresh_after_edit(knowledge, user, fake_gateway):
    upload = SimpleUploadedFile("d.md", b"# 标题\n旧内容。", content_type="text/markdown")
    svc = DocumentIngestService()
    doc = svc.upload(knowledge, user, upload)
    svc.split(str(doc.id))
    p = doc.paragraphs.first()
    p.content = "新内容。"
    p.save()
    svc.refresh_document(str(doc.id))
    # 段落重置为 PENDING，旧向量被删
    assert Paragraph.objects.get(id=p.id).status == Status.PENDING
    assert Embedding.objects.filter(document=doc).count() == 0