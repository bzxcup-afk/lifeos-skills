#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import requests
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("检查并补充时间字段")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

# 需要补充的表
tables_to_fix = [
    ("weekly_plan", "tblkHBrurIm6f0j0"),
    ("medication_supplement_list", "tblDX3SHgxlFTsPI"),
]

# 时间字段类型：创建时间=24, 修改时间=23
time_fields = [
    {"field_name": "created_at", "field_type": 24},  # 创建时间
    {"field_name": "updated_at", "field_type": 23},  # 修改时间
]

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

for table_name, table_id in tables_to_fix:
    print(f"\n[检查表] {table_name}")
    
    # 获取现有字段
    url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/DtWnbquyZaIj9xsWLSIcagjQnAc/tables/{table_id}/fields'
    resp = requests.get(url, headers=headers, timeout=30)
    result = resp.json()
    
    if result.get('code') != 0:
        print(f"  [ERROR] 获取字段失败: {result.get('msg')}")
        continue
    
    existing_fields = result.get('data', {}).get('items', [])
    existing_names = [f.get('field_name') for f in existing_fields]
    
    print(f"  现有字段: {len(existing_fields)}")
    
    # 检查缺失的时间字段
    for tf in time_fields:
        if tf['field_name'] not in existing_names:
            # 添加缺失的字段
            data = {'field_name': tf['field_name'], 'type': tf['field_type']}
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            result = resp.json()
            
            if result.get('code') == 0:
                print(f"  [OK] 添加 {tf['field_name']}")
            elif result.get('code') == 4007:
                print(f"  [SKIP] {tf['field_name']} 已存在")
            else:
                print(f"  [FAIL] {tf['field_name']}: {result.get('code')}")
        else:
            print(f"  [OK] {tf['field_name']} 已存在")
        
        time.sleep(0.2)

print("\n" + "="*60)
print("时间字段补充完成")
print("="*60)
