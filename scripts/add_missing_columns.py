#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充所有表缺失的字段

检查所有现有表，补充缺失的字段以完善功能
"""

import sys
sys.path.insert(0, '.')
from db import execute, query_many

def table_exists(table_name):
    """检查表是否存在"""
    result = query_many(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return len(result) > 0

def column_exists(table_name, column_name):
    """检查列是否存在"""
    columns = query_many(f'PRAGMA table_info({table_name})', ())
    return any(col['name'] == column_name for col in columns)

def add_column(table_name, column_name, column_type, default=None):
    """添加列"""
    try:
        if default is not None:
            sql = f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default}'
        else:
            sql = f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'
        execute(sql)
        return True
    except Exception as e:
        print(f'    Error adding {column_name}: {e}')
        return False

def main():
    print('=' * 80)
    print('补充所有表缺失的字段')
    print('=' * 80)
    
    # 定义需要补充的字段
    alterations = {
        'profiles': [
            # 联系信息
            ('nickname', 'TEXT', None, '昵称'),
            ('phone', 'TEXT', None, '手机号'),
            ('email', 'TEXT', None, '邮箱'),
            ('emergency_contact', 'TEXT', None, '紧急联系人'),
            ('emergency_phone', 'TEXT', None, '紧急联系电话'),
            # 社保医保
            ('social_security', 'TEXT', None, '社保信息'),
            ('medical_insurance', 'TEXT', None, '医保信息'),
            ('id_card', 'TEXT', None, '身份证号'),
            # 头像
            ('avatar', 'TEXT', None, '头像路径'),
        ],
        
        'daily_logs': [
            ('mood_score', 'INTEGER', None, '心情评分'),
            ('stress_level', 'INTEGER', None, '压力水平'),
            ('steps', 'INTEGER', None, '步数'),
            ('active_minutes', 'INTEGER', None, '活跃分钟数'),
            ('blood_pressure_systolic', 'INTEGER', None, '收缩压'),
            ('blood_pressure_diastolic', 'INTEGER', None, '舒张压'),
            ('heart_rate', 'INTEGER', None, '心率'),
            ('blood_glucose', 'REAL', None, '血糖'),
            ('temperature', 'REAL', None, '体温'),
            ('oxygen_saturation', 'REAL', None, '血氧饱和度'),
        ],
        
        'medical_records': [
            ('hospital_name', 'TEXT', None, '医院名称'),
            ('department', 'TEXT', None, '科室'),
            ('doctor_name', 'TEXT', None, '主治医生'),
            ('symptoms', 'TEXT', None, '症状描述'),
            ('treatment', 'TEXT', None, '治疗方案'),
            ('prescription', 'TEXT', None, '处方药物'),
            ('test_results', 'TEXT', None, '检查结果'),
            ('images_attached', 'BOOLEAN', 0, '是否附图片'),
            ('image_urls', 'TEXT', None, '图片链接（JSON）'),
            ('notes', 'TEXT', None, '备注'),
            ('follow_up_date', 'TEXT', None, '复诊日期'),
            ('cost_total', 'REAL', None, '总费用'),
            ('cost_insurance', 'REAL', None, '医保报销'),
            ('cost_self', 'REAL', None, '自费金额'),
            ('updated_at', 'TEXT', None, '更新时间'),
        ],
        
        'medications': [
            ('drug_category', 'TEXT', None, '药物类别'),
            ('frequency', 'TEXT', None, '服用频率'),
            ('start_date', 'TEXT', None, '开始日期'),
            ('end_date', 'TEXT', None, '结束日期'),
            ('prescribed_by', 'TEXT', None, '开药医生'),
            ('purpose', 'TEXT', None, '用药目的'),
            ('side_effects', 'TEXT', None, '副作用'),
            ('notes', 'TEXT', None, '备注'),
            ('updated_at', 'TEXT', None, '更新时间'),
        ],
        
        'events': [
            ('event_location', 'TEXT', None, '事件地点'),
            ('participants', 'TEXT', None, '参与人员'),
            ('duration_hours', 'REAL', None, '持续时间'),
            ('impact_description', 'TEXT', None, '影响描述'),
            ('resolution', 'TEXT', None, '解决方式'),
            ('follow_up_required', 'BOOLEAN', 0, '是否需要跟进'),
            ('follow_up_date', 'TEXT', None, '跟进日期'),
            ('notes', 'TEXT', None, '备注'),
            ('updated_at', 'TEXT', None, '更新时间'),
        ],
    }
    
    total_added = 0
    total_errors = 0
    
    for table_name, columns in alterations.items():
        print(f'\n处理表: {table_name}')
        print('-' * 70)
        
        # 检查表是否存在
        exists = query_many(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not exists:
            print(f'  [跳过] 表不存在: {table_name}')
            continue
        
        added = 0
        errors = 0
        
        for col_name, col_type, default, description in columns:
            # 检查列是否已存在
            existing = query_many(
                f'PRAGMA table_info({table_name})',
                ()
            )
            if any(col['name'] == col_name for col in existing):
                print(f'  [已存在] {col_name}')
                continue
            
            # 添加列
            try:
                if default is not None:
                    sql = f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} DEFAULT {default}'
                else:
                    sql = f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}'
                execute(sql)
                print(f'  [已添加] {col_name} ({col_type}) - {description}')
                added += 1
            except Exception as e:
                print(f'  [错误] {col_name}: {e}')
                errors += 1
        
        print(f'\n  小结: 添加 {added} 个, 错误 {errors} 个')
        total_added += added
        total_errors += errors
    
    print('\n' + '=' * 70)
    print('总结果:')
    print(f'  成功添加: {total_added} 个字段')
    print(f'  错误: {total_errors} 个')
    print('=' * 70)

if __name__ == '__main__':
    main()
