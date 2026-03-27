#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import requests
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

token = bitable_ops.get_token()

# 飞书日期字段需要的时间戳格式（毫秒）
import datetime
ts = int(datetime.datetime(2026, 3, 20).timestamp() * 1000)
print(f"Timestamp for 2026-03-20: {ts}")

data = {
    'fields': {
        'date': ts,
        'weight_kg': 90.5,
        'body_status_notes': '首次记录体重'
    }
}

url = 'https://open.feishu.cn/open-apis/bitable/v1/apps/DtWnbquyZaIj9xsWLSIcagjQnAc/tables/tbl9i2SehAhTZKrg/records'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

resp = requests.post(url, headers=headers, json=data, timeout=30)
result = resp.json()

if result.get('code') == 0:
    record_id = result.get('data', {}).get('record', {}).get('record_id')
    print(f'[OK] Daily Log 创建成功')
    print(f'     record_id: {record_id}')
else:
    print(f'[FAIL] error={result.get("code")}: {result.get("msg")}')
