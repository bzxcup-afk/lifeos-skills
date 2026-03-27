#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 更新 profiles 表结构

运行此脚本将现有的 profiles 表添加新的字段：
- blood_type: 血型
- resting_heart_rate: 静息心率
- waist_cm: 腰围
- hip_cm: 臀围
- body_goal: 身体目标
- current_stage: 当前阶段
- health_concerns: 健康关注
- family_history: 家族病史
- lifestyle_habits: 生活习惯
- diet_preferences: 饮食偏好

使用方法：
    cd scripts
    python migrate_add_profile_fields.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import execute, query_one, get_connection

def check_column_exists(table_name, column_name):
    """检查列是否已存在"""
    try:
        result = query_one(
            f"PRAGMA table_info({table_name})",
            ()
        )
        if result:
            columns = query_many(
                f"PRAGMA table_info({table_name})",
                ()
            )
            for col in columns:
                if col['name'] == column_name:
                    return True
        return False
    except:
        return False

def add_column(table_name, column_name, column_type):
    """添加列到表"""
    try:
        execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        return True
    except Exception as e:
        print(f"  添加列 {column_name} 失败: {e}")
        return False

def main():
    print("=" * 60)
    print("数据库迁移 - 更新 profiles 表结构")
    print("=" * 60)
    print()
    
    # 要添加的新字段
    new_fields = [
        ('blood_type', 'TEXT'),               # 血型
        ('resting_heart_rate', 'INTEGER'),      # 静息心率
        ('waist_cm', 'REAL'),                  # 腰围
        ('hip_cm', 'REAL'),                    # 臀围
        ('body_goal', 'TEXT'),                 # 身体目标
        ('current_stage', 'TEXT'),             # 当前阶段
        ('health_concerns', 'TEXT'),           # 健康关注
        ('family_history', 'TEXT'),            # 家族病史
        ('lifestyle_habits', 'TEXT'),          # 生活习惯
        ('diet_preferences', 'TEXT'),          # 饮食偏好
    ]
    
    added_count = 0
    skipped_count = 0
    
    print(f"将要添加 {len(new_fields)} 个新字段到 profiles 表:")
    print()
    
    for field_name, field_type in new_fields:
        print(f"  - {field_name} ({field_type})", end="")
        
        # 检查是否已存在
        try:
            existing = query_one(
                "SELECT 1 FROM pragma_table_info('profiles') WHERE name = ?",
                (field_name,)
            )
            
            if existing:
                print(" [已存在，跳过]")
                skipped_count += 1
                continue
        except:
            pass
        
        # 添加字段
        if add_column('profiles', field_name, field_type):
            print(" [添加成功]")
            added_count += 1
        else:
            print(" [添加失败]")
    
    print()
    print("=" * 60)
    print(f"迁移完成！")
    print(f"  - 新增字段: {added_count} 个")
    print(f"  - 已存在: {skipped_count} 个")
    print("=" * 60)
    print()
    
    # 显示当前表结构
    print("当前 profiles 表结构:")
    try:
        columns = query_many("PRAGMA table_info(profiles)", ())
        for col in columns:
            print(f"  - {col['name']:25s} {col['type']:10s}")
    except Exception as e:
        print(f"  获取表结构失败: {e}")

if __name__ == '__main__':
    # 导入 query_many
    from db import query_many
    main()
