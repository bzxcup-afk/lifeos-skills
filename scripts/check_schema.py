#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的数据库表结构检查脚本

对比 SQLite 本地表结构和飞书 Bitable 原表结构，找出缺失的字段
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import query_many

def get_table_columns(table_name):
    """获取表的列信息"""
    columns = query_many(f"PRAGMA table_info({table_name})", ())
    return {col['name']: col['type'] for col in columns}

def check_all_tables():
    """检查所有表的完整性"""
    
    # 获取所有表
    tables = query_many(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
        ()
    )
    
    print("=" * 80)
    print("数据库表结构全面检查报告")
    print("=" * 80)
    print(f"\n共有 {len(tables)} 张表:\n")
    
    # 详细的表结构检查
    table_checks = {
        'profiles': {
            'required': [
                'profile_id', 'name', 'gender', 'birth_date', 'height_cm', 'weight_kg',
                'blood_type', 'resting_heart_rate', 'waist_cm', 'hip_cm',
                'body_goal', 'current_stage', 'health_concerns', 'family_history',
                'lifestyle_habits', 'diet_preferences', 'training_base', 'health_goal'
            ],
            'optional': ['created_at', 'updated_at']
        },
        'daily_logs': {
            'required': [
                'log_id', 'profile_id', 'date', 'sleep_hours', 'sleep_quality',
                'fatigue_score', 'energy_score', 'weight_kg', 'had_training',
                'training_brief', 'diet_status', 'body_status_notes', 'today_summary', 'state_tags'
            ],
            'optional': ['created_at', 'updated_at']
        },
        'events': {
            'required': ['event_id', 'profile_id', 'event_date', 'event_type', 'event_description'],
            'optional': ['impact_level', 'related_metrics', 'created_at']
        },
        'medical_records': {
            'required': ['record_id', 'profile_id', 'record_date', 'record_type', 'complaint_or_reason'],
            'optional': ['diagnosis', 'key_metrics_json', 'treatment_summary', 'tags', 'summary_for_system', 'created_at']
        },
        'weekly_plans': {
            'required': ['plan_id', 'profile_id', 'week_start'],
            'optional': ['week_end', 'plan_status', 'weekly_goal', 'key_focus', 'risk_notes', 'adjustment_principles', 'created_at', 'updated_at']
        },
        'medications': {
            'required': ['med_id', 'profile_id', 'drug_name'],
            'optional': ['dosage', 'time_slot', 'is_active', 'created_at']
        },
        'health_evaluations': {
            'required': ['eval_id', 'profile_id'],
            'optional': [
                'eval_date', 'data_source_desc', 'data_time_range', 'data_coverage',
                'confidence_score', 'cardio_score', 'strength_score', 'metabolism_score',
                'recovery_score', 'execution_score', 'total_score', 'risk_signals',
                'overall_status', 'main_issues', 'recommended_actions', 'brief_report',
                'chart_data_json', 'explanation_json', 'eval_age', 'eval_gender',
                'eval_training_base', 'eval_health_goal', 'missing_fields', 'created_at'
            ]
        }
    }
    
    # 检查每张表
    total_issues = []
    
    for table_name, expected in table_checks.items():
        print(f"\n{'─' * 80}")
        print(f"检查表: {table_name}")
        print('─' * 80)
        
        # 获取实际列
        actual_columns = get_table_columns(table_name)
        
        if not actual_columns:
            print(f"  ❌ 表不存在或无法读取")
            total_issues.append((table_name, "表不存在"))
            continue
        
        print(f"  实际列数: {len(actual_columns)}")
        
        # 检查必需字段
        missing_required = []
        for field in expected['required']:
            if field not in actual_columns:
                missing_required.append(field)
        
        if missing_required:
            print(f"  ❌ 缺失必需字段 ({len(missing_required)}个):")
            for field in missing_required:
                print(f"      - {field}")
            total_issues.append((table_name, f"缺失必需字段: {', '.join(missing_required[:5])}{'...' if len(missing_required) > 5 else ''}"))
        else:
            print(f"  ✅ 所有必需字段齐全")
        
        # 检查可选字段
        missing_optional = [f for f in expected['optional'] if f not in actual_columns]
        if missing_optional:
            print(f"  ⚠️  缺失可选字段 ({len(missing_optional)}个): {', '.join(missing_optional[:3])}{'...' if len(missing_optional) > 3 else ''}")
    
    # 总结
    print(f"\n{'=' * 80}")
    print("检查总结")
    print('=' * 80)
    
    if total_issues:
        print(f"\n发现 {len(total_issues)} 个问题:")
        for table, issue in total_issues:
            print(f"  - {table}: {issue}")
        print("\n建议: 运行迁移脚本添加缺失的字段")
    else:
        print("\n✅ 所有表结构完整，无缺失字段")
    
    print('=' * 80)

if __name__ == '__main__':
    check_all_tables()
