#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移状态检查脚本
检查哪些模块已迁移到本地 SQLite
"""

import sys
sys.path.insert(0, '.')
from db import query_many

def main():
    print('=' * 70)
    print('LifeOS 本地 SQLite 迁移状态检查')
    print('=' * 70)
    
    # 获取所有表
    tables = query_many(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        ()
    )
    table_names = [t['name'] for t in tables]
    
    print('\n【已迁移到本地 SQLite 的表】')
    print('-' * 70)
    for name in table_names:
        cols = query_many(f'PRAGMA table_info({name})', ())
        print(f'  {name:35s} ({len(cols):3d} 个字段)')
    
    print('\n【功能模块迁移状态】')
    print('-' * 70)
    
    modules = [
        ('用户资料 (profiles)', 'profiles'),
        ('每日记录 (daily_logs)', 'daily_logs'),
        ('事件记录 (events)', 'events'),
        ('医疗记录 (medical_records)', 'medical_records'),
        ('周计划 (weekly_plans)', 'weekly_plans'),
        ('周计划详情 (weekly_plan_details)', 'weekly_plan_details'),
        ('用药管理 (medications)', 'medications'),
        ('服药记录 (medication_logs)', 'medication_logs'),
        ('健康评估 (health_evaluations)', 'health_evaluations'),
        ('健康知识库 (health_knowledge)', 'health_knowledge'),
        ('规则表 (rules)', 'rules'),
    ]
    
    migrated_count = 0
    for module_name, table in modules:
        exists = table in table_names
        status = '已迁移' if exists else '未迁移'
        marker = '[OK]' if exists else '[X]'
        print(f'  {marker} {module_name:40s} {status}')
        if exists:
            migrated_count += 1
    
    print('\n' + '=' * 70)
    print(f'总结: {migrated_count}/{len(modules)} 个核心模块已迁移')
    if migrated_count == len(modules):
        print('✅ 所有核心模块已迁移到本地 SQLite！')
    else:
        missing = [m for m, t in modules if t not in table_names]
        print(f'❌ 未迁移: {", ".join(missing)}')
    print('=' * 70)

if __name__ == '__main__':
    main()
