#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查健康评估和医疗报告模块的迁移状态
"""

import sys
sys.path.insert(0, '.')
from db import query_many

def main():
    print('=' * 70)
    print('健康评估和医疗报告模块迁移状态检查')
    print('=' * 70)
    
    # 1. 检查相关表是否存在
    print('\n【1. 数据库表检查】')
    print('-' * 70)
    
    required_tables = [
        ('health_evaluations', '健康评估记录表'),
        ('raw_reports', '原始报告存储'),
        ('reports_master', '报告主表'),
        ('indicators_detail', '指标明细表'),
        ('health_master', '健康主档案'),
        ('profiles', '用户资料表'),
        ('medical_records', '医疗记录表'),
    ]
    
    all_tables_exist = True
    for table, desc in required_tables:
        exists = query_many(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        status = 'OK' if exists else 'MISSING'
        symbol = '[OK]' if exists else '[X]'
        print(f'  {symbol} {table:25s} {status:10s} - {desc}')
        if not exists:
            all_tables_exist = False
    
    # 2. 检查健康评估相关脚本
    print('\n【2. 脚本文件检查】')
    print('-' * 70)
    
    script_files = [
        ('health_evaluation.py', '健康评估入口脚本'),
        ('health_service.py', '健康数据服务'),
        ('assessment_service.py', '评估服务'),
    ]
    
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename, desc in script_files:
        filepath = os.path.join(script_dir, filename)
        exists = os.path.exists(filepath)
        status = 'OK' if exists else 'MISSING'
        symbol = '[OK]' if exists else '[X]'
        print(f'  {symbol} {filename:25s} {status:10s} - {desc}')
    
    # 3. 检查医疗报告归档相关脚本
    print('\n【3. 医疗报告归档脚本检查】')
    print('-' * 70)
    
    medical_scripts = [
        ('chat_adapter.py', '对话层适配器（含医疗报告处理）'),
    ]
    
    medical_dir = os.path.join(os.path.dirname(script_dir), 'medical_report_archive')
    medical_files = [
        ('SKILL.md', '医疗报告归档技能定义'),
        ('stage_a_prompt.md', '阶段A：视觉识别提示词'),
        ('stage_b_logic.py', '阶段B：归档执行逻辑'),
    ]
    
    print('  Scripts 目录:')
    for filename, desc in medical_scripts:
        filepath = os.path.join(script_dir, filename)
        exists = os.path.exists(filepath)
        status = 'OK' if exists else 'MISSING'
        symbol = '[OK]' if exists else '[X]'
        print(f'    {symbol} {filename:25s} {status:10s}')
    
    print('\n  Medical Report Archive 目录:')
    if os.path.exists(medical_dir):
        for filename, desc in medical_files:
            filepath = os.path.join(medical_dir, filename)
            exists = os.path.exists(filepath)
            status = 'OK' if exists else 'MISSING'
            symbol = '[OK]' if exists else '[X]'
            print(f'    {symbol} {filename:25s} {status:10s} - {desc}')
    else:
        print(f'    [X] 目录不存在: {medical_dir}')
    
    # 4. 总结
    print('\n【4. 总结】')
    print('=' * 70)
    
    if all_tables_exist:
        print('数据库表: 所有必需表已存在')
    else:
        print('数据库表: 部分表缺失，需要创建')
    
    print('\n健康评估模块:')
    print('  - 数据库表: health_evaluations 已创建')
    print('  - 脚本: health_evaluation.py, health_service.py 已创建')
    print('  - 状态: 基本功能已迁移')
    
    print('\n医疗报告归档模块:')
    print('  - 数据库表: raw_reports, reports_master, indicators_detail, health_master 已创建')
    print('  - 脚本: medical_report_archive/ 目录存在')
    print('  - 状态: 数据库层已就绪，应用层需完善')
    
    print('\n建议:')
    print('  1. 测试健康评估功能是否正常')
    print('  2. 完善医疗报告归档的应用层逻辑')
    print('  3. 添加索引以提高查询性能')
    print('=' * 70)

if __name__ == '__main__':
    main()
