#!/bin/bash

# 遇到命令错误或使用未定义变量时，立即停止脚本
set -eu

# 检查查询帐号密码是否已经通过环境变量传入
: "${DEMO_READER_PASSWORD:?DEMO_READER_PASSWORD must be set}"

# 使用管理员帐号连接postgreSQL并执行权限配置
psql --set=ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" \ 
     --dbname "$POSTGRES_DB" \
     --set=reader_password="$DEMO_READER_PASSWORD" << 'SQL'

-- 如果demo_reader不存在, 就创建该帐号。
SELECT format(
    'CREATE ROLE demo_reader LOGIN PASSWORD %L',
    :'reader_password'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_roles

WHERE NOT EXISTS (
    SELECT 1
    FROM pg_roles
    WHERE rolname = 'demo_reader'
) \gexec

-- 确保demo_reader使用当前配置的密码。
SELECT format(
    'ALTER ROLE demo_reader PASSWORD %L',
    :'reader_password'
) \gexec


-- 将该账号的事务默认设置为只读。
ALTER ROLE demo_reader
    SET default_transaction_read_only = on;

-- 单条SQL最多执行5秒,避免长时间占用数据库。
ALTER ROLE demo_reader
    SET statement_timeout = '5s';

-- 设置默认对象搜索路径。
ALTER ROLE demo_reader
    SET search_path = dispatch, public;


-- 删除PUBLIC在dispatch模式上的默认权限。
REVOKE ALL ON SCHEMA dispatch FROM PUBLIC;

-- 删除PUBLIC对dispatch中所有表和视图的默认权限。
REVOKE ALL ON ALL TABLES IN SCHEMA dispatch FROM PUBLIC;


-- 允许demo_reader连接当前数据库。
SELECT format(
    'GRANT CONNECT ON DATABASE %I TO demo_reader',
    current_database()
) \gexec

-- 允许demo_reader进入dispatch模式。
GRANT USAGE ON SCHEMA dispatch TO demo_reader;

-- 只允许demo_reader读取统一脱敏视图。
GRANT SELECT
ON dispatch.v_dispatch_case_search
TO demo_reader;

SQL
