FROM python:3.14-slim AS builder

WORKDIR /app

COPY requirements.txt .

# pip 캐시 완전 비활성화 + tmpfs 사용
RUN --mount=type=tmpfs,destination=/tmp pip install --no-cache-dir \
    --disable-pip-version-check --no-python-version-warning \
    --only-binary=all -r requirements.txt -i https://pypi.org/simple/

FROM python:3.14-slim

# 시스템 패키지 최소화
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m appuser

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.14 /usr/local/lib/python3.14
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src ./src

USER appuser
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8501 8000
CMD ["streamlit", "run", "src/core/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
