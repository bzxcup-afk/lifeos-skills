#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import json

sys.path.insert(0, 'C:\\Users\\Jin\\.openclaw\\workspace-coding\\skills\\lifeos-main\\scripts')
os.environ['LIFEOS_DEFAULT_BITABLE'] = 'lifeos_laoma'

from bitable_ops import get_token, create_record, get_table_ids

def main():
    token = get_token()
    if not token:
        print("[ERROR] Failed to get token")
        return 1
    
    # 3份报告数据
    reports = [
        {
            "fields": {
                "report_type": "检验报告",
                "complaint_or_reason": "血脂四项、血糖检查",
                "hospital": "威海市立第三医院",
                "exam_date": 1675296000000,
                "key_metrics_json": '{"TG": 1.36, "CHOL": 5.78, "HDL-C": 2.09, "LDL-C": 3.01, "GLU": 6.17}',
                "summary_for_system": "总胆固醇偏高(5.78)，高密度脂蛋白偏高(2.09)，血糖接近上限(6.17)",
                "tags": "血脂异常,血糖偏高,心血管"
            }
        },
        {
            "fields": {
                "report_type": "检验报告",
                "complaint_or_reason": "血脂四项、血糖检查",
                "hospital": "威海市立第三医院",
                "exam_date": 1675296000000,
                "key_metrics_json": '{"TG": 1.36, "CHOL": 5.78, "HDL-C": 2.09, "LDL-C": 3.01, "GLU": 6.17}',
                "summary_for_system": "总胆固醇偏高(5.78)，高密度脂蛋白偏高(2.09)，血糖接近上限(6.17)",
                "tags": "血脂异常,血糖偏高,心血管"
            }
        },
        {
            "fields": {
                "report_type": "检验报告",
                "complaint_or_reason": "血脂四项、血糖检查",
                "hospital": "北京中能建医院",
                "exam_date": 1737696000000,
                "key_metrics_json": '{"TG": 1.70, "CHOL": 6.09, "HDL-C": 1.97, "LDL-C": 3.02, "GLU": 6.12}',
                "summary_for_system": "总胆固醇偏高(6.09)，甘油三酯偏高(1.70)，血糖偏高(6.12)，高密度脂蛋白偏高(1.97)",
                "tags": "血脂异常,血糖偏高,心血管"
            }
        }
    ]
    
    success_count = 0
    for i, report in enumerate(reports, 1):
        print(f"Archiving report {i}/3...")
        try:
            result = create_record(token, "medical_records", report["fields"])
            if result:
                print(f"  Success: {result.get('record_id', 'unknown')}")
                success_count += 1
            else:
                print(f"  Failed: create_record returned None")
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\nCompleted: {success_count}/{len(reports)} reports archived successfully")
    return 0 if success_count == len(reports) else 1

if __name__ == "__main__":
    sys.exit(main())
