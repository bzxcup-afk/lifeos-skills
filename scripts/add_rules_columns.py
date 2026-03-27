#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充 rules 表缺失的字段

rules 表现有11个字段，需要补充20个字段
"""

import sys
sys.path.insert(0, '.')
from db import execute, query_many

def main():
    print('=' * 70)
    print('补充 rules 表缺失的字段')
    print('=' * 70)
    
    # 需要补充的字段列表
    columns_to_add = [
        # 规则描述和分类
        ('rule_description', 'TEXT', None, '规则详细描述'),
        ('rule_category', 'TEXT', None, '规则类别（如：健康/用药/运动）'),
        
        # 触发条件扩展
        ('trigger_events', 'TEXT', None, '触发事件列表（JSON）'),
        
        # 动作扩展
        ('action_params', 'TEXT', None, '动作参数（JSON）'),
        
        # 有效期
        ('effective_date', 'TEXT', None, '生效日期'),
        ('expiry_date', 'TEXT', None, '过期日期'),
        
        # 适用范围
        ('applies_to_profiles', 'TEXT', None, '适用的用户（JSON数组）'),
        ('applies_to_groups', 'TEXT', None, '适用的群组（JSON数组）'),
        ('exclusions', 'TEXT', None, '排除条件（JSON）'),
        
        # 审核信息
        ('reviewed_by', 'TEXT', None, '审核人'),
        ('reviewed_at', 'TEXT', None, '审核时间'),
        ('review_notes', 'TEXT', None, '审核备注'),
        
        # 统计信息
        ('evidence_count', 'INTEGER', 0, '证据数量'),
        ('success_rate', 'REAL', None, '成功率（0-1）'),
        ('last_triggered_at', 'TEXT', None, '最后触发时间'),
        ('trigger_count', 'INTEGER', 0, '触发次数'),
        
        # 版本控制
        ('created_by', 'TEXT', None, '创建人'),
        ('updated_by', 'TEXT', None, '更新人'),
        ('updated_at', 'TEXT', None, '更新时间'),
        ('version', 'INTEGER', 1, '版本号'),
    ]
    
    # 获取现有列
    existing = query_many('PRAGMA table_info(rules)')
    existing_names = [col['name'] for col in existing]
    
    print(f'\n现有字段: {len(existing_names)} 个')
    print(f'需要补充: {len(columns_to_add)} 个')
    
    added = 0
    skipped = 0
    errors = 0
    
    print('\n开始补充字段...')
    print('-' * 70)
    
    for col_name, col_type, default, description in columns_to_add:
        # 检查是否已存在
        if col_name in existing_names:
            print(f'  [已存在] {col_name}')
            skipped += 1
            continue
        
        # 添加列
        try:
            if default is not None:
                sql = f'ALTER TABLE rules ADD COLUMN {col_name} {col_type} DEFAULT {default}'
            else:
                sql = f'ALTER TABLE rules ADD COLUMN {col_name} {col_type}'
            execute(sql)
            print(f'  [已添加] {col_name} ({col_type}) - {description}')
            added += 1
        except Exception as e:
            print(f'  [错误] {col_name}: {e}')
            errors += 1
    
    print('-' * 70)
    print('\n' + '=' * 70)
    print('结果汇总')
    print('=' * 70)
    print(f'  成功添加: {added} 个')
    print(f'  已存在跳过: {skipped} 个')
    print(f'  错误: {errors} 个')
    
    # 检查最终字段数
    final = query_many('PRAGMA table_info(rules)')
    print(f'\n  rules 表现在共有: {len(final)} 个字段')
    print('=' * 70)

if __name__ == '__main__':
    main()
