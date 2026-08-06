# coding=utf-8
from django.db import connection


class Pg:
    """RAW SQL 助手：返回 dict 行 / 执行无返回"""

    def raw(self, sql: str, params: dict) -> list[dict]:
        with connection.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description] if cur.description else []
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def execute(self, sql: str, params: list | None = None) -> None:
        with connection.cursor() as cur:
            cur.execute(sql, params or [])


db = Pg()