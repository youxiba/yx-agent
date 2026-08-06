# coding=utf-8
from .events import bus, DocumentIngested, ParagraphEmbedded


def _on_document_ingested(ev: DocumentIngested):
    from ..tasks import split_document
    split_document.delay(ev.document_id)


def _on_paragraph_embedded(ev: ParagraphEmbedded):
    from ..tasks import tokenize_by_document
    tokenize_by_document.delay(ev.document_id)


def register():
    bus.on(DocumentIngested, _on_document_ingested)
    bus.on(ParagraphEmbedded, _on_paragraph_embedded)