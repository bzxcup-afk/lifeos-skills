#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# Add script directory to path
script_dir = r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts'
sys.path.insert(0, script_dir)

import bitable_ops

# Test 1: 状态记录
print("="*60)
print("测试 1: 状态记录")
print("="*60)
text = "今天感觉特别累，状态很差"
info = bitable_ops.parse_user_input(text)
print(f"输入: {text}")
print(f"解析结果:")
print(f"  类型: {info['type']}")
print(f"  数据: {info['data']}")
print(f"  需写入: {info['needs_write']}")

# Test 2: 数据输入 - 睡眠
print("\n" + "="*60)
print("测试 2: 数据输入 - 睡眠")
print("="*60)
text = "昨晚只睡了5个小时，质量一般"
info = bitable_ops.parse_user_input(text)
print(f"输入: {text}")
print(f"解析结果:")
print(f"  类型: {info['type']}")
print(f"  数据: {info['data']}")
print(f"  需写入: {info['needs_write']}")

# Test 3: 事件记录
print("\n" + "="*60)
print("测试 3: 事件记录")
print("="*60)
text = "今晚有聚餐，可能要吃多了"
info = bitable_ops.parse_user_input(text)
print(f"输入: {text}")
print(f"解析结果:")
print(f"  类型: {info['type']}")
print(f"  事件: {info['event']}")
print(f"  需写入: {info['needs_write']}")

# Test 4: 请求建议
print("\n" + "="*60)
print("测试 4: 请求建议")
print("="*60)
text = "今天要不要去健身房？"
info = bitable_ops.parse_user_input(text)
print(f"输入: {text}")
print(f"解析结果:")
print(f"  类型: {info['type']}")
print(f"  数据: {info['data']}")

# Test 5: 医疗相关
print("\n" + "="*60)
print("测试 5: 医疗相关")
print("="*60)
text = "体检发现血脂有点高，医生让我注意饮食"
info = bitable_ops.parse_user_input(text)
print(f"输入: {text}")
print(f"解析结果:")
print(f"  类型: {info['type']}")
print(f"  事件: {info['event']}")
print(f"  需写入: {info['needs_write']}")

print("\n" + "="*60)
print("测试完成")
print("="*60)
