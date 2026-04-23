import sys
import os
sys.path.insert(0, '.')
from db import insert

med_record = {
    'profile_id': '002',
    'record_date': '2025-01-01',
    'record_type': '检查结果',
    'complaint_or_reason': '年度体检血糖检测',
    'key_metrics_json': '{"血糖": 5.0, "单位": "mmol/L", "检测时间": "2025年", "类型": "空腹血糖"}',
    'tags': '血糖,体检',
    'summary_for_system': '2025年体检空腹血糖5.0 mmol/L，正常范围'
}

result = insert('medical_records', med_record)
print('result:', result)
