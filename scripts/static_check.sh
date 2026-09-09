#!/bin/sh

#源码检查

#遇到错误立即停止
set -eu

project_dir="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd )"
cd "$project_dir"

python3 -m compileall -q api ui tests

PYTHONPATH=. python3 -m unittest discover -s tests -v


# 任意用户输入都不应该通过f-string插入sql
# SQL中只能拼接由程序控制的白名单常量

if grep -R "question.*SELECT\|SELECT.*question" api/app --include='*.py' > /dev/null;then
    echo "ERROR: 发现疑似把原始问题拼入SQL的代码" >&2
    exit 1
fi

echo "PASS: Python编译、单元测试和基础安全扫描通过。"   
