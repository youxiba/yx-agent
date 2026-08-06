-- 混合检索：向量相似度 0.7 + 全文相关度 0.3，FULL OUTER JOIN 取并集
WITH vector_top AS (
    SELECT paragraph_id, (1 - (vector <=> %(q)s::vector)) AS v_score
    FROM embedding
    WHERE knowledge_id = %(k_id)s AND is_active = true
    ORDER BY vector <=> %(q)s::vector
    LIMIT LEAST(%(top_n)s * 10, 500)
), keyword_top AS (
    SELECT paragraph_id, ts_rank_cd(search_vector, websearch_to_tsquery('simple', %(q_text)s), 32) AS k_score
    FROM embedding
    WHERE search_vector @@ websearch_to_tsquery('simple', %(q_text)s)
      AND knowledge_id = %(k_id)s AND is_active = true
)
SELECT COALESCE(v.paragraph_id, k.paragraph_id) AS paragraph_id,
       COALESCE(v.v_score, 0) * 0.7 + COALESCE(k.k_score, 0) * 0.3 AS score
FROM vector_top v FULL OUTER JOIN keyword_top k ON v.paragraph_id = k.paragraph_id
ORDER BY score DESC
LIMIT %(top_n)s;