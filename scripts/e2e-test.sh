#!/bin/sh
#从浏览器之后的入口层开始，验证 API -> QueryPlan -> SQL -> PostgreSQL 全链路。

set -eu

api_url="${API_URL:-http://127.0.0.1:8000}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

attempt=0

until curl -fsS "${api_url}/health/ready" > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    

    if [ "$attempt" -ge 30 ];then
        echo "ERROR: API连续30次检查未准备就绪; 请检查postgres和API日志" >&2
        exit 1
    fi

    sleep 2
done

printf '%s\n' 'PASS: API已就绪'

run_case() {
    name="$1"
    question="$2"
    output="${tmp_dir}/${name}.json"

    printf "INFO: 正在执行测试 ${name}\n"

    curl -fsS -X POST "${api_url}/api/v1/query" \
    -H 'Content-Type: application/json' \
    --data "{\"question\":\"${question}\",\"user_id\":\"e2e_tester\"}" \
    > "$output"
    python3 - "$output" "$name"<<'PY'
import json
import sys

with open(sys.argv[1],encoding="UTF-8") as handle:
    result = json.load(handle)

assert result['query_plan']['intent'] in {
    "detail_search","aggregate","similar_case_search"
}
assert 0 <= result["row_count"] <=100
assert ":start_time" in result["sql_template"]

print(f"PASS: {sys.argv[2]} -> {result['row_count']} rows, {result['elapsed_ms']} ms" )
PY
}

run_case hospital_count "查询最近7天各医院的派车数量"
run_case slow_dispatch "找出最近30天金平区派车超过5分钟的记录"
run_case similar_case "找10条与老人胸闷出汗相似的警情"
run_case reponse_avg "统计最近30天各地区的平均响应时间"


echo "PASS: 四类端到端查询全部完成。页面可访问 http://127.0.0.1:${UI_PORT:-8501}"