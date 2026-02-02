import logging
from logging.handlers import TimedRotatingFileHandler
import os

# 確保 logs 資料夾存在
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logger():
    logger = logging.getLogger("price_tracker")
    logger.setLevel(logging.INFO)

    # 💡 格式設定：模仿 Laravel [時間] 層級: 訊息
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. 終端機輸出 (Console)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 檔案輸出 + 按天切割 (Rotating File)
    # backupCount=7 代表保留最近 7 天的日誌
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "fastapi.log"),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 初始化全域變數
logger = setup_logger()