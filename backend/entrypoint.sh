#!/bin/bash
# 讓腳本在遇到錯誤時立即停止
set -e

# 定義虛擬環境路徑 (根據你的 Dockerfile)
VENV_PYTHON="python"
VENV_ALEMBIC="alembic"

echo "🔍 [System] 正在檢查服務連線狀態..."

# --- 內部函式：等待資料庫 ---
wait_for_db() {
    echo "⏳ 等待資料庫連線 (db:5432)..."
    # 使用 Python 腳本測試連線，比 pg_isready 更通用
    until $VENV_PYTHON -c "import socket; s = socket.socket(); s.connect(('db', 5432))" 2>/dev/null; do
        sleep 2
    done
    echo "✅ 資料庫連線成功！"
}

# 所有的服務（API, Worker, Scheduler）都需要等待資料庫
wait_for_db

# --- 判斷是否為「主後端服務」 (由環境變數或啟動命令判斷) ---
# 只有 API 服務 (通常不帶 CELERY_WORKER 變數) 才負責執行 DB Migration
if [[ "$CELERY_WORKER" != "true" ]]; then
    echo "🏗️  主服務模式：檢查並執行資料庫遷移..."
    
    # 確保遷移目錄存在
    mkdir -p migrations/versions
    
    # 檢查是否有任何遷移腳本 (排除 __init__.py)
    VERSION_FILES=$(ls migrations/versions/*.py 2>/dev/null | grep -v "__init__.py" || true)

    if [ -z "$VERSION_FILES" ]; then
        echo "⚠️  本地無遷移檔案，執行初始化同步 (Stamp & Revision)..."
        $VENV_ALEMBIC stamp base || echo "Stamp skipped"
        $VENV_ALEMBIC revision --autogenerate -m "Initial_schema"
    fi

    echo "🚀 執行 Alembic Upgrade..."
    $VENV_ALEMBIC upgrade head

    echo "🌱 檢查種子資料..."
    # 執行種子資料填充，若出錯僅警告不中斷 (預防重複插入)
    $VENV_PYTHON seed.py || echo "⚠️  Seed 任務已跳過或資料已存在"
else
    echo "👷 Celery 模式：跳過資料庫遷移，準備啟動 Worker/Beat..."
fi

echo "🔥 [System] 啟動最終服務指令: $@"

# 💡 關鍵：使用 exec "$@" 執行 docker-compose.yml 中定義的 command
# 這能讓 API 執行 uvicorn，Worker 執行 celery worker，Scheduler 執行 celery beat
exec "$@"