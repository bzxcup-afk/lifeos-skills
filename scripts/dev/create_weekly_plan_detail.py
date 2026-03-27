#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import requests
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("创建 weekly_plan_detail 表")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

# 1. 创建表
print("\n[Step 1] 创建 weekly_plan_detail 表")
url = 'https://open.feishu.cn/open-apis/bitable/v1/apps/DtWnbquyZaIj9xsWLSIcagjQnAc/tables'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
data = {'table': {'name': 'weekly_plan_detail', 'description': '每周每日详细计划'}}

resp = requests.post(url, headers=headers, json=data, timeout=30)
result = resp.json()

if result.get('code') == 0:
    table_id = result.get('data', {}).get('table_id')
    print(f"[OK] 表创建成功: {table_id}")
else:
    print(f"[ERROR] {result}")
    sys.exit(1)

time.sleep(0.5)

# 2. 创建字段
print("\n[Step 2] 创建字段")

fields_to_create = [
    {"field_name": "detail_id", "field_type": 1},
    {"field_name": "weekly_plan_id", "field_type": 1},
    {"field_name": "profile_id", "field_type": 1},
    {"field_name": "plan_date", "field_type": 5},
    {"field_name": "weekday", "field_type": 3, "property": {"options": [{"name": "周一"}, {"name": "周二"}, {"name": "周三"}, {"name": "周四"}, {"name": "周五"}, {"name": "周六"}, {"name": "周日"}]}},
    {"field_name": "daily_theme", "field_type": 1},
    {"field_name": "training_detail", "field_type": 1},
    {"field_name": "diet_detail", "field_type": 1},
    {"field_name": "supplement_medication_detail", "field_type": 1},
    {"field_name": "recovery_detail", "field_type": 1},
    {"field_name": "fallback_plan", "field_type": 1},
    {"field_name": "priority_level", "field_type": 3, "property": {"options": [{"name": "高"}, {"name": "中"}, {"name": "低"}]}},
    {"field_name": "notes", "field_type": 1},
]

success = 0
skip = 0

for i, field in enumerate(fields_to_create, 1):
    field_name = field['field_name']
    field_type = field['field_type']
    prop = field.get('property')
    
    url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/DtWnbquyZaIj9xsWLSIcagjQnAc/tables/{table_id}/fields'
    data = {'field_name': field_name, 'type': field_type}
    if prop:
        data['property'] = prop
    
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    result = resp.json()
    
    if result.get('code') == 0:
        success += 1
        print(f"  [{i:2d}] OK   {field_name}")
    elif result.get('code') == 4007:
        skip += 1
        print(f"  [{i:2d}] SKIP {field_name}")
    else:
        print(f"  [{i:2d}] FAIL {field_name}: {result.get('code')}")
    
    time.sleep(0.1)

print(f"\n字段创建完成: OK={success}, SKIP={skip}")

# 3. 补充时间字段
print("\n[Step 3] 补充时间字段")

# updated_at
data = {'field_name': 'updated_at', 'type': 23}
resp = requests.post(url, headers=headers, json=data, timeout=30)
result = resp.json()
if result.get('code') == 0:
    print("  [OK] updated_at (修改时间)")
elif result.get('code') == 4007:
    print("  [SKIP] updated_at exists")
else:
    print(f"  [FAIL] updated_at: {result.get('code')}")

time.sleep(0.2)

# created_at (日期类型)
data = {'field_name': 'created_at', 'type': 5}
resp = requests.post(url, headers=headers, json=data, timeout=30)
result = resp.json()
if result.get('code') == 0:
    print("  [OK] created_at (日期类型)")
elif result.get('code') == 4007:
    print("  [SKIP] created_at exists")
else:
    print(f"  [FAIL] created_at: {result.get('code')}")

print("\n" + "="*60)
print(f"weekly_plan_detail 表创建完成")
print(f"Table ID: {table_id}")
print(f"字段总数: {success + skip + 2}")
print("="*60)
