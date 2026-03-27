#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看数据库表结构"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import query_many

def show_table_schema(table_name):
    """显示表结构"""
    print(f"\n=== {table_name} 表结构 ===")
    schema = query_many(f'PRAGMA table_info({table_name})')
    
    for col in schema:
        pk = "PK" if col.get('pk') else ""
        null = "NULL" if col.get('notnull') == 0 else "NOT NULL"
        print(f"  {col['name']:20s} {col['type']:10s} {null:10s} {pk}")
    
    return len(schema)

def show_tables():
    """显示所有表"""
    print("=== 数据库中的所有表 ===")
    tables = query_many("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for t in tables:
        print(f"  - {t['name']}")
    return [t['name'] for t in tables]

def compare_with_feishu():
    """与飞书 Bitable 原表字段对比说明"""
    print("\n" + "="*60)
    print("与飞书 Bitable 原表字段对比说明")
    print("="*60)
    
    print("""
【核心字段已保留】
- profile_id: 用户标识（替代飞书的 record_id 关联）
- date: 日期
- sleep_hours: 睡眠时长
- sleep_quality: 睡眠质量
- fatigue_score: 疲劳度
- energy_score: 精力评分
- weight_kg: 体重（kg）
- had_training: 是否训练
- training_brief: 训练简述
- diet_status: 饮食状态
- body_status_notes: 身体状态备注
- today_summary: 今日总结
- state_tags: 状态标签
- created_at, updated_at: 时间戳

【飞书特有字段已移除/简化】
- record_id: 飞书独有，本地使用自增 log_id
- 飞书特有的 lookup、formula 字段：本地不需要
- 多人协作字段（created_by, updated_by 等）：单机版不需要

【新增本地字段】
- log_id: 本地自增主键
- profile_id: 本地用户标识（001/002/003/004）
""")

if __name__ == '__main__':
    # 显示所有表
    tables = show_tables()
    
    # 显示主要表结构
    main_tables = ['profiles', 'daily_logs', 'events', 'medical_records', 
                   'weekly_plans', 'medications', 'health_evaluations']
    
    total_fields = 0
    for table in main_tables:
        if table in tables:
            count = show_table_schema(table)
            total_fields += count
    
    print(f"\n总计: {len([t for t in main_tables if t in tables])} 张核心表, {total_fields} 个字段")
    
    # 对比说明
    compare_with_feishu()
