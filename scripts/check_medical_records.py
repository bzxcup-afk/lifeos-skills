#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 medical_records 表结构并对比飞书原表
"""

import sys
sys.path.insert(0, '.')
from db import query_many

def main():
    print('=' * 70)
    print('检查 medical_records 表结构')
    print('=' * 70)
    
    # 获取表结构
    columns = query_many('PRAGMA table_info(medical_records)')
    
    print('\n现有字段（共 {} 个）:'.format(len(columns)))
    print('-' * 70)
    for col in columns:
        name = col['name']
        type_ = col['type']
        pk = 'PK' if col.get('pk') else ''
        notnull = 'NOT NULL' if col.get('notnull') else ''
        print('  {:25s} {:12s} {:10s} {:8s}'.format(name, type_, notnull, pk))
    
    # 与飞书原表对比（根据常见的医疗记录表结构）
    print('\n' + '=' * 70)
    print('与飞书 Bitable 原表对比')
    print('=' * 70)
    
    # 飞书原表常见的字段
    feishu_fields = [
        ('record_id', '记录ID（飞书独有）'),
        ('profile_id', '用户ID'),
        ('record_date', '记录日期'),
        ('record_type', '记录类型（门诊/住院/体检）'),
        ('hospital_name', '医院名称'),
        ('department', '科室'),
        ('doctor_name', '主治医生'),
        ('diagnosis', '诊断结果'),
        ('symptoms', '症状描述'),
        ('treatment', '治疗方案'),
        ('prescription', '处方药物'),
        ('test_results', '检查结果'),
        ('images_attached', '是否附图片'),
        ('image_urls', '图片链接（JSON）'),
        ('notes', '备注'),
        ('follow_up_date', '复诊日期'),
        ('cost_total', '总费用'),
        ('cost_insurance', '医保报销'),
        ('cost_self', '自费金额'),
        ('created_by', '创建人（飞书）'),
        ('created_at', '创建时间'),
        ('updated_by', '更新人（飞书）'),
        ('updated_at', '更新时间'),
    ]
    
    existing = [c['name'] for c in columns]
    
    print('\n飞书有但本地缺失的字段:')
    missing = []
    for field, desc in feishu_fields:
        if field not in existing:
            print('  [缺失] {:20s} - {}'.format(field, desc))
            missing.append(field)
    
    if not missing:
        print('  无缺失（或已使用不同名称）')
    
    print('\n已存在的对应字段:')
    for field, desc in feishu_fields:
        if field in existing:
            print('  [OK]   {:20s} - {}'.format(field, desc))
    
    print('\n' + '=' * 70)
    print('总结:')
    print('  - 现有字段数: {}'.format(len(existing)))
    print('  - 缺失字段数: {}'.format(len(missing)))
    if missing:
        print('\n  建议: 添加缺失的字段以完善功能')
    print('=' * 70)

if __name__ == '__main__':
    main()
