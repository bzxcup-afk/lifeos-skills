#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import requests
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("创建 weekly_plan 表")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

# 1. 创建表
print("\n[Step 1] 创建 weekly_plan 表")
url = 'https://open.feishu.cn/open-apis/bitable/v1/apps/DtWnbquyZaIj9xsWLSIcagjQnAc/tables'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
data = {'table': {'name': 'weekly_plan', 'description': '每周计划表'}}

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
    {"field_name": "weekly_plan_id", "field_type": 1},
    {"field_name": "profile_id", "field_type": 1},
    {"field_name": "week_start", "field_type": 5},
    {"field_name": "week_end", "field_type": 5},
    {"field_name": "plan_status", "field_type": 3, "property": {"options": [{"name": "草稿"}, {"name": "生效中"}, {"name": "已完成"}, {"name": "已调整"}]}},
    {"field_name": "phase", "field_type": 3, "property": {"options": [{"name": "减脂期"}, {"name": "增肌期"}, {"name": "维持期"}, {"name": "恢复期"}]}},
    {"field_name": "weekly_goal", "field_type": 1},
    {"field_name": "focus_areas", "field_type": 4, "property": {"options": [{"name": "训练"}, {"name": "饮食"}, {"name": "睡眠"}, {"name": "恢复"}, {"name": "补剂"}, {"name": "医疗"}]}},
    {"field_name": "training_target", "field_type": 1},
    {"field_name": "diet_target", "field_type": 1},
    {"field_name": "supplement_target", "field_type": 1},
    {"field_name": "medical_notes", "field_type": 1},
    {"field_name": "key_risks", "field_type": 1},
    {"field_name": "adjustment_strategy", "field_type": 1},
    {"field_name": "success_criteria", "field_type": 1},
    {"field_name": "triggered_rules", "field_type": 1},
    {"field_name": "source_summary", "field_type": 1},
    {"field_name": "execution_score", "field_type": 2, "property": {"formatter": "0"}},
    {"field_name": "review_summary", "field_type": 1},
    {"field_name": "next_week_notes", "field_type": 1},
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
print(f"weekly_plan 表创建完成")
print(f"Table ID: {table_id}")
print(f"字段总数: {success + skip}")
print("="*60)
