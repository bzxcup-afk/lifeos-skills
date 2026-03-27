#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

token = bitable_ops.get_token()

print("="*60)
print("验证写入数据")
print("="*60)

# 检查 profile
records, _ = bitable_ops.read_records(token, 'profile', limit=5)
if records:
    print("\nProfile 表:")
    for r in records:
        fields = r.get('fields', {})
        name = fields.get('name', 'N/A')
        height = fields.get('height_cm', 'N/A')
        print(f"  - name: {name}, height_cm: {height}")

# 检查 daily_log
records, _ = bitable_ops.read_records(token, 'daily_log', limit=5)
if records:
    print("\nDaily Log 表:")
    for r in records:
        fields = r.get('fields', {})
        date = fields.get('date', 'N/A')
        weight = fields.get('weight_kg', 'N/A')
        notes = fields.get('body_status_notes', 'N/A')
        print(f"  - date: {date}, weight_kg: {weight}")
        print(f"    notes: {notes}")

print("\n" + "="*60)
print("验证完成")
print("="*60)
