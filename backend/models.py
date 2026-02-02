from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import pytz

Base = declarative_base()

# --- 1. Helper: 確保全系統時區一致性 ---
def get_tw_time():
    """獲取精準的台灣時間 (UTC+8)"""
    return datetime.now(pytz.timezone('Asia/Taipei'))

# --- 2. 使用者系統 (Users) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 💡 關鍵新增：解決 Seed 錯誤並提供帳號停用功能
    is_active = Column(Boolean, default=True, nullable=False) 
    
    created_at = Column(DateTime, default=get_tw_time)

    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

# --- 3. 產品模型 (ProductModels) - 標準化規格層 ---
class ProductModel(Base):
    __tablename__ = "product_models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True) 
    category = Column(String(50), index=True) # 手機, 平板...
    
    items = relationship("Product", back_populates="model", cascade="all, delete-orphan")

# --- 4. 平台定義 (Platforms) ---
class Platform(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True) # Momo, PChome
    url = Column(String(255))
    
    products = relationship("Product", back_populates="platform")

# --- 5. 賣場連結 (Products) - 實體關聯層 ---
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    model_id = Column(Integer, ForeignKey("product_models.id"), nullable=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    
    product_id_on_platform = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False) 
    url = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=get_tw_time)

    model = relationship("ProductModel", back_populates="items")
    platform = relationship("Platform", back_populates="products")
    
    prices = relationship("Price", back_populates="product", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('platform_id', 'product_id_on_platform', name='_platform_product_uc'),
    )

# --- 6. 即時價格 (Prices) - 當前掛牌價 ---
class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    url = Column(String(1024)) 
    updated_at = Column(DateTime, default=get_tw_time, onupdate=get_tw_time)

    product = relationship("Product", back_populates="prices")
    platform = relationship("Platform")

    __table_args__ = (
        UniqueConstraint('product_id', name='uq_price_product_instance'),
    )

# --- 7. 價格提醒 (Alerts) ---
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    target_price = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_tw_time)

    user = relationship("User", back_populates="alerts")
    product = relationship("Product", back_populates="alerts")

# --- 8. 歷史價格 (PriceHistory) - 時間序列大數據 ---
class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    recorded_at = Column(DateTime, default=get_tw_time)

    product = relationship("Product", back_populates="price_history")
    platform = relationship("Platform")

    __table_args__ = (
        Index('idx_history_product_time', 'product_id', 'recorded_at'),
    )

# --- 9. 收藏系統 (Favorites) ---
class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=get_tw_time)

    user = relationship("User", back_populates="favorites")
    product = relationship("Product", back_populates="favorites")