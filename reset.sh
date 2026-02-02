#!/bin/bash
# -------------------------------------------------------
# reset.sh - 專業架構師版：徹底重置並解鎖環境
# -------------------------------------------------------
set -e

echo "🔥 [1/5] 徹底銷毀環境、舊數據與映像檔快取..."
# -v 刪除 volume, --rmi local 刪除本地構建的 image 確保代碼更新
docker-compose down -v --remove-orphans --rmi local

echo "🧹 [2/5] 清除舊有的遷移腳本 (回歸白紙狀態)..."
# 確保我們是在乾淨的狀態下重新生成 Initial Schema
find ./migrations/versions -name "*.py" ! -name "__init__.py" -delete 2>/dev/null || true

echo "🏗️ [3/5] 重新構建並啟動基礎設施 (DB/Redis)..."
docker-compose build --no-cache
docker-compose up -d db redis

echo "⏳ 等待資料庫就緒..."
until docker-compose exec -T db pg_isready -U user -d price_db; do
  sleep 2
done

# 💡 關鍵修正：直接在 DB 裡砍掉 alembic 紀錄，防止狀態衝突
docker-compose exec -T db psql -U user -d price_db -c "DROP TABLE IF EXISTS alembic_version CASCADE;"

echo "🚀 [4/5] 啟動後端並同步資料結構..."
# 這裡直接讓 backend 跑起來，它會執行我們修好的 entrypoint.sh
# entrypoint.sh 裡面已經有 python -m alembic ... 的邏輯了
docker-compose up -d backend

echo "⏳ 等待後端初始化與 Seed 填充..."
# 給後端一點時間跑 alembic upgrade 與 seed.py
sleep 10

echo "🌐 [5/5] 解鎖前端與其他服務..."
# 透過 --no-deps 或是直接啟動，繞過健康檢查的死循環
docker-compose up -d frontend worker scheduler

echo "-------------------------------------------------------"
echo "✅ [SUCCESS] 系統重置完成！"
docker-compose ps
echo "-------------------------------------------------------"