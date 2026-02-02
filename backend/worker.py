import os
import logging
from celery import Celery
from celery.schedules import crontab  # 💡 必須引入以支持 Cron 定時格式
# 💡 確保引入 scraper 中的類別與日誌配置
from scraper import PriceScraper, setup_logging 

# 1. 確保初始化日誌配置，這樣 Celery 執行時的日誌才會同步寫入檔案與控制台
logger = setup_logging()

# --- 1. Celery 基礎配置 ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# 🚀 專業配置優化
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True,
    # 💡 爬蟲關鍵：Prefetch 設為 1，避免單個 Worker 領取過多任務導致其他 Worker 閒置
    worker_prefetch_multiplier=1,
    task_track_started=True,
    
    # --- 🕒 自動化排程核心配置 (Beat Schedule) ---
    beat_schedule={
        # 名稱：全平台價格定時更新
        'auto-scrape-every-6-hours': {
            'task': 'worker.scrape_all_platforms',  # 💡 指向下方定義的 Task Name
            'schedule': crontab(minute=0, hour='*/2'), # 每 2 小時執行一次 (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22 點)
            # 測試用 (每 5 分鐘跑一次)：'schedule': 300.0, 
        },
    },
    
    # 限制頻率，保護 IP 不被電商封鎖
    task_annotations={
        'worker.scrape_all_platforms': {'rate_limit': '1/m'} 
    }
)

# --- 2. 定義 Celery Tasks ---

# 💡 顯式指定 name="worker.scrape_all_platforms" 以確保 Scheduler 派發與 Worker 接收一致
@celery_app.task(
    bind=True, 
    name="worker.scrape_all_platforms", 
    max_retries=3, 
    default_retry_delay=300
)
def scrape_all_platforms(self):
    """
    排程任務：執行全平台價格更新
    """
    logger.info("📅 [Celery] 接收到排程任務：開始全平台爬取")
    
    try:
        # 在任務內部實例化，確保資料庫連線獨立
        scraper = PriceScraper()
        for platform in ["Momo", "PChome"]:
            logger.info(f"正在處理平台: {platform}")
            scraper.automated_run(platform)
            
        return {"status": "success", "msg": "All platforms updated"}
    except Exception as exc:
        logger.error(f"❌ 全平台任務執行失敗: {exc}")
        raise self.retry(exc=exc)

@celery_app.task(
    bind=True, 
    name="worker.scrape_single_product_task", 
    max_retries=2
)
def scrape_single_product_task(self, platform_name, product_id_on_platform):
    """
    單一商品即時爬取任務 (通常由 API 手動觸發)
    """
    logger.info(f"⚡ [Celery] 即時更新指令：{platform_name} (ID: {product_id_on_platform})")
    try:
        scraper = PriceScraper()
        if platform_name.lower() == "momo":
            price = scraper.scrape_momo(product_id_on_platform)
        else:
            price = scraper.scrape_pchome(product_id_on_platform)
            
        if price and price > 0:
            logger.info(f"✅ 即時抓取成功：價格 ${price}")
            return {"status": "success", "price": price}
        else:
            logger.warning(f"⚠️ 抓取結束，但未獲得有效價格 (ID: {product_id_on_platform})")
            return {"status": "failed", "reason": "Price not found"}
    except Exception as exc:
        logger.error(f"❌ 即時任務異常: {exc}")
        raise self.retry(exc=exc)