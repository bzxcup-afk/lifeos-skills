#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import requests
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("更新今日状态记录")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

# 今日记录 ID
record_id = "recveo5pbCzFsd"

# 更新字段
fields = {
    "fatigue_score": 8,
    "mood_score": 5,
    "state_tags": ["高疲劳", "需要恢复", "执行良好"],
    "today_summary": "早上血压偏高(124/80)，下午篮球2小时，晚上感觉疲劳，建议休息恢复",
    "plan_status": "按计划"
}

url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/DtWnbquyZaIj9xsWLSIcagjQnAc/tables/tbl9i2SehAhTZKrg/records/{record_id}'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
data = {'fields': fields}

print(f"更新 record_id={record_id}")
print(f"字段: {fields}")

resp = requests.put(url, headers=headers, json=data, timeout=30)
result = resp.json()

if result.get('code') == 0:
    print("\n[OK] 状态更新成功")
    print()
    print("更新内容:")
    print("  fatigue_score: 8 (高疲劳)")
    print("  mood_score: 5 (一般)")
    print("  state_tags: 高疲劳、需要恢复、执行良好")
    print("  today_summary: 已填写")
else:
    print(f"\n[ERROR] 更新失败: {result.get('msg')}")

print("="*60)
