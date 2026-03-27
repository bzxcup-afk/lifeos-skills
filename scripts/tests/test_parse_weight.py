#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import re
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

text = "我身高183，体重今天早上181斤"

print("="*60)
print("用户输入解析")
print("="*60)
print(f"原始输入: {text}")
print()

# 基础解析
info = bitable_ops.parse_user_input(text)
print(f"基础解析结果:")
print(f"  类型: {info['type']}")
print(f"  数据: {info['data']}")
print()

# 额外解析身高体重
height = re.search(r'(\d+)\s*(?:cm|厘米|m)?', text, re.IGNORECASE)
weight = re.search(r'(\d+\.?\d*)\s*(?:斤|kg|公斤)', text)

if height:
    h = int(height.group(1))
    print(f"身高提取: {h} cm")

if weight:
    w = float(weight.group(1))
    w_kg = w / 2  # 斤转公斤
    print(f"体重提取: {w} 斤 = {w_kg} kg")

print()
print("="*60)
print("建议操作")
print("="*60)
print("1. 身高(183cm) -> 写入 profile 表的 height_cm 字段")
print("2. 今日体重(90.5kg) -> 写入 daily_log 表的 weight_kg 字段")
print()
print("是否写入表格？")
