# coding=utf-8
from django.db import migrations


class Migration(migrations.Migration):
    """给 embedding 补 tsvector 列 + GIN 索引（用于 keywords/blend 全文检索）"""
    dependencies = [("knowledge", "0001_initial")]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE embedding ADD COLUMN IF NOT EXISTS search_vector tsvector;",
            "ALTER TABLE embedding DROP COLUMN IF EXISTS search_vector;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_embedding_search_vector_gin ON embedding USING gin (search_vector);",
            "DROP INDEX IF EXISTS idx_embedding_search_vector_gin;",
        ),
    ]