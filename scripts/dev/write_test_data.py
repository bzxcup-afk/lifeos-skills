#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("写入用户数据")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

print("[OK] Token OK")

# 1. 写入 profile 表 - 身高
print("\n[Step 1] 写入 profile 表 - 身高")
profile_fields = {
    "name": "金",
    "height_cm": 183
}
record_id, err = bitable_ops.create_record(token, "profile", profile_fields)
if err:
    print(f"[ERROR] {err}")
else:
    print(f"[OK] Profile 创建成功, record_id: {record_id}")

# 2. 写入 daily_log 表 - 体重
print("\n[Step 2] 写入 daily_log 表 - 体重")
daily_fields = {
    "date": "2026-03-20",
    "weight_kg": 90.5,
    "body_status_notes": "首次记录体重"
}
record_id, err = bitable_ops.create_record(token, "daily_log", daily_fields)
if err:
    print(f"[ERROR] {err}")
else:
    print(f"[OK] Daily Log 创建成功, record_id: {record_id}")

print("\n" + "="*60)
print("写入完成")
print("="*60)
