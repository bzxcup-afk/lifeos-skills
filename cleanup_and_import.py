# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from scripts.db import get_connection
from health_data.entry import import_from_screenshot

# 清理 2026-04-02 的所有数据
with get_connection() as conn:
    conn.execute("DELETE FROM health_data_logs WHERE date = '2026-04-02'")
    print("Deleted 2026-04-02 records")

# 导入完整数据（8条）
llm_json = {
    'source_app': 'xiaomi_health',
    'records': [
        {'metric_type': '步数', 'value': 5665, 'unit': '步', 'date': '2024-04-02', 'granularity': 'day', 'raw_text': '5665 /6000步'},
        {'metric_type': '卡路里', 'value': 209, 'unit': '千卡', 'date': '2024-04-02', 'granularity': 'day', 'raw_text': '209 /500千卡'},
        {'metric_type': '中高强度', 'value': 4, 'unit': '分钟', 'date': '2024-04-02', 'granularity': 'day', 'raw_text': '4 /30分钟'},
        {'metric_type': '活动次数', 'value': 2, 'unit': '次', 'date': '2024-04-02', 'granularity': 'day', 'raw_text': '活动次数 2 次'},
        {'metric_type': '睡眠时长', 'value': 436, 'unit': '分钟', 'date': '2024-04-02', 'granularity': 'day', 'raw_text': '7时16分'},
        {'metric_type': '心率', 'value': 83, 'unit': '次/分', 'date': '2024-04-02', 'granularity': 'instant', 'raw_text': '83次/分 4月2日 15:52'},
        {'metric_type': '血糖', 'value': 5.0, 'unit': 'mmol/L', 'date': '2024-04-02', 'granularity': 'instant', 'raw_text': '5.0 mmol/L 2月18日 17:42'},
        {'metric_type': '体重', 'value': 91.0, 'unit': 'KG', 'date': '2024-04-02', 'granularity': 'instant', 'raw_text': '91.00KG 2月3日 09:22'}
    ]
}

result = import_from_screenshot(
    profile_id='001',
    user_id='ou_fde56bd8d48eca22b3d57ab990ee4f02',
    image_path='C:\\Users\\Jin\\.openclaw\\media\\inbound\\5dbcf2cc-8e2e-4f17-9db8-0d47500b6828.jpg',
    llm_json=llm_json
)

print(f"\nImport result: success={result['success']}")
print(f"Reply: {result['reply_message']}")

# 验证
print("\n=== Database verification ===")
with get_connection() as conn:
    cur = conn.execute("SELECT COUNT(*) as cnt FROM health_data_logs WHERE date = '2026-04-02'")
    print(f"Total 2026-04-02 records: {cur.fetchone()['cnt']}")
    cur = conn.execute("SELECT metric_type, value, unit FROM health_data_logs WHERE date = '2026-04-02' ORDER BY metric_type")
    for r in cur.fetchall():
        print(f"  {r['metric_type']}: {r['value']} {r['unit']}")
