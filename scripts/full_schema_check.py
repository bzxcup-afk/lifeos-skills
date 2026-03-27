#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面数据库表结构检查与对比

检查所有表的字段完整性，对比飞书 Bitable 原表结构
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import query_many

def get_table_info(table_name):
    """获取表结构信息"""
    try:
        columns = query_many(f"PRAGMA table_info({table_name})", ())
        return {col['name']: col['type'] for col in columns}
    except:
        return {}

def check_table(table_name, required_fields, optional_fields=None):
    """检查单个表的字段完整性"""
    optional_fields = optional_fields or []
    actual = get_table_info(table_name)
    
    if not actual:
        return {"missing_required": required_fields, "missing_optional": [], "exists": False}
    
    missing_required = [f for f in required_fields if f not in actual]
    missing_optional = [f for f in optional_fields if f not in actual]
    
    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "exists": True,
        "total_fields": len(actual)
    }

def main():
    print("=" * 80)
    print("全面数据库表结构检查")
    print("=" * 80)
    
    # 定义所有表及其必需字段（基于飞书 Bitable 原表结构）
    table_definitions = {
        "profiles": {
            "required": [
                # 基础信息
                "profile_id", "name", "gender", "birth_date", "height_cm", "weight_kg",
                # 体征信息（新增）
                "blood_type", "resting_heart_rate", "waist_cm", "hip_cm",
                # 目标与阶段（新增）
                "body_goal", "current_stage",
                # 健康相关（新增）
                "health_concerns", "family_history", "lifestyle_habits", "diet_preferences",
                # 原有字段
                "training_base", "health_goal"
            ],
            "optional": ["created_at", "updated_at"]
        },
        
        "daily_logs": {
            "required": [
                "log_id", "profile_id", "date",
                "sleep_hours", "sleep_quality", "fatigue_score", "energy_score",
                "weight_kg", "had_training", "training_brief",
                "diet_status", "body_status_notes", "today_summary", "state_tags"
            ],
            "optional": ["created_at", "updated_at"]
        },
        
        "events": {
            "required": ["event_id", "profile_id", "event_date", "event_type", "event_description"],
            "optional": ["impact_level", "related_metrics", "created_at"]
        },
        
        "medical_records": {
            "required": ["record_id", "profile_id", "record_date", "record_type", "complaint_or_reason"],
            "optional": ["diagnosis", "key_metrics_json", "treatment_summary", "tags", "summary_for_system", "created_at"]
        },
        
        "weekly_plans": {
            "required": ["plan_id", "profile_id", "week_start"],
            "optional": ["week_end", "plan_status", "weekly_goal", "key_focus", "risk_notes", "adjustment_principles", "created_at", "updated_at"]
        },
        
        "weekly_plan_details": {
            "required": ["detail_id", "plan_id", "profile_id", "plan_date"],
            "optional": ["weekday", "daily_theme", "training_detail", "diet_detail", "supplement_medication_detail", "recovery_detail", "fallback_plan", "priority_level", "notes"]
        },
        
        "medications": {
            "required": ["med_id", "profile_id", "drug_name"],
            "optional": ["dosage", "time_slot", "is_active", "created_at"]
        },
        
        "medication_logs": {
            "required": ["log_id", "med_id", "profile_id", "date"],
            "optional": ["time_slot", "status", "taken_at"]
        },
        
        "health_evaluations": {
            "required": ["eval_id", "profile_id"],
            "optional": [
                "eval_date", "data_source_desc", "data_time_range", "data_coverage",
                "confidence_score", "cardio_score", "strength_score", "metabolism_score",
                "recovery_score", "execution_score", "total_score", "risk_signals",
                "overall_status", "main_issues", "recommended_actions", "brief_report",
                "chart_data_json", "explanation_json", "eval_age", "eval_gender",
                "eval_training_base", "eval_health_goal", "missing_fields", "created_at"
            ]
        },
        
        "health_knowledge": {
            "required": ["knowledge_id"],
            "optional": ["topic", "content", "category", "tags", "source", "confidence", "created_at"]
        },
        
        "rules": {
            "required": ["rule_id"],
            "optional": ["rule_name", "trigger_conditions", "action", "priority", "enabled", "review_status", "confidence", "tags", "notes", "created_at"]
        }
    }
    
    # 执行检查
    total_issues = []
    total_tables = 0
    total_fields = 0
    
    for table_name, definition in table_definitions.items():
        result = check_table(
            table_name,
            definition['required'],
            definition['optional']
        )
        
        total_tables += 1
        
        if not result['exists']:
            print(f"\n❌ 表不存在: {table_name}")
            total_issues.append((table_name, "表不存在"))
            continue
        
        total_fields += result['total_fields']
        
        # 显示检查结果
        print(f"\n{'─' * 80}")
        print(f"表: {table_name}")
        print(f"字段数: {result['total_fields']}")
        
        if result['missing_required']:
            print(f"❌ 缺失必需字段 ({len(result['missing_required'])}个):")
            for field in result['missing_required']:
                print(f"    - {field}")
            total_issues.append((table_name, f"缺失: {', '.join(result['missing_required'][:3])}{'...' if len(result['missing_required']) > 3 else ''}"))
        else:
            print("✅ 所有必需字段齐全")
        
        if result['missing_optional']:
            print(f"⚠️  缺失可选字段 ({len(result['missing_optional'])}个): {', '.join(result['missing_optional'][:5])}{'...' if len(result['missing_optional']) > 5 else ''}")
    
    # 最终总结
    print(f"\n{'=' * 80}")
    print("检查总结")
    print('=' * 80)
    print(f"\n总表数: {total_tables}")
    print(f"总字段数: {total_fields}")
    
    if total_issues:
        print(f"\n❌ 发现问题: {len(total_issues)} 处")
        print("\n问题列表:")
        for table, issue in total_issues:
            print(f"  - {table}: {issue}")
        print("\n建议: 运行数据库重建或迁移脚本")
    else:
        print("\n✅ 所有表结构完整，无缺失字段")
    
    print('=' * 80)

if __name__ == '__main__':
    main()
