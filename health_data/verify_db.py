# -*- coding: utf-8 -*-
"""验证数据库表"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.db import get_connection

# 检查表是否存在
with get_connection() as conn:
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("Tables:", [t[0] for t in tables])
    
    if ("health_data_logs",) in tables:
        cols = conn.execute("PRAGMA table_info(health_data_logs)").fetchall()
        print("\nhealth_data_logs columns:")
        for c in cols:
            print(f"  {c[1]} {c[2]}")
