#!/bin/sh

set -eu

: "${POSTGRES_USER:?POSTGRES_USER must be set}"
: "${POSTGRES_DB:?POSTGRES_DB must be set}"
: "${DEMO_READER_PASSWORD:?DEMO_READER_PASSWORD must be set}"

# 这里只打印数据库名和管理员账号，不打印密码。
printf '正在连接数据库：<%s>\n' "$POSTGRES_DB"
printf '使用管理员账号：<%s>\n' "$POSTGRES_USER"

psql \
    --set=ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --set=reader_password="$DEMO_READER_PASSWORD" <<'SQL'

SELECT format(
    'CREATE ROLE demo_reader LOGIN PASSWORD %L',
    :'reader_password'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_roles
    WHERE rolname = 'demo_reader'
) \gexec

SELECT format(
    'ALTER ROLE demo_reader PASSWORD %L',
    :'reader_password'
) \gexec

ALTER ROLE demo_reader
    SET default_transaction_read_only = on;

ALTER ROLE demo_reader
    SET statement_timeout = '5s';

ALTER ROLE demo_reader
    SET search_path = dispatch, public;

REVOKE ALL
ON SCHEMA dispatch
FROM PUBLIC;

REVOKE ALL
ON ALL TABLES IN SCHEMA dispatch
FROM PUBLIC;

SELECT format(
    'GRANT CONNECT ON DATABASE %I TO demo_reader',
    current_database()
) \gexec

GRANT USAGE
ON SCHEMA dispatch
TO demo_reader;

GRANT SELECT
ON dispatch.v_dispatch_case_search
TO demo_reader;

SQL
