# 📊 iPhone Price Tracker Pro

**iPhone Price Tracker Pro** 是一款專為電子商務設計的自動化比價與監測系統。系統專注於從 **Momo 購物網** 與 **PChome 24h 購物** 實時抓取價格數據，並透過異步管線進行清理、聚合與存儲。

---

## 🏗️ 設計哲學與架構決策 (Design Philosophy & Decisions)

### 1. 為什麼選擇 FastAPI？

- **非同步優先 (Async Native)**：電商比價涉及大量 I/O 等待，FastAPI 的非同步特性讓系統能處理更多併發請求。
- **數據型別安全**：利用 Pydantic 進行數據校驗，確保從電商網頁抓回來的價格格式正確。

### 2. 為什麼需要 `reset.sh` 強力重置？

- **徹底清空狀態**：透過 `down -v --rmi local` 銷毀卷與舊映像檔。
- **解決環境污染**：手動刪除舊有的 Alembic 遷移腳本並重設 `alembic_version` 表，確保資料庫 Schema 始終處於最新且一致的狀態。

---

## 🕒 自動化排程機制 (Scheduling)

系統採用 **Celery Beat** 作為定時任務調度器，實現無人值守的自動化監控。

- **任務調度**：透過 `scheduler` 服務定時將爬蟲任務派發至 Redis 佇列。
- **權限與衝突處理**：
- **PID 與 Schedule 檔案**：在啟動指令中，將 `celerybeat.pid` 與 `celerybeat-schedule` 指向 `/tmp` 目錄，有效避開 Docker 容器內的權限受限問題 (`Errno 13 Permission denied`)。
- **指令配置**：使用 `celery -A worker.celery_app beat --pidfile=/tmp/celerybeat.pid -s /tmp/celerybeat-schedule` 確保服務平滑重啟而不發生衝突。

---

## ログ 與 可觀測性 (Logging & Observability)

為了便於線上排錯與行為分析，系統實施了完整的日誌持久化策略。

- **日誌持久化 (Persistence)**：
- **Volume 掛載**：後端 (`backend`)、爬蟲 (`worker`) 與排程器 (`scheduler`) 皆將容器內的 `/app/logs` 目錄掛載至宿主機的 `./backend/logs`。
- **實時監控**：開發者可以直接在宿主機讀取日誌檔，無需頻繁進入容器。

- **開發偵錯模式**：
- 後端 API 啟動時啟用 `--reload` 模式，並設定 `PYTHONUNBUFFERED=1` 確保 Python 日誌能即時輸出至標準輸出 (Stdout) 與文件，不被緩衝區延遲。

---

## 🛠️ 工程亮點 (Engineering Highlights)

- **Docker Multi-stage Build**：
- **編譯階段**：使用 `node:18-alpine` 進行 `npm install` 與 `npm run build` 。

- **運行階段**：使用 `nginx:stable-alpine` 僅部署編譯後的 `dist` 檔案，極大化縮小鏡像體積 。

- **解鎖循環依賴**：`reset.sh` 腳本採用「漸進式啟動」，先確保資料庫就緒後才啟動後端，最後解鎖前端，避開健康檢查導致的啟動死循環。

---

## 🚀 快速啟動

### 1. 初始化環境

```bash
# 賦予執行權限並啟動重置腳本
chmod +x reset.sh
./reset.sh

```

此腳本會自動完成 DB 清理、Alembic 初始化、後端啟動以及前端部署。

### 2. 查看系統運行狀況

- **查看即時日誌**：`tail -f backend/logs/app.log`
- **API 文件 (Swagger)**：`http://localhost:8888/api/docs`

---
