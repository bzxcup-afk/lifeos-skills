#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import datetime
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops
import requests

print("="*60)
print("写入训练记录")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

# 1. 先查询今天的 daily_log 记录
print("\n[Step 1] 查询今日 daily_log")
records, err = bitable_ops.read_records(token, 'daily_log', limit=10)

today_record = None
if records:
    # 找今天的记录
    for r in records:
        fields = r.get('fields', {})
        date_val = fields.get('date', '')
        # 检查是否是今天的记录
        if '2026-03-20' in str(date_val) or date_val == 1773936000000:
            today_record = r
            print(f"找到今日记录: record_id={r.get('record_id')}")
            break

if not today_record:
    print("今日没有记录，需要先创建")
    # 创建今日记录
    fields = {
        'date': 1773936000000,
        'had_training': True,
        'training_brief': '篮球 2小时',
        'body_status_notes': '下午打球'
    }
    record_id, err = bitable_ops.create_record(token, 'daily_log', fields)
    if err:
        print(f"[ERROR] 创建 daily_log 失败: {err}")
    else:
        print(f"[OK] 创建 daily_log 成功: {record_id}")
else:
    # 更新现有记录
    print(f"\n[Step 2] 更新 daily_log record_id={today_record.get('record_id')}")
    record_id = today_record.get('record_id')
    url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/DtWnbquyZaIj9xsWLSIcagjQnAc/tables/tbl9i2SehAhTZKrg/records/{record_id}'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {
        'fields': {
            'had_training': True,
            'training_brief': '篮球 2小时',
            'body_status_notes': '下午打了2小时篮球'
        }
    }
    resp = requests.put(url, headers=headers, json=data, timeout=30)
    result = resp.json()
    if result.get('code') == 0:
        print(f"[OK] daily_log 更新成功")
    else:
        print(f"[ERROR] daily_log 更新失败: {result.get('msg')}")

# 2. 创建 event_log 记录
print(f"\n[Step 3] 创建 event_log 训练事件")
event_fields = {
    'event_datetime': 1773936000000,
    'related_date': 1773936000000,
    'event_type': '训练',
    'event_title': '篮球训练',
    'description': '打了2小时篮球',
    'impact_scope': ['训练', '恢复'],
    'severity': '中',
    'expected_duration': '当天',
    'recovery_needed': True,
    'system_interpretation': '中等强度有氧运动，有助于心肺功能'
}

record_id, err = bitable_ops.create_record(token, 'event_log', event_fields)
if err:
    print(f"[ERROR] event_log 创建失败: {err}")
else:
    print(f"[OK] event_log 创建成功: {record_id}")

print("\n" + "="*60)
print("训练记录写入完成")
print("="*60)
print("\n数据摘要:")
print("  日期: 2026-03-20")
print("  训练: 篮球 2小时")
print("  强度: 中等")
print("  恢复需求: 是")
