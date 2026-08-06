-- 单知识库向量召回：WHERE knowledge_id = %(k_id)s 命中 partial HNSW 索引
-- 先宽召回（top_n*10）再按相似度精排，避免 HNSW 近似召回漏掉边界
WITH vector_top AS (
    SELECT paragraph_id, vector <=> %(q)s::vector AS distance
    FROM embedding
    WHERE knowledge_id = %(k_id)s AND is_active = true
    ORDER BY vector <=> %(q)s::vector
    LIMIT LEAST(%(top_n)s * 10, 500)
)
SELECT paragraph_id, (1 - distance) AS score
FROM vector_top
WHERE (1 - distance) > %(similarity)s
ORDER BY score DESC
LIMIT %(top_n)s;