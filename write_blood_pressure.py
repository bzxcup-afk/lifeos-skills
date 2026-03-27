#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import datetime
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("写入血压数据")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

# 血压数据：收缩压124，舒张压80
# 存储为 JSON 格式在 key_metrics_json 字段

record_date_ts = int(datetime.datetime(2026, 3, 20).timestamp() * 1000)

fields = {
    "record_date": record_date_ts,
    "record_type": "体检",
    "institution": "家庭自测",
    "complaint_or_reason": "早上自测血压",
    "key_metrics_json": '{"blood_pressure": {"systolic": 124, "diastolic": 80}, "unit": "mmHg"}',
    "abnormal_items": "收缩压偏高(124mmHg，正常<120)",
    "diagnosis": "血压偏高（正常高值）",
    "tags": ["心血管"],
    "summary_for_system": "收缩压80，舒张压124，属于正常高值范围，需关注",
    "follow_up_needed": True
}

record_id, err = bitable_ops.create_record(token, "medical_records", fields)

if err:
    print(f"[ERROR] {err}")
else:
    print(f"[OK] Medical Record 创建成功")
    print(f"     record_id: {record_id}")
    print()
    print("数据摘要:")
    print(f"  日期: 2026-03-20")
    print(f"  收缩压: 124 mmHg (偏高)")
    print(f"  舒张压: 80 mmHg (正常)")
    print(f"  状态: 需关注")

print("="*60)
