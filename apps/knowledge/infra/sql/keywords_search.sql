-- 全文检索：ts_rank_cd 排序 + websearch_to_tsquery（'simple' 配置不分词，兼容中文）
SELECT paragraph_id,
       ts_rank_cd(search_vector, websearch_to_tsquery('simple', %(q)s), 32) AS score
FROM embedding
WHERE search_vector @@ websearch_to_tsquery('simple', %(q)s)
  AND knowledge_id = %(k_id)s AND is_active = true
ORDER BY score DESC
LIMIT %(top_n)s;