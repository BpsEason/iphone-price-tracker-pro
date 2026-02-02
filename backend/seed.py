import requests
import re
import logging
import json
import os
import sys
import time
import random
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

# 💡 確保引入 User 模型與雜湊函式
from database import SessionLocal
from models import Platform, Product, ProductModel, User
from auth import get_password_hash

# --- 1. 日誌配置 ---
def setup_seed_logging():
    log_dir = "logs"
    logger = logging.getLogger("seed_service")
    logger.setLevel(logging.INFO)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(log_dir, "seed.log"), encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except (PermissionError, OSError) as e:
        print(f"⚠️ 無法寫入日誌檔: {e}，將僅輸出至控制台。")
        
    return logger

logger = setup_seed_logging()

# --- 2. 業務定義 ---
MODEL_DEFINITIONS = [
    {"name": "iPhone 17 Pro Max", "keywords": ["17 PRO MAX", "17PROMAX"]},
    {"name": "iPhone 17 Pro", "keywords": ["17 PRO", "17PRO"]},
    {"name": "iPhone 17 Slim", "keywords": ["17 SLIM", "17SLIM", "17 AIR"]},
    {"name": "iPhone 17", "keywords": ["IPHONE 17", "IPHONE17"]},
]

SEARCH_ENTRIES = [
    {
        "category": "iPhone",
        "keyword": "iPhone 17 Pro Max",
        "momo_search": "https://m.momoshop.com.tw/search.momo?searchKeyword=iPhone%2017%20Pro%20Max",
        "pchome_api": "https://ecshweb.pchome.com.tw/search/v3.3/all/results?q=iPhone 17 Pro Max&page=1&sort=rnk/dc"
    },
    {
        "category": "iPhone",
        "keyword": "iPhone 17 Pro",
        "momo_search": "https://m.momoshop.com.tw/search.momo?searchKeyword=iPhone%2017%20Pro",
        "pchome_api": "https://ecshweb.pchome.com.tw/search/v3.3/all/results?q=iPhone 17 Pro&page=1&sort=rnk/dc"
    }
]

# --- 3. 工具函式 ---

def seed_users(db):
    """💡 新增：初始化預設管理員帳號"""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin1234")
    
    logger.info(f"👤 執行 User 初始化: {admin_email}")
    
    # 使用 PostgreSQL Upsert 確保不重複插入
    stmt = insert(User).values(
        username="Administrator",
        email=admin_email,
        password_hash=get_password_hash(admin_pass),
        is_active=True
    ).on_conflict_do_nothing(index_elements=['email'])
    
    db.execute(stmt)
    db.commit()

def map_to_model(product_name):
    if not product_name: return None
    name_upper = product_name.upper().replace(" ", "")
    sorted_defs = sorted(MODEL_DEFINITIONS, key=lambda x: len(x['name']), reverse=True)
    for model in sorted_defs:
        for kw in model["keywords"]:
            if kw.upper().replace(" ", "") in name_upper:
                return model["name"]
    return None

def clean_momo_name(raw_name):
    if not raw_name: return ""
    try:
        processed = raw_name.replace('\\"', '"').replace('\\\\', '\\')
        processed = processed.encode('utf-8').decode('unicode_escape')
        return processed.encode('latin1').decode('utf-8')
    except Exception:
        return raw_name

def auto_discover_ids(entry, platform_type):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    }
    products = []
    
    try:
        if platform_type == "momo":
            session = requests.Session()
            session.get("https://m.momoshop.com.tw/main.momo", headers=headers, timeout=10)
            time.sleep(random.uniform(1, 2))
            res = session.get(entry["momo_search"], headers=headers, timeout=20)
            res.encoding = 'utf-8' 
            html_content = res.text
            codes = re.findall(r'i_code=(\d+)', html_content)
            names = re.findall(r'\\"goodsName\\":\\"(.*?)\\"', html_content)
            if not names:
                names = re.findall(r'"goodsName":"(.*?)"', html_content)
            seen_ids = set()
            for i in range(min(len(codes), len(names))):
                g_id = codes[i]
                if g_id not in seen_ids:
                    seen_ids.add(g_id)
                    products.append({
                        "id": g_id,
                        "name": clean_momo_name(names[i]),
                        "url": f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={g_id}"
                    })
        elif platform_type == "pchome":
            res = requests.get(entry["pchome_api"], headers=headers, timeout=15)
            data = res.json()
            if data.get("prods"):
                for p in data["prods"]:
                    products.append({
                        "id": p["Id"],
                        "name": p["name"],
                        "url": f"https://24h.pchome.com.tw/prod/{p['Id']}"
                    })
        return products
    except Exception as e:
        logger.error(f"❌ {platform_type} 發現失敗: {e}")
        return []

# --- 4. Seed 主程序 ---

def seed_data():
    db = SessionLocal()
    try:
        logger.info("🚀 啟動強化版數據 Seed 流程 (含 User 初始化)...")
        
        # 💡 [關鍵] 1. 先初始化 User
        seed_users(db)
        
        # 2. 初始化平台資料
        platform_map = {}
        platforms_to_seed = {
            "Momo": "https://www.momoshop.com.tw", 
            "PChome": "https://24h.pchome.com.tw"
        }
        for name, url in platforms_to_seed.items():
            p_obj = db.query(Platform).filter_by(name=name).first()
            if not p_obj:
                p_obj = Platform(name=name, url=url)
                db.add(p_obj)
                db.flush()
            platform_map[name.lower()] = p_obj

        # 3. 初始化型號資料
        model_map = {}
        for m_def in MODEL_DEFINITIONS:
            m_obj = db.query(ProductModel).filter_by(name=m_def["name"]).first()
            if not m_obj:
                m_obj = ProductModel(name=m_def["name"], category="iPhone")
                db.add(m_obj)
                db.flush()
            model_map[m_def["name"]] = m_obj
        
        db.commit()

        # 4. 執行自動發現與入庫
        for entry in SEARCH_ENTRIES:
            for p_type in ["momo", "pchome"]:
                found_list = auto_discover_ids(entry, p_type)
                p_obj = platform_map[p_type]
                for info in found_list:
                    matched_model_name = map_to_model(info["name"])
                    target_model_id = model_map[matched_model_name].id if matched_model_name else None
                    stmt = insert(Product).values(
                        model_id=target_model_id,
                        platform_id=p_obj.id,
                        product_id_on_platform=info["id"],
                        name=info["name"],
                        url=info["url"]
                    ).on_conflict_do_update(
                        index_elements=['platform_id', 'product_id_on_platform'],
                        set_={"name": info["name"], "url": info["url"], "model_id": target_model_id}
                    )
                    db.execute(stmt)
                db.commit()
                logger.info(f"✅ {p_type.capitalize()} 處理完成: {entry['keyword']}")
                time.sleep(random.uniform(1, 2))

    except Exception as e:
        db.rollback()
        logger.error(f"💥 Seed 致命錯誤: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()