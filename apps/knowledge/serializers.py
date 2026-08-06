# coding=utf-8
from rest_framework import serializers
from .models import Knowledge, KnowledgeFolder, Document, Paragraph, Problem, Termbase, Term


class KnowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Knowledge
        fields = ["id", "name", "description", "embedding_model_id", "vector_type",
                  "index_name", "type", "folder_id", "workspace_id", "user_id", "meta", "create_time", "update_time"]
        read_only_fields = ["id", "user_id", "create_time", "update_time"]


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeFolder
        fields = ["id", "knowledge_id", "parent_id", "name", "create_time"]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "knowledge_id", "folder_id", "name", "type", "char_length",
                  "para_count", "status", "meta", "create_time", "update_time"]
        read_only_fields = ["id", "create_time", "update_time"]


class ParagraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paragraph
        fields = ["id", "document_id", "knowledge_id", "title", "content", "status",
                  "is_active", "keywords", "version", "create_time", "update_time"]
        read_only_fields = ["id", "knowledge_id", "version", "create_time", "update_time"]


class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ["id", "paragraph_id", "content", "is_active", "create_time"]


class TermbaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Termbase
        fields = ["id", "name", "workspace_id", "user_id", "is_active", "create_time", "update_time"]


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ["id", "termbase_id", "content", "is_active", "create_time"]