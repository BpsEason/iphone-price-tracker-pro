# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev

# --- Stage 2: Final ---
FROM python:3.12-slim
WORKDIR /app

# 建立非 root 帳號 (使用固定 UID/GID 1000 以利於權限管理)
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

# 安裝運行時必要的庫與工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    dnsutils \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# 複製虛擬環境
COPY --from=builder /opt/venv /opt/venv

# 設定環境變數
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Taipei \
    PYTHONDONTWRITEBYTECODE=1

# 💡 關鍵修正：確保 logs 目錄存在且權限正確
# 同時確保宿主機掛載點的父目錄也是正確的擁有者
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# 使用 --chown 確保代碼檔案屬於 appuser
COPY --chown=appuser:appuser . .

# 修正 entrypoint 權限
RUN chmod +x entrypoint.sh && chown appuser:appuser entrypoint.sh

# 切換到非 root 使用者
USER appuser

ENTRYPOINT ["./entrypoint.sh"]