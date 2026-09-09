FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install --index-url "$PIP_INDEX_URL" --no-cache-dir --retries 10 --timeout 120 -r requirements.txt

COPY app ./app

RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["uvicron",  "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
