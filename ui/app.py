"""Streamlit 演示页面。页面只访问API,不持有数据库密码"""

import os
import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL","http://localhost:8000").rstrip("/")

st.set_page_config(page_title="智能数据查询助手", page_icon="🚑", layout="wide")
st.title("🚑 智能数据查询助手 Demo")
st.caption("历史脱敏数据查询演示; 不用于医疗诊断或实时派车。")

examples = [
    "查询最近7天各医院的派车数量",
    "找出最近30天龙湖区派车超过5分钟的记录",
    "找10条与老人胸闷出汗相似的警情",
    "统计最近30天各区的平均响应时间",
]

with st.sidebar:
    st.subheader("演示设置")
    user_id = st.text_input("查询人标识",value="demo_user",max_chars=64)
    selected = st.selectbox("示例问题",options=["自定义"] + examples)
    st.info("系统最多放回100条;默认查询最近30天。")

default_question = ""if selected == "自定义" else selected
question = st.text_area(
    "请输入要查询的内容",
    value=default_question,
    height=100,
    placeholder="例如:统计最近30天各区的平均响应时间"
)

if st.button("开始查询",type="primary",use_container_width=True):
    if len(question.strip())< 2:
        st.warning("请输入至少2个字符。")

    else:
        try:
            with st.spinner("正在生成查询计划并读取数据..."):
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/query",
                    json={
                        "question":question.strip(),
                        "user_id":user_id or "demo_user"
                    },
                    timeout=30,
                )

            if response.status_code != 200:
                detail = response.json().get("detail", response.text)
                st.error(f"查询失败: {detail}")

            else:
                result = response.json()

                c1,c2,c3 = st.columns(3)
                c1.metric("返回记录",result["row_count"])
                c2.metric("总耗时",f"{result['elapsed_ms']} ms")
                c3.metric("计划生成器",result["planner"])

                if result.get("planner_warning"):
                    st.warning("本地模型不可用，已自动使用规则解析器完成查询。")

                st.subheader("查询结果")
                if result["rows"]:
                    st.dataframe(
                        pd.DataFrame(result["rows"]),
                        use_container_width=True,
                    )

                else:
                    st.info("条件解析成功，但没有匹配记录。可扩大时间范围或减少过滤条件。")

                with st.expander("查看系统识别的条件和SQL模板"):
                    st.json(result["query_plan"])
                    st.code(result["sql_template"],language="sql")
                    st.caption("SQL中只有固定模板; 实际条件通过参数绑定,不进行字符串拼接。")    
        except requests.RequestException as exc:
            st.error(f"无法连接查询服务:{exc}")