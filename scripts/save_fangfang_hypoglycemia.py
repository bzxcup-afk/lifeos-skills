import sys
import os
sys.path.insert(0, '.')
from db import insert, update

# 写入 medical_records
med_record = {
    'profile_id': '002',
    'record_date': '2026-04-01',
    'record_type': '症状描述',
    'complaint_or_reason': '偶发低血糖',
    'key_metrics_json': '{"症状": "低血糖", "频率": "偶发"}',
    'tags': '血糖,低血糖',
    'summary_for_system': '芳芳自述偶发低血糖，需关注血糖稳定'
}

result = insert('medical_records', med_record)
print('insert medical_records result:', result)

# 更新 profile 的健康关注
result2 = update('profiles', {
    'health_concerns': '低血糖'
}, 'profile_id = ?', ['002'])
print('update profiles result:', result2)
