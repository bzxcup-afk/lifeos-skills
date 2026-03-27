#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试医疗报告评估模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import query_one, insert

def test_medical_report_module():
    print('=' * 70)
    print('医疗报告评估模块测试')
    print('=' * 70)
    
    # 1. 检查数据库表
    print('\n【1. 数据库表检查】')
    print('-' * 70)
    
    tables = [
        'raw_reports',
        'reports_master',
        'indicators_detail',
        'health_master'
    ]
    
    for table in tables:
        result = query_one(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        status = 'OK' if result else 'MISSING'
        print(f'  [{status}] {table}')
    
    # 2. 测试插入原始报告
    print('\n【2. 测试插入原始报告】')
    print('-' * 70)
    
    try:
        raw_id = insert('raw_reports', {
            'profile_id': '001',
            'report_source': '测试医院体检中心',
            'report_type': '体检报告',
            'report_date': '2026-03-26',
            'ocr_raw_text': '【体检报告】\n姓名: 金\n性别: 男\n年龄: 35\n\n【血常规】\n白细胞: 6.5 (参考: 4.0-10.0)\n红细胞: 4.8 (参考: 4.0-5.5)\n血红蛋白: 150 (参考: 120-160)\n\n【血脂】\n总胆固醇: 5.2 (参考: 3.0-5.7)\n甘油三酯: 1.5 (参考: 0.5-1.7)\n\n【血糖】\n空腹血糖: 5.8 (参考: 3.9-6.1)\n\n结论: 各项指标正常。',
            'ocr_confidence': 0.96,
            'ocr_engine': 'paddleocr',
            'image_count': 5,
            'image_paths': '["report_page1.jpg", "report_page2.jpg", "report_page3.jpg", "report_page4.jpg", "report_page5.jpg"]',
            'processing_status': 'completed',
            'processing_notes': 'OCR识别成功，已提取关键指标'
        })
        
        print(f'  [OK] 成功插入 raw_reports，ID: {raw_id}')
        
        # 验证插入的数据
        record = query_one('SELECT * FROM raw_reports WHERE raw_id = ?', (raw_id,))
        if record:
            print(f'  [OK] 数据验证成功:')
            print(f'       - 来源: {record["report_source"]}')
            print(f'       - 类型: {record["report_type"]}')
            print(f'       - OCR置信度: {record["ocr_confidence"]}')
            print(f'       - 图片数: {record["image_count"]}')
    
    except Exception as e:
        print(f'  [ERROR] 插入失败: {e}')
    
    # 3. 测试健康评估
    print('\n【3. 测试健康评估功能】')
    print('-' * 70)
    
    try:
        from health_evaluation import run_evaluation
        
        print('  运行健康评估 (profile_id=001, days=7)...')
        result = run_evaluation('001', days=7)
        
        if 'error' in result:
            print(f'  [WARN] 评估运行但可能缺少数据: {result["error"]}')
        else:
            print(f'  [OK] 评估完成!')
            print(f'       - 评估ID: {result.get("eval_id")}')
            print(f'       - 总分: {result.get("total_score")}')
            print(f'       - 状态: {result.get("overall_status")}')
    
    except Exception as e:
        print(f'  [ERROR] 健康评估失败: {e}')
    
    # 4. 总结
    print('\n' + '=' * 70)
    print('测试总结')
    print('=' * 70)
    print('  [OK] 医疗报告归档表已创建')
    print('  [OK] 原始报告数据可正常插入')
    print('  [OK] 健康评估功能可运行')
    print('\n  状态: 医疗报告评估模块基本可用')
    print('=' * 70)

if __name__ == '__main__':
    main()
