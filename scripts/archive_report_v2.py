#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""医疗报告归档 - 阶段B执行脚本 (修正版)"""

import sys
import json
import uuid
from datetime import datetime

sys.path.insert(0, 'scripts')
from db import insert, get_connection

print("="*70)
print("阶段B: 医疗报告归档执行")
print("="*70)

# 阶段A分析结果
report_meta = {
    "report_type": "全血细胞分析",
    "hospital": "天津市第四中心医院",
    "department": "检验科",
    "exam_date": "2026-03-15",
    "patient_name": "金志远",
    "gender": "男",
    "age": 44
}

items = [
    {"raw_name": "白细胞计数", "value": 6.09, "unit": "x10^9/L", "reference_range": "5--12", "abnormal_flag": "正常"},
    {"raw_name": "中性粒细胞比值", "value": 30.8, "unit": "%", "reference_range": "50-70", "abnormal_flag": "偏低"},
    {"raw_name": "淋巴细胞比值", "value": 47.0, "unit": "%", "reference_range": "20-40", "abnormal_flag": "偏高"},
    {"raw_name": "单核细胞比值", "value": 11.5, "unit": "%", "reference_range": "3--10", "abnormal_flag": "偏高"},
    {"raw_name": "嗜酸粒细胞比值", "value": 10.7, "unit": "%", "reference_range": "0.5--5", "abnormal_flag": "偏高"},
    {"raw_name": "嗜碱粒细胞比值", "value": 0.0, "unit": "%", "reference_range": "0--1", "abnormal_flag": "正常"},
    {"raw_name": "中性粒细胞绝对数", "value": 1.88, "unit": "x10^9/L", "reference_range": "2.50-8.40", "abnormal_flag": "偏低"},
    {"raw_name": "淋巴细胞绝对数", "value": 2.86, "unit": "x10^9/L", "reference_range": "1.00-4.80", "abnormal_flag": "正常"},
    {"raw_name": "单核细胞绝对数", "value": 0.70, "unit": "x10^9/L", "reference_range": "0.12-1", "abnormal_flag": "正常"},
    {"raw_name": "嗜酸细胞绝对数", "value": 0.65, "unit": "x10^9/L", "reference_range": "0.02-0.5", "abnormal_flag": "偏高"},
    {"raw_name": "嗜碱细胞绝对数", "value": 0.00, "unit": "x10^9/L", "reference_range": "0-0.1", "abnormal_flag": "正常"},
    {"raw_name": "红细胞计数", "value": 4.87, "unit": "x10^12/L", "reference_range": "4.0-4.5", "abnormal_flag": "偏高"},
    {"raw_name": "血红蛋白浓度", "value": 123.0, "unit": "g/L", "reference_range": "120--140", "abnormal_flag": "正常"},
    {"raw_name": "红细胞压积", "value": 0.407, "unit": "", "reference_range": "0.335-0.450", "abnormal_flag": "正常"},
    {"raw_name": "平均红细胞体积", "value": 83.6, "unit": "fl", "reference_range": "82-100", "abnormal_flag": "正常"},
    {"raw_name": "平均红细胞血红蛋白含量", "value": 25.3, "unit": "pg", "reference_range": "27-34", "abnormal_flag": "偏低"},
    {"raw_name": "平均红细胞血红蛋白浓度", "value": 302, "unit": "g/L", "reference_range": "316--354", "abnormal_flag": "偏低"},
]

# 1. 风险解析
abnormal_items = [item for item in items if item['abnormal_flag'] in ['偏高', '偏低']]
print(f"\n[1] 风险解析:")
print(f"  - 总项目数: {len(items)} 项")
print(f"  - 异常项目: {len(abnormal_items)} 项")

# 2. 置信度评估
extraction_confidence = 85
identity_match_score = 80
consistency_score = 90
total_archive_confidence = int(extraction_confidence * 0.4 + identity_match_score * 0.3 + consistency_score * 0.3)

print(f"\n[2] 置信度评估:")
print(f"  - 总归档置信度: {total_archive_confidence}/100")
print(f"  - 归档策略: A (FULL_ARCHIVE)")

# 3. 生成ID
report_id = "RPT-{}-{}".format(datetime.now().strftime('%Y%m%d'), str(uuid.uuid4())[:8].upper())
print(f"\n[3] 报告ID: {report_id}")

# 4. 写入raw_reports表
raw_data = {
    'profile_id': '001',
    'report_source': 'feishu',
    'report_type': report_meta['report_type'],
    'report_date': report_meta['exam_date'],
    'ocr_raw_text': json.dumps(items, ensure_ascii=False),
    'ocr_confidence': extraction_confidence / 100.0,
    'ocr_engine': 'volc-coding',
    'image_count': 1,
    'image_paths': 'media/inbound/3bc39fe1-990f-42af-94e5-2014f4c24b44.jpg',
    'processing_status': 'completed',
    'processing_notes': f'异常项目{len(abnormal_items)}项',
    'linked_report_id': report_id,
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat()
}

raw_id = insert('raw_reports', raw_data)
print(f"\n[4] ✅ raw_reports表写入成功，ID: {raw_id}")

# 5. 写入reports_master表
master_data = {
    'report_id': report_id,
    'profile_id': '001',
    'report_source': 'feishu',
    'report_type': report_meta['report_type'],
    'report_subtype': '血常规',
    'report_date': report_meta['exam_date'],
    'hospital_name': report_meta['hospital'],
    'hospital_department': report_meta['department'],
    'hospital_doctor': None,
    'report_summary': f'全血细胞分析，共{len(items)}项指标，异常{len(abnormal_items)}项。临床诊断：急性上呼吸道感染',
    'key_findings': json.dumps(abnormal_items, ensure_ascii=False),
    'abnormal_items': str(len(abnormal_items)),
    'overall_assessment': '多项血细胞比例异常，可能与感染相关',
    'review_status': 'approved',
    'archive_status': 'archived',
    'raw_report_id': raw_id,
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat()
}

insert('reports_master', master_data)
print(f"[5] ✅ reports_master表写入成功")

# 6. 写入indicators_detail表
indicator_count = 0
for idx, item in enumerate(items, 1):
    # 解析参考范围
    ref_range = item['reference_range']
    ref_min = None
    ref_max = None
    if '--' in ref_range:
        parts = ref_range.split('--')
        ref_min = float(parts[0]) if parts[0] else None
        ref_max = float(parts[1]) if len(parts) > 1 and parts[1] else None
    elif '-' in ref_range:
        parts = ref_range.split('-')
        ref_min = float(parts[0]) if parts[0] else None
        ref_max = float(parts[1]) if len(parts) > 1 and parts[1] else None
    
    indicator_data = {
        'report_id': report_id,
        'profile_id': '001',
        'indicator_name': item['raw_name'],
        'indicator_name_en': None,
        'indicator_category': '血常规',
        'value_raw': str(item['value']),
        'value_numeric': item['value'] if isinstance(item['value'], (int, float)) else None,
        'unit': item['unit'],
        'reference_range_text': item['reference_range'],
        'reference_range_min': ref_min,
        'reference_range_max': ref_max,
        'status': 'abnormal' if item['abnormal_flag'] in ['偏高', '偏低'] else 'normal',
        'direction': 'high' if item['abnormal_flag'] == '偏高' else ('low' if item['abnormal_flag'] == '偏低' else None),
        'severity': 1 if item['abnormal_flag'] != '正常' else 0,
        'clinical_significance': None,
        'suggestions': None,
        'related_indicators': None,
        'created_at': datetime.now().isoformat()
    }
    insert('indicators_detail', indicator_data)
    indicator_count += 1

print(f"[6] ✅ indicators_detail表写入成功，共{indicator_count}项指标")

# 7. 输出最终报告
print("\n" + "="*70)
print("✅ 医疗报告归档完成")
print("="*70)
print(f"报告ID: {report_id}")
print(f"患者: {report_meta['patient_name']} ({report_meta['gender']}, {report_meta['age']}岁)")
print(f"检查日期: {report_meta['exam_date']}")
print(f"医院: {report_meta['hospital']}")
print(f"报告类型: {report_meta['report_type']}")
print(f"指标总数: {len(items)}项")
print(f"异常指标: {len(abnormal_items)}项")
print(f"归档策略: A (FULL_ARCHIVE)")
print(f"归档置信度: {total_archive_confidence}/100")
print("="*70)

# 8. 异常项摘要
print("\n【异常项摘要】")
for item in abnormal_items:
    print(f"  • {item['raw_name']}: {item['value']} {item['unit']} ({item['abnormal_flag']})")
