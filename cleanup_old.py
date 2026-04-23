# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from scripts.db import get_connection

# 清理测试数据（2024年的和重复的2026年数据）
with get_connection() as conn:
    # 删除2024年的数据
    conn.execute("DELETE FROM health_data_logs WHERE date < '2025-01-01'")
    # 删除同一批次导入的重复数据（保留最早一条）
    conn.execute("""
        DELETE FROM health_data_logs 
        WHERE id NOT IN (
            SELECT MIN(id) FROM health_data_logs 
            WHERE date = '2026-04-02'
            GROUP BY metric_type, value, date
        )
        AND date = '2026-04-02'
    """)

print("Cleanup done")

# 验证
with get_connection() as conn:
    cur = conn.execute("SELECT COUNT(*) as cnt FROM health_data_logs")
    print(f"Total records: {cur.fetchone()['cnt']}")
    cur = conn.execute("SELECT metric_type, value, date FROM health_data_logs ORDER BY date DESC, metric_type LIMIT 10")
    for r in cur.fetchall():
        print(f"  {r['date']} | {r['metric_type']} | {r['value']}")
