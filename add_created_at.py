#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import requests
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("补充 created_at 字段 (使用日期类型)")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

tables_to_fix = [
    ("weekly_plan", "tblkHBrurIm6f0j0"),
    ("medication_supplement_list", "tblDX3SHgxlFTsPI"),
]

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

for table_name, table_id in tables_to_fix:
    print(f"\n[检查] {table_name}")
    
    # 检查是否已有 created_at
    url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/DtWnbquyZaIj9xsWLSIcagjQnAc/tables/{table_id}/fields'
    resp = requests.get(url, headers=headers, timeout=30)
    result = resp.json()
    
    if result.get('code') != 0:
        print(f"  [ERROR] {result.get('msg')}")
        continue
    
    existing_fields = result.get('data', {}).get('items', [])
    existing_names = [f.get('field_name') for f in existing_fields]
    
    if 'created_at' not in existing_names:
        # 用日期类型添加
        data = {'field_name': 'created_at', 'type': 5}  # 日期类型
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        
        if result.get('code') == 0:
            print(f"  [OK] created_at 已添加 (日期类型)")
        elif result.get('code') == 4007:
            print(f"  [SKIP] created_at 已存在")
        else:
            print(f"  [FAIL] created_at: {result.get('code')}")
    else:
        print(f"  [OK] created_at 已存在")
    
    time.sleep(0.2)

print("\n" + "="*60)
print("created_at 补充完成")
print("="*60)
print("\n说明: created_at 使用日期类型(type=5)替代创建时间(type=24)")
print("      updated_at 已使用修改时间(type=23)")
