#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查缺失的医疗报告相关表
"""

import sys
sys.path.insert(0, '.')
from db import query_many

def main():
    print('=' * 70)
    print('检查医疗报告相关表')
    print('=' * 70)
    
    # 获取所有表
    tables = query_many(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        ()
    )
    existing = [t['name'] for t in tables]
    
    print('\n当前数据库中的表:')
    for name in existing:
        is_medical = any(x in name for x in ['medical', 'report', 'indicator', 'health_master', 'raw_'])
        marker = ' [医疗]' if is_medical else ''
        print(f'  {name}{marker}')
    
    # 检查缺失的医疗报告表
    print('\n' + '=' * 70)
    print('医疗报告相关表检查')
    print('=' * 70)
    
    expected_tables = {
        'raw_reports': '原始报告存储（OCR识别后的原始数据）',
        'reports_master': '报告主表（医疗报告的汇总信息）',
        'indicators_detail': '指标明细（各项检查指标的详细数据）',
        'health_master': '健康主档案（个人的健康汇总档案）'
    }
    
    print('\n期望的医疗报告表:')
    all_missing = []
    for table, desc in expected_tables.items():
        exists = table in existing
        status = '已存在' if exists else '缺失'
        symbol = '[OK]' if exists else '[X]'
        print(f'  {symbol} {table:25s} {status:10s} - {desc}')
        if not exists:
            all_missing.append(table)
    
    print('\n' + '=' * 70)
    if all_missing:
        print(f'缺失 {len(all_missing)} 个医疗报告表:')
        for t in all_missing:
            print(f'  - {t}')
        print('\n建议: 创建这些表以支持医疗报告归档功能')
    else:
        print('所有医疗报告表已存在！')
    print('=' * 70)

if __name__ == '__main__':
    main()
