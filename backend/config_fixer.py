import os
import sys

def fix_configs():
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("❌ 錯誤: 找不到 DATABASE_URL 環境變數")
        return

    # 修復 alembic.ini
    if os.path.exists("alembic.ini"):
        with open("alembic.ini", "r") as f:
            lines = f.readlines()
        with open("alembic.ini", "w") as f:
            for line in lines:
                if line.startswith("sqlalchemy.url ="):
                    f.write(f"sqlalchemy.url = {db_url}\n")
                else:
                    f.write(line)
        print("✅ alembic.ini 連線資訊已更新")

    # 修復 migrations/env.py
    env_path = "migrations/env.py"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
        
        # 注入模型與路徑
        target = 'target_metadata = None'
        replacement = """import sys
from os.path import dirname, realpath
sys.path.insert(0, dirname(dirname(realpath(__file__))))
from models import Base
target_metadata = Base.metadata"""
        
        if target in content:
            with open(env_path, "w") as f:
                f.write(content.replace(target, replacement))
            print("✅ migrations/env.py 已注入模型 Metadata")

if __name__ == "__main__":
    fix_configs()
