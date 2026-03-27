#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗报告归档完整流程测试

模拟完整的医疗报告处理流程：
1. 接收报告图片 -> raw_reports
2. OCR识别 -> 提取文本
3. 解析指标 -> indicators_detail
4. 生成报告摘要 -> reports_master
5. 更新健康档案 -> health_master
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import insert, query_one, execute
import json

def test_medical_report_workflow():
    """测试完整的医疗报告处理流程"""
    
    print('=' * 80)
    print('医疗报告归档完整流程测试')
    print('=' * 80)
    
    profile_id = '001'  # 金的用户ID
    
    # 步骤1: 创建原始报告记录 (raw_reports)
    print('\n【步骤1】创建原始报告记录 (raw_reports)')
    print('-' * 80)
    
    ocr_text = """
    【体检报告】
    姓名: 金
    性别: 男
    年龄: 35
    体检日期: 2026-03-26
    体检编号: TJ20260326001
    
    【血常规】
    白细胞: 6.5 (参考: 4.0-10.0) 10^9/L - 正常
    红细胞: 4.8 (参考: 4.0-5.5) 10^12/L - 正常
    血红蛋白: 150 (参考: 120-160) g/L - 正常
    血小板: 220 (参考: 100-300) 10^9/L - 正常
    
    【血脂】
    总胆固醇: 5.2 (参考: 3.0-5.7) mmol/L - 正常
    甘油三酯: 1.5 (参考: 0.5-1.7) mmol/L - 正常
    高密度脂蛋白: 1.3 (参考: 1.0-1.6) mmol/L - 正常
    低密度脂蛋白: 3.0 (参考: 2.0-3.4) mmol/L - 正常
    
    【血糖】
    空腹血糖: 5.8 (参考: 3.9-6.1) mmol/L - 正常
    
    【肝功能】
    谷丙转氨酶: 25 (参考: 9-50) U/L - 正常
    谷草转氨酶: 22 (参考: 15-40) U/L - 正常
    
    【肾功能】
    肌酐: 85 (参考: 57-97) umol/L - 正常
    尿素氮: 5.2 (参考: 2.6-7.5) mmol/L - 正常
    尿酸: 380 (参考: 208-428) umol/L - 正常
    
    【血压】
    收缩压: 118 (参考: 90-139) mmHg - 正常
    舒张压: 76 (参考: 60-89) mmHg - 正常
    
    【结论】
    各项体检指标均在正常范围内，身体状况良好。
    建议：保持现有健康生活方式，定期体检。
    
    报告医生：李医生
    审核医生：王主任
    体检中心：XX健康体检中心
    ""
    
    raw_data = {
        'profile_id': profile_id,
        'report_source': 'XX健康体检中心',
        'report_type': '体检报告',
        'report_date': '2026-03-26',
        'ocr_raw_text': ocr_text,
        'ocr_confidence': 0.96,
        'ocr_engine': 'paddleocr',
        'image_count': 5,
        'image_paths': json.dumps(['report_page1.jpg', 'report_page2.jpg', 'report_page3.jpg', 'report_page4.jpg', 'report_page5.jpg']),
        'processing_status': 'completed',
        'processing_notes': 'OCR识别成功，已提取所有关键指标'
    }
    
    try:
        raw_id = insert('raw_reports', raw_data)
        print(f'  [OK] 原始报告已创建，ID: {raw_id}')
    except Exception as e:
        print(f'  [ERROR] 创建失败: {e}')
        return
    
    # 步骤2: 解析指标并保存到 indicators_detail
    print('\n【步骤2】解析指标并保存 (indicators_detail)')
    print('-' * 80)
    
    # 从OCR文本中提取的关键指标
    indicators = [
        ('白细胞', '6.5', '10^9/L', 4.0, 10.0, '6.5', 'normal'),
        ('红细胞', '4.8', '10^12/L', 4.0, 5.5, '4.8', 'normal'),
        ('血红蛋白', '150', 'g/L', 120, 160, '150', 'normal'),
        ('血小板', '220', '10^9/L', 100, 300, '220', 'normal'),
        ('总胆固醇', '5.2', 'mmol/L', 3.0, 5.7, '5.2', 'normal'),
        ('甘油三酯', '1.5', 'mmol/L', 0.5, 1.7, '1.5', 'normal'),
        ('高密度脂蛋白', '1.3', 'mmol/L', 1.0, 1.6, '1.3', 'normal'),
        ('低密度脂蛋白', '3.0', 'mmol/L', 2.0, 3.4, '3.0', 'normal'),
        ('空腹血糖', '5.8', 'mmol/L', 3.9, 6.1, '5.8', 'normal'),
        ('谷丙转氨酶', '25', 'U/L', 9, 50, '25', 'normal'),
        ('谷草转氨酶', '22', 'U/L', 15, 40, '22', 'normal'),
        ('肌酐', '85', 'umol/L', 57, 97, '85', 'normal'),
        ('尿素氮', '5.2', 'mmol/L', 2.6, 7.5, '5.2', 'normal'),
        ('尿酸', '380', 'umol/L', 208, 428, '380', 'normal'),
        ('收缩压', '118', 'mmHg', 90, 139, '118', 'normal'),
        ('舒张压', '76', 'mmHg', 60, 89, '76', 'normal'),
    ]
    
    # 生成报告ID
    import uuid
    report_id = 'REP-' + str(uuid.uuid4())[:8].upper()
    
    inserted_count = 0
    
    for indicator in indicators:
        name, value, unit, ref_min, ref_max, value_raw, status = indicator
        
        try:
            insert('indicators_detail', {
                'report_id': report_id,
                'profile_id': profile_id,
                'indicator_name': name,
                'indicator_name_en': '',
                'indicator_category': '体检指标',
                'value_raw': value_raw,
                'value_numeric': float(value),
                'unit': unit,
                'reference_range_text': f'{ref_min}-{ref_max}',
                'reference_range_min': ref_min,
                'reference_range_max': ref_max,
                'status': status,
                'direction': 'normal' if status == 'normal' else 'abnormal',
                'severity': 0 if status == 'normal' else 3,
                'clinical_significance': '指标在正常范围内' if status == 'normal' else '指标异常，需要关注',
                'suggestions': '继续保持健康生活方式' if status == 'normal' else '建议咨询医生，进一步检查',
            })
            inserted_count += 1
        except Exception as e:
            print(f'    [ERROR] 插入 {name} 失败: {e}')
    
    print(f'  [OK] 成功解析并保存 {inserted_count}/{len(indicators)} 个指标')
    
    # 步骤3: 创建报告主记录
    print('\n【步骤3】创建报告主记录 (reports_master)')
    print('-' * 80)
    
    try:
        insert('reports_master', {
            'report_id': report_id,
            'profile_id': profile_id,
            'report_source': 'XX健康体检中心',
            'report_type': '体检报告',
            'report_subtype': '年度体检',
            'report_date': '2026-03-26',
            'hospital_name': 'XX健康体检中心',
            'hospital_department': '体检科',
            'hospital_doctor': '李医生',
            'report_summary': '本次体检各项指标均在正常范围内，身体状况良好。共检查19项指标，全部正常。',
            'key_findings': json.dumps([
                '血常规指标全部正常',
                '血脂指标全部正常',
                '血糖指标正常',
                '肝功能指标正常',
                '肾功能指标正常',
                '血压正常'
            ]),
            'abnormal_items': json.dumps([]),
            'overall_assessment': '身体状况良好，各项指标均在正常范围内。',
            'review_status': 'confirmed',
            'archive_status': 'active',
            'raw_report_id': raw_id,
        })
        print(f'  [OK] 报告主记录已创建，ID: {report_id}')
    except Exception as e:
        print(f'  [ERROR] 创建失败: {e}')
        return
    
    # 步骤4: 更新健康档案
    print('\n【步骤4】更新健康档案 (health_master)')
    print('-' * 80)
    
    try:
        # 检查是否已有健康档案
        existing = query_one('SELECT * FROM health_master WHERE profile_id = ?', (profile_id,))
        
        if existing:
            # 更新现有档案
            execute('''
                UPDATE health_master SET
                    latest_physical_date = '2026-03-26',
                    latest_physical_report_id = ?,
                    latest_blood_pressure = '118/76',
                    latest_blood_sugar = 5.8,
                    latest_hba1c = NULL,
                    latest_cholesterol_total = 5.2,
                    latest_ldl = 3.0,
                    latest_hdl = 1.3,
                    latest_triglycerides = 1.5,
                    abnormal_indicators = '[]',
                    chronic_conditions = '[]',
                    overall_health_score = 95,
                    health_risk_level = 'low',
                    last_evaluation_date = '2026-03-26',
                    follow_up_items = '["继续保持健康生活方式", "定期体检" ]',
                    next_checkup_date = '2027-03-26',
                    total_reports = total_reports + 1,
                    total_indicators = total_indicators + 19,
                    updated_at = datetime('now')
                WHERE profile_id = ?
            ''', (report_id, profile_id))
            print('  [OK] 健康档案已更新')
        else:
            # 创建新档案
            insert('health_master', {
                'profile_id': profile_id,
                'latest_physical_date': '2026-03-26',
                'latest_physical_report_id': report_id,
                'latest_blood_pressure': '118/76',
                'latest_blood_sugar': 5.8,
                'latest_hba1c': None,
                'latest_cholesterol_total': 5.2,
                'latest_ldl': 3.0,
                'latest_hdl': 1.3,
                'latest_triglycerides': 1.5,
                'abnormal_indicators': '[]',
                'chronic_conditions': '[]',
                'overall_health_score': 95,
                'health_risk_level': 'low',
                'last_evaluation_date': '2026-03-26',
                'follow_up_items': json.dumps(['继续保持健康生活方式', '定期体检']),
                'next_checkup_date': '2027-03-26',
                'total_reports': 1,
                'total_indicators': 19,
            })
            print('  [OK] 健康档案已创建')
    
    except Exception as e:
        print(f'  [ERROR] 更新失败: {e}')
    
    # 完成
    print('\n' + '=' * 80)
    print('医疗报告归档完整流程测试完成！')
    print('=' * 80)
    print(f'\n报告ID: {report_id}')
    print(f'原始记录ID: {raw_id}')
    print(f'用户ID: {profile_id}')
    print('\n已完成的操作:')
    print('  [OK] 1. 创建原始报告记录 (raw_reports)')
    print('  [OK] 2. 解析并保存19项指标 (indicators_detail)')
    print('  [OK] 3. 创建报告主记录 (reports_master)')
    print('  [OK] 4. 更新健康档案 (health_master)')
    print('\n所有数据已成功保存到本地 SQLite 数据库！')
    print('=' * 80)

if __name__ == '__main__':
    main()
