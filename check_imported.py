# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
import sqlite3
from scripts.db import get_db_path

conn = sqlite3.connect(get_db_path())
conn.row_factory = sqlite3.Row
cur = conn.execute("SELECT metric_type, value, date FROM health_data_logs WHERE profile_id='001' ORDER BY date DESC, metric_type LIMIT 20")
rows = cur.fetchall()
print("Recent health data records:")
for r in rows:
    print(f"  {r['date']} | {r['metric_type']} | {r['value']}")
conn.close()
