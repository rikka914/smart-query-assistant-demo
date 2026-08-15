-- demo_queries.sql
-- 智能数据查询助手的典型查询示例。
-- 所有查询只允许访问统一脱敏视图。


-- =========================================================
-- 查询1：最近24小时各医院的派车数量
-- =========================================================

SELECT
    hospital_name,
    count(*) AS dispatch_count
FROM dispatch.v_dispatch_case_search
WHERE alarm_time >=now() - interval '24 hours'
GROUP BY hospital_name
ORDER BY dispatch_count DESC;

-- =========================================================
-- 查询2：最近30天各区域的平均响应时间
-- =========================================================

SELECT
    district,
    count(*) AS case_count,
    round(avg(response_seconds)) AS avg_response_seconds
FROM dispatch.v_dispatch_case_search
WHERE alarm_time >= now() - interval '30 days'
GROUP BY district
ORDER BY avg_response_seconds ;

-- =========================================================
-- 查询3：最近30天派车超过5分钟的记录
-- =========================================================

SELECT
    case_id,
    alarm_time,
    district,
    hospital_name,
    event_type,
    chief_complaint,
    dispatch_seconds
FROM dispatch.v_dispatch_case_search
WHERE alarm_time >= now() - interval '30 days'
  AND dispatch_seconds > 300
ORDER BY dispatch_seconds DESC
LIMIT 20;


-- =========================================================
-- 查询4：查找描述相似的警情
-- =========================================================

SELECT
    case_id,
    alarm_time,
    district,
    case_summary,

    round(
        similarity(
            case_summary,
            '老人胸闷出冷汗意识模糊'
        )::numeric,
        3
    ) AS similarity

FROM dispatch.v_dispatch_case_search

WHERE case_summary % '老人胸闷出冷汗意识模糊'

ORDER BY similarity(
    case_summary,
    '老人胸闷出冷汗意识模糊'
) DESC

LIMIT 10;

-- =========================================================
-- 查询5：未来接入Embedding模型后使用的向量查询模板
-- 当前embedding字段为空，所以暂时不要执行
-- =========================================================

-- SELECT
--     case_id,
--     case_summary,
--     1 - (embedding <=> :query_vector) AS similarity
-- FROM dispatch.v_dispatch_case_search
-- WHERE embedding IS NOT NULL
-- ORDER BY embedding <=> :query_vector
-- LIMIT 10;