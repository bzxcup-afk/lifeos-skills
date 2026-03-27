#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import requests
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("创建 medication_supplement_list 表")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

# 1. 创建表
print("\n[Step 1] 创建 medication_supplement_list 表")
url = 'https://open.feishu.cn/open-apis/bitable/v1/apps/DtWnbquyZaIj9xsWLSIcagjQnAc/tables'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
data = {'table': {'name': 'medication_supplement_list', 'description': '药品补剂列表'}}

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
    {"field_name": "item_id", "field_type": 1},
    {"field_name": "profile_id", "field_type": 1},
    {"field_name": "name", "field_type": 1},
    {"field_name": "item_type", "field_type": 3, "property": {"options": [{"name": "补剂"}, {"name": "药品"}]}},
    {"field_name": "dosage", "field_type": 1},
    {"field_name": "frequency", "field_type": 3, "property": {"options": [{"name": "每天"}, {"name": "每周"}, {"name": "按需"}]}},
    {"field_name": "timing", "field_type": 4, "property": {"options": [{"name": "早餐前"}, {"name": "早餐后"}, {"name": "午餐前"}, {"name": "午餐后"}, {"name": "晚餐前"}, {"name": "晚餐后"}, {"name": "睡前"}]}},
    {"field_name": "with_food", "field_type": 3, "property": {"options": [{"name": "随餐"}, {"name": "空腹"}, {"name": "均可"}]}},
    {"field_name": "start_date", "field_type": 5},
    {"field_name": "end_date", "field_type": 5},
    {"field_name": "purpose", "field_type": 1},
    {"field_name": "precautions", "field_type": 1},
    {"field_name": "source_type", "field_type": 3, "property": {"options": [{"name": "医生建议"}, {"name": "用户设定"}, {"name": "系统建议"}]}},
    {"field_name": "status", "field_type": 3, "property": {"options": [{"name": "启用"}, {"name": "暂停"}, {"name": "已结束"}]}},
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

print("\n" + "="*60)
print(f"medication_supplement_list 表创建完成")
print(f"Table ID: {table_id}")
print(f"字段总数: {success + skip}")
print("="*60)
