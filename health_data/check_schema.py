# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from scripts.db import get_db_path

db_path = get_db_path()
print(f"DB path: {db_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Check columns
cur = conn.execute("PRAGMA table_info(health_data_logs)")
cols = cur.fetchall()
print("\nhealth_data_logs columns:")
for c in cols:
    print(f"  {c[1]} {c[2]}")

conn.close()
