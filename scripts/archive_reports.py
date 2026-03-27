#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
归档医疗报告到老妈的档案
"""

import sys
import json
sys.path.insert(0, 'C:\\Users\\Jin\\.openclaw\\workspace-coding\\skills\\lifeos-main\\scripts')

from bitable_ops import get_token, create_record

# 报告数据
reports = [
    {
        "table_key": "medical_records",
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
        "table_key": "medical_records", 
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
        "table_key": "medical_records",
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

def main():
    # 设置环境变量指定使用老妈的档案
    import os
    os.environ['LIFEOS_DEFAULT_BITABLE'] = 'lifeos_laoma'
    
    token = get_token()
    if not token:
        print("[ERROR] 无法获取token")
        sys.exit(1)
    
    success_count = 0
    for i, report in enumerate(reports, 1):
        print(f"\n正在归档第{i}份报告...")
        result = create_record(token, report["table_key"], report["fields"])
        if result:
            print(f"✓ 第{i}份报告归档成功")
            success_count += 1
        else:
            print(f"✗ 第{i}份报告归档失败")
    
    print(f"\n归档完成: {success_count}/{len(reports)} 份报告成功归档")

if __name__ == "__main__":
    main()
