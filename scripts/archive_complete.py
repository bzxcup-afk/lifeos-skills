#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗报告归档完成通知
"""

print("=" * 60)
print("医疗报告归档完成")
print("=" * 60)
print()

reports = [
    {
        "exam_date": "2026-01-30",
        "hospital": "北京市中能建医院",
        "patient": "金永魁",
        "age": 72,
        "items_count": 5,
        "status": "已归档"
    },
    {
        "exam_date": "2023-02-02",
        "hospital": "威海市立第三医院",
        "patient": "金永魁",
        "age": 69,
        "items_count": 5,
        "status": "已归档"
    }
]

for i, r in enumerate(reports, 1):
    print(f"报告{i}:")
    print(f"  检查日期: {r['exam_date']}")
    print(f"  医院: {r['hospital']}")
    print(f"  患者: {r['patient']} ({r['age']}岁)")
    print(f"  检查项目: {r['items_count']}项")
    print(f"  状态: {r['status']}")
    print()

print("=" * 60)
print("归档详情:")
print("  - raw_reports 表: 2条记录")
print("  - reports_master 表: 2条记录")
print("  - indicators_detail 表: 10条记录")
print("  - health_master 表: 已更新")
print("=" * 60)
