import requests
import random
import time
import re
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

# 💡 確保引入與你的專案目錄結構一致
from database import SessionLocal
from models import Product, Platform, Price, PriceHistory
from bs4 import BeautifulSoup

# --- 1. 日誌配置 (架構師強化版) ---
def setup_logging():
    """
    配置日誌系統：
    1. 優先保證輸出到控制台 (Docker Logs 必要)
    2. 嘗試建立檔案日誌，若因權限問題失敗則優雅降級，不導致程式崩潰
    """
    # 使用絕對路徑避免在 Docker 環境中路徑偏移
    log_dir = os.path.join(os.getcwd(), "logs")
    logger = logging.getLogger("PriceScraper")
    
    # 避免重複添加 Handler (在 Celery 或 Uvicorn 重載時常見)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s (%(name)s): %(message)s', '%Y-%m-%d %H:%M:%S')
        
        # --- A. 建立控制台輸出 (Stdout) ---
        # 這是 Docker 的生命線，絕對不會因為權限問題失敗
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # --- B. 建立檔案輸出 (File) ---
        try:
            if not os.path.exists(log_dir):
                # exist_ok=True 避免併發建立時的 Race Condition
                os.makedirs(log_dir, exist_ok=True)
            
            log_path = os.path.join(log_dir, "scraper.log")
            file_handler = RotatingFileHandler(
                log_path, 
                maxBytes=5*1024*1024, 
                backupCount=5, 
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            # 💡 關鍵修正：捕捉權限錯誤，印出警告但不中止程式
            print(f"⚠️  Permission Warning: 無法寫入實體 Log 檔案 ({e})。")
            print("💡 提示：目前僅會將日誌輸出至 Docker Console (stdout)。")
        
        logger.propagate = False
        
    return logger

# 全域初始化 Logger
logger = setup_logging()

# --- 2. 價格爬蟲引擎 ---
class PriceScraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def clean_price(self, price_str):
        if price_str is None: return 0.0
        try:
            clean_str = str(price_str).replace(",", "").replace("$", "").replace("NT", "").strip()
            match = re.search(r'\d+(\.\d+)?', clean_str)
            return float(match.group()) if match else 0.0
        except Exception as e:
            logger.error(f"⚠️ 價格轉換失敗 ({price_str}): {e}")
            return 0.0

    def clean_momo_name(self, raw_name):
        if not raw_name: return ""
        try:
            # 處理 Momo 網頁偶發的編碼異常
            return raw_name.encode('utf-8').decode('unicode_escape').encode('latin1').decode('utf-8')
        except:
            return raw_name

    def get_headers(self, platform="Momo"):
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        if platform == "Momo":
            headers["Referer"] = "https://www.momoshop.com.tw/"
        else:
            headers["Referer"] = "https://24h.pchome.com.tw/"
        return headers

    # --- PChome 強化邏輯 ---
    def scrape_pchome(self, prod_id: str):
        clean_id = str(prod_id).strip()
        logger.info(f"🔍 PChome 深度爬取: {clean_id}")
        
        # 1. 優先使用 API
        price = self._scrape_pchome_api(clean_id)
        if price: return price

        # 2. API 失敗後使用網頁解析保底
        return self._scrape_pchome_frontend(clean_id)

    def _scrape_pchome_api(self, prod_id):
        try:
            ts = int(time.time() * 1000)
            api_url = f"https://ecapi.pchome.com.tw/ecshop/prodapi/v2/prod?id={prod_id}&fields=Price&_callback=jsonp_price&_={ts}"
            res = self.session.get(api_url, headers=self.get_headers("PChome"), timeout=10)
            match = re.search(r'\((.*)\)', res.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                # 動態取 Key (PChome API 回傳結構通常以商品 ID 為 Key)
                for key in data.keys():
                    if isinstance(data[key], dict) and "Price" in data[key]:
                        return self.clean_price(data[key]["Price"].get("P", 0))
        except: pass
        return None

    def _scrape_pchome_frontend(self, prod_id):
        """Next.js 結構解析"""
        url = f"https://24h.pchome.com.tw/prod/{prod_id}"
        try:
            time.sleep(random.uniform(1, 2))
            res = self.session.get(url, headers=self.get_headers("PChome"), timeout=15)
            
            # 策略：JSON-LD 解析 (SEO 標準結構)
            price_match = re.search(r'"price":\s*"(\d+)"', res.text)
            if price_match:
                return float(price_match.group(1))
        except Exception as e:
            logger.error(f"❌ PChome 網頁解析出錯: {e}")
        return None

    # --- Momo 強化邏輯 ---
    def scrape_momo(self, i_code: str):
        url = f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={i_code}"
        try:
            time.sleep(random.uniform(2, 4))
            res = self.session.get(url, headers=self.get_headers("Momo"), timeout=15)
            if res.status_code != 200: return None

            soup = BeautifulSoup(res.text, 'html.parser')
            # 優先找 meta tag，最快且穩定
            meta_price = soup.find("meta", property="product:price:amount")
            if meta_price: 
                return self.clean_price(meta_price.get("content"))
            
            # 備援：JSON-LD
            json_ld = soup.find("script", type="application/ld+json")
            if json_ld:
                data = json.loads(json_ld.string)
                offers = data.get('offers')
                if isinstance(offers, list): return self.clean_price(offers[0].get('price'))
                return self.clean_price(offers.get('price'))
        except Exception as e:
            logger.error(f"❌ Momo 抓取失敗: {e}")
        return None

    # --- 資料庫保存邏輯 ---
    def _save_price_to_db(self, db, item, price_val):
        """
        同步更新 Price 表 (Upsert) 與 PriceHistory 表
        """
        try:
            # 1. 更新當前價格
            stmt = insert(Price).values(
                product_id=item.id,
                platform_id=item.platform_id,
                price=price_val,
                updated_at=datetime.now()
            ).on_conflict_do_update(
                index_elements=['product_id'],
                set_={'price': price_val, 'updated_at': datetime.now()}
            )
            db.execute(stmt)

            # 2. 寫入歷史紀錄
            new_history = PriceHistory(
                product_id=item.id,
                platform_id=item.platform_id,
                price=price_val,
                recorded_at=datetime.now()
            )
            db.add(new_history)
        except Exception as e:
            logger.error(f"❌ DB 寫入錯誤: {e}")
            raise

    # --- 核心啟動引擎 ---
    def automated_run(self, target_platform="Momo"):
        logger.info(f"🚀 [TASK] 開始更新 {target_platform} 價格...")
        db = SessionLocal()
        try:
            # 使用 ILIKE 模糊匹配平台名稱
            query = text("""
                SELECT p.id, p.name, p.product_id_on_platform, p.platform_id
                FROM products p
                JOIN platforms pl ON p.platform_id = pl.id
                WHERE pl.name ILIKE :target
            """)
            items = db.execute(query, {"target": f"%{target_platform}%"}).fetchall()
            
            if not items:
                logger.warning(f"🔎 找不到匹配 {target_platform} 的商品。")
                return

            success_count = 0
            for item in items:
                if "momo" in target_platform.lower():
                    price_val = self.scrape_momo(item.product_id_on_platform)
                else:
                    price_val = self.scrape_pchome(item.product_id_on_platform)

                if price_val and price_val > 0:
                    self._save_price_to_db(db, item, price_val)
                    db.commit() 
                    logger.info(f"✅ 更新: {item.name[:20]}... -> ${price_val}")
                    success_count += 1
                
                # 動態延遲防止被封 IP
                time.sleep(random.uniform(5, 10))

            logger.info(f"🏁 任務完成: {success_count}/{len(items)} 成功")

        except Exception as e:
            db.rollback()
            logger.error(f"💥 任務執行崩潰: {e}")
        finally:
            db.close()

if __name__ == "__main__":
    scraper = PriceScraper()
    for plat in ["Momo", "PChome"]:
        scraper.automated_run(plat)