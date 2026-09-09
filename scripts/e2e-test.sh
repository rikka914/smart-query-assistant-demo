#!/bin/sh
#从浏览器之后的入口层开始，验证 API -> QueryPlan -> SQL -> PostgreSQL 全链路。

set -eu

api_url="${API_URL:-http://127.0.0.1:8000}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

