#!/bin/sh
#验证种子数据、脱敏视图和demo_reader的只读权限。
set -eu

project_dir="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$project_dir"

if [ -f .env ]; then
    set -a
    #.env只应该包含可信的key=value配置。
    . ./.env
    set +a
fi

compose="docker compose"
if ! docker compose version >/dev/null 2>&1; then
compose="docker-compose"
fi

$compose exec -T postgres psql \
  --username "${POSTGRES_USER:-demo_admin}" \
  --dbname "${POSTGRES_DB:-dispatch_demo}" \
  --set=ON_ERROR_STOP=1 <<'SQL'
SELECT count(*) AS hospitals FROM dispatch.hospital;
SELECT count(*) AS cases FROM dispatch.v_dispatch_case_search;
SELECT count(*) FILTER(WHERE address_masked LIKE '%某%') AS masked_address FROM dispatch.v_dispatch_case_search;
SQL

$compose exec -T \
  -e PGPASSWD="${DEMO_READER_PASSWORD:?请先加载.env或导出DEMO_READER_PASSWORD}" postgres \
  psql --username demo_reader --dbname "${POSTGRES_DB:-dispatch_demo}" \
  --set=ON_ERROR_STOP=1 \
  --command "SELECT case_id,district,event_type FROM dispatch.v_dispatch_case_search LIMIT 3;"


if $compose exec -T \
   -e PGPASSWD="$DEMO_READER_PASSWORD" postgres \
   psql --username demo_reader --dbname "${POSTGRES_DB:-dispatch_demo}" \
   --set=ON_ERROR_STOP=1 \
   --command "DELETE FROM dispatch.alarm_case WHERE false;" >/dev/null 2>&1; then
   echo "ERROR: demo_reader unexpectedly obtained write access" >&2
   exit 1
fi

echo "PASS: 数据可读,且demo_reader无法写业务表."
