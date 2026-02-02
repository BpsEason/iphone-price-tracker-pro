import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# --- [專業修正 1] 確保動態載入模型路徑 ---
# 將專案根目錄加入路徑，確保能 import models 
from os.path import dirname, realpath
sys.path.insert(0, dirname(dirname(realpath(__file__))))
from models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- [專業修正 2] 綁定模型 Metadata ---
target_metadata = Base.metadata

def get_url():
    """優先從環境變數獲取連線字串，若無則回傳 None"""
    return os.getenv("DATABASE_URL")

def run_migrations_offline() -> None:
    """離線模式遷移"""
    # 如果環境變數中有連線資訊，優先覆蓋 ini 檔案中的設定
    url = get_url() or config.get_main_option("sqlalchemy.url")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """在線模式遷移"""
    # 獲取 alembic.ini 中的 [alembic] 區塊配置
    section = config.get_section(config.config_ini_section, {})
    
    # 💡 核心邏輯：如果 DATABASE_URL 存在，動態注入到配置中
    url = get_url()
    if url:
        section["sqlalchemy.url"] = url

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()