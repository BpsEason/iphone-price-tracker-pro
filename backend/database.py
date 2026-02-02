import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 💡 1. 主動載入 .env 檔案 (在本機開發時非常重要)
load_dotenv()

# 💡 2. 優先組合具體的環境變數，這比單一個 DATABASE_URL 更容易在 Docker 中除錯
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_NAME = os.getenv("POSTGRES_DB", "price_db")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# 💡 3. 動態構建連線字串
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 💡 4. 建立引擎：加入 pool_pre_ping 與 pool_size 優化效能
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 👈 每次連線前先測試，避免 "Server has gone away" 錯誤
    pool_size=10,        # 👈 預設保持 10 個連線，適合併發需求
    max_overflow=20      # 👈 尖峰時段最多允許額外 20 個連線
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI Dependency: 確保每個請求都有獨立的 Session 並在結束後關閉"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()