-- 01-schema.sql: 创建数据库扩展，Schema 和基础业务表。
-- 该文件只会在postgreSQL数据卷第一次初始化时执行。

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS dispatch;

CREATE TABLE dispatch.hospital(
    hospital_id varchar(16) PRIMARY KEY,
    hospital_name varchar(128) NOT NULL UNIQUE,
    district varchar(32) NOT NULL,
    enabled boolean NOT NULL DEFAULT true
);

CREATE TABLE dispatch.alarm_case(
    case_id varchar(32) PRIMARY KEY,
    alarm_time timestamptz NOT NULL,
    district varchar(32) NOT NULL,

    --只保存模糊地址，不保存姓名、电话和精确门牌。
    address_masked text NOT NULL,

    event_type varchar(32) NOT NULL,
    chief_complaint text NOT NULL,
    case_summary text NOT NULL,
    caller_age_group varchar(16),
    caller_gender varchar(8),
    source_updated_at timestamptz NOT NULL DEFAULT now(),

    -- 预留384维向量字段，当前阶段暂时不填充。
    embedding vector(384),

    CONSTRAINT alarm_case_gender_check
        CHECK (
            caller_gender IS NULL
            OR caller_gender IN ('男','女','未知')
        )
);


CREATE TABLE dispatch.ambulance_dispatch(
    dispatch_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    case_id varchar(32)
        NOT NULL
        UNIQUE
        REFERENCES dispatch.alarm_case(case_id),

    hospital_id varchar(32)
        NOT NULL
        REFERENCES dispatch.hospital(hospital_id),

    ambulance_code_masked varchar(32) NOT NULL,
    dispatch_time timestamptz,
    arrival_time timestamptz,
    finish_time timestamptz,
    dispatch_status varchar(16) NOT NULL,

    CONSTRAINT dispatch_status_check
        CHECK (
            dispatch_status IN ('已完成', '已到达', '已派车', '已取消')
        ),

    CONSTRAINT dispatch_time_order_check
        CHECK (
            arrival_time IS NULL
            OR dispatch_time IS NULL
            OR arrival_time >= dispatch_time
        ),

    CONSTRAINT finish_time_order_check
        CHECK (
            finish_time IS NULL
            OR arrival_time IS NULL
            OR finish_time >= arrival_time
        )
);

-- 为查询条件创建条件索引

CREATE INDEX idx_alarm_case_time ON dispatch.alarm_case(alarm_time DESC);
CREATE INDEX idx_alarm_case_destrict_time ON dispatch.alarm_case(district, alarm_time DESC);
CREATE INDEX idx_alarm_case_event_time ON dispatch.alarm_case(event_type, alarm_time DESC);
CREATE INDEX idx_dispatch_hospital ON dispatch.ambulance_dispatch(hospital_id);
CREATE INDEX idx_alarm_case_summary_trgm ON dispatch.alarm_case(case_summary, gin_trgm_ops);


-- 创建查询助手唯一允许读取的统一脱敏视图。

CREATE VIEW dispatch.v_dispatch_case_search
WITH (security_barrier = true) AS 
SELECT
    c.case_id,
    c.alarm_case,
    c.district,
    c.address_masked,
    c.event_type,
    c.chief_complaint,
    c.case_summary,
    c.caller_age_group,
    c.caller_gender,

    h.hospital_id,
    h.hospital_name,

    d.ambulance_code_masked,
    d.dispatch_time,
    d.arrival_time,
    d.finish_time,
    d.dispatch_status,

    CASE
        WHEN d.dispatch_time IS NOT NULL
        THEN extract(
            epoch FROM d.dispatch_time - c.alarm_time
        )::integer
    END AS response_seconds,

    c.source_updated_at,
    c.embedding

FROM dispatch.alarm_case AS c

JOIN dispatch.ambulance_dispatch AS d
    USING(case_id)

JOIN dispatch.hospital AS h
    USING(hospital_id);

COMMENT ON VIEW dispatch.v_dispatch_case_search IS
    '智能查询助手唯一允许读取的脱敏视图；不含姓名、电话、证件号和精确门牌。';