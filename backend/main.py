import inspect
import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, Query, Path, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from auth import get_current_user_optional
import pytz

# 💡 核心組件匯入
from scraper import PriceScraper, setup_logging
from worker import scrape_all_platforms
from database import SessionLocal
from models import User
# 💡 認證邏輯與時區工具匯入
from auth import verify_password, create_access_token, get_current_user
from models import get_tw_time

# --- 1. 系統日誌與初始化 ---
logger = setup_logging()

raw_description = """
    ## 專業級 iPhone 價格追蹤系統後端 (v2.6.1)
    整合 OAuth2 JWT 安全認證、異步爬蟲排程與個人化收藏功能。
"""

app = FastAPI(
    title="iPhone Price Tracker Pro API",
    description=inspect.cleandoc(raw_description),
    version="2.6.1",
    root_path="/api",      
    docs_url="/docs",      
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. 資料庫依賴 ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 3. Pydantic 數據模型 (Schemas) ---

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfileSchema(BaseModel):
    username: str
    email: str
    created_at: datetime
    class Config:
        from_attributes = True

class FavoriteCreate(BaseModel):
    product_id: int = Field(..., description="要收藏的 Product 實體 ID")

class FavoriteResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    platform_name: str
    url: str
    current_price: Optional[float] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ProductModelSchema(BaseModel):
    id: int
    name: str = Field(..., example="iPhone 16 Pro")
    category: Optional[str] = Field(None, example="Smartphones")
    
    # 💡 關鍵：增加這個欄位，預設為 False
    # 當 SQL 查詢使用 LEFT JOIN 算出收藏狀態後，FastAPI 會自動填入這裡
    is_favorite: bool = False 

    class Config:
        # 💡 允許從資料庫的 Row 物件直接轉換 (針對 SQLAlchemy)
        from_attributes = True

class SystemStatsSchema(BaseModel):
    total_models: int
    total_price_records: int
    db_status: str
    active_platforms: List[str]
    server_time: datetime

class PriceHistoryPoint(BaseModel):
    date: str  # YYYY-MM-DD
    price: float
    platform: str

class PriceTrendResponse(BaseModel):
    model_name: str
    history: List[PriceHistoryPoint]

# --- 4. 認證路由 (Authentication) ---

@app.post("/v1/auth/login", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/v1/users/me", response_model=UserProfileSchema, tags=["Auth"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- 5. 系統狀態與健康檢查 (Health) ---

@app.get("/", tags=["Health"])
def read_root():
    """🏠 根路徑導引"""
    return {
        "status": "online",
        "version": "2.6.1",
        "documentation": "/api/docs"
    }

@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """🏥 系統深層健康檢查 (含資料庫連線)"""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy", 
            "database": "connected", 
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"❌ DB Health Check Failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Down")

# --- 6. 收藏功能路由 (Favorites) ---

@app.post("/v1/favorites", tags=["Business"])
async def add_favorite(
    fav_in: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. 檢查商品是否存在 (注意：這裡要對應你資料庫的表名，若為 product_models 請修改)
    product = db.execute(
        text("SELECT id FROM product_models WHERE id = :pid"), 
        {"pid": fav_in.product_id}
    ).fetchone()
    
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 2. 檢查是否已經收藏
    existing = db.execute(
        text("SELECT id FROM favorites WHERE user_id = :uid AND product_id = :pid"),
        {"uid": current_user.id, "pid": fav_in.product_id}
    ).fetchone()
    
    try:
        if existing:
            # 💡 核心改動：如果已存在，就執行「刪除」，實現取消收藏功能
            db.execute(
                text("DELETE FROM favorites WHERE id = :fid"),
                {"fid": existing.id}
            )
            db.commit()
            return {
                "status": "removed", 
                "message": "已從收藏清單移除", 
                "is_favorite": False  # 💡 讓前端知道現在是「未收藏」
            }

        # 3. 如果不存在，則執行「新增」
        db.execute(
            text("INSERT INTO favorites (user_id, product_id, created_at) VALUES (:uid, :pid, :cat)"),
            {"uid": current_user.id, "pid": fav_in.product_id, "cat": get_tw_time()}
        )
        db.commit()
        return {
            "status": "success", 
            "message": "已加入收藏", 
            "is_favorite": True   # 💡 讓前端知道現在是「已收藏」
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"收藏操作失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="資料庫操作失敗")

@app.get("/v1/favorites", response_model=List[FavoriteResponse], tags=["Business"])
async def list_my_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = text("""
        SELECT 
            f.id, f.product_id, f.created_at,
            p.name as product_name, p.url,
            pl.name as platform_name,
            pr.price as current_price
        FROM favorites f
        JOIN products p ON f.product_id = p.id
        JOIN platforms pl ON p.platform_id = pl.id
        LEFT JOIN prices pr ON p.id = pr.product_id
        WHERE f.user_id = :uid
        ORDER BY f.created_at DESC
    """)
    result = db.execute(query, {"uid": current_user.id}).fetchall()
    return [dict(row._mapping) for row in result]

@app.delete("/v1/favorites/{fav_id}", tags=["Business"])
async def delete_favorite(
    fav_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = db.execute(
        text("DELETE FROM favorites WHERE id = :fid AND user_id = :uid"),
        {"fid": fav_id, "uid": current_user.id}
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="收藏紀錄不存在或無權限")
    return {"status": "success", "message": "已移除收藏"}

# --- 7. 業務與系統管理 ---

@app.get("/products", response_model=List[ProductModelSchema], tags=["Business"])
def list_products(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    uid = current_user.id if current_user else 0
    
    # 💡 修正後的 SQL：透過 products 表連結型號與收藏
    query = text("""
        SELECT 
            pm.id, 
            pm.name, 
            pm.category,
            EXISTS (
                SELECT 1 
                FROM products p
                JOIN favorites f ON f.product_id = p.id
                WHERE p.model_id = pm.id AND f.user_id = :uid
            ) as is_favorite
        FROM product_models pm
        ORDER BY pm.id DESC
    """)
    
    result = db.execute(query, {"uid": uid}).fetchall()
    return [dict(row._mapping) for row in result]

@app.post("/tasks/scrape", tags=["System"])
def trigger_scrape_task(
    target: Optional[str] = Query("All", description="目標平台"),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"🔔 管理員 [{current_user.email}] 觸發了 {target} 爬蟲任務")
    task = scrape_all_platforms.delay()
    return {"status": "accepted", "task_id": task.id, "operator": current_user.username}

@app.get("/stats", response_model=SystemStatsSchema, tags=["System"])
def get_system_stats(db: Session = Depends(get_db)):
    model_count = db.execute(text("SELECT count(*) FROM product_models")).scalar()
    price_count = db.execute(text("SELECT count(*) FROM prices")).scalar()
    platforms = db.execute(text("SELECT name FROM platforms")).fetchall()
    return {
        "total_models": model_count, "total_price_records": price_count,
        "db_status": "stable", "active_platforms": [p[0] for p in platforms],
        "server_time": datetime.now()
    }

@app.get("/products/{model_id}/history", response_model=PriceTrendResponse, tags=["Products"])
async def get_price_history(
    model_id: int = Path(..., description="產品型號 ID"),
    db: Session = Depends(get_db)
):
    # 1. 先確認型號存在
    model = db.execute(
        text("SELECT name FROM product_models WHERE id = :mid"),
        {"mid": model_id}
    ).fetchone()

    if not model:
        raise HTTPException(404, "型號不存在")

    # 💡 架構師提示：使用相容性較高的 SQL 寫法，或在 Python 層處理時間過濾
    # 這裡假設你的生產環境是 PostgreSQL
    query = text("""
        SELECT 
            TO_CHAR(pr.updated_at, 'YYYY-MM-DD') as date_str,
            CAST(pr.price AS FLOAT) as price_val,
            pl.name as platform_name
        FROM prices pr
        JOIN products p ON pr.product_id = p.id
        JOIN platforms pl ON p.platform_id = pl.id
        WHERE p.model_id = :mid
        ORDER BY pr.updated_at ASC
    """)
    
    try:
        rows = db.execute(query, {"mid": model_id}).fetchall()
        
        # 💡 使用 List Comprehension 進行高效轉換
        history = [
            PriceHistoryPoint(
                date=row.date_str,
                price=row.price_val,
                platform=row.platform_name
            ) for row in rows
        ]

        return PriceTrendResponse(
            model_name=model.name,
            history=history
        )
    except Exception as e:
        logger.error(f"查詢歷史價格失敗: {str(e)}")
        raise HTTPException(500, "伺服器內部查詢錯誤")