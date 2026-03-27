# -*- coding: utf-8 -*-
"""
验证策略C的触发条件
规则：关键项目有识别风险（非指标异常）时触发策略C
"""

import sys
sys.path.insert(0, '../medical_report_archive')

from stage_b_logic import parse_risks, determine_strategy, ArchiveStrategy

# 测试用例1: 指标异常但无识别风险 -> 应该走策略A（完全归档）
test_case_1 = {
    "report_meta": {"patient_name": "测试", "gender": "男"},
    "table_structure_check": {
        "table_confidence": 0.95,
        "has_possible_shift": False,
        "overall_risk_level": "low"
    },
    "items": [
        {
            "raw_name": "LDL-C",
            "standard_name": "LDL-C",
            "value": 4.2,
            "reference_range": "<3.4",
            "abnormal_flag": "high",
            "confidence": 0.95,
            "risk_flags": [],
            "review_priority": "low"
        }
    ],
    "confidence_check": {
        "hard_conflict": False,
        "identity_match_score": 95,
        "extraction_confidence": 95
    }
}

# 测试用例2: 有识别风险 -> 应该触发策略C
test_case_2 = {
    "report_meta": {"patient_name": "测试", "gender": "男"},
    "table_structure_check": {
        "table_confidence": 0.95,
        "has_possible_shift": False,
        "overall_risk_level": "low"
    },
    "items": [
        {
            "raw_name": "LDL-C",
            "standard_name": "LDL-C",
            "value": 4.2,
            "reference_range": "<3.4",
            "abnormal_flag": "high",
            "confidence": 0.70,
            "risk_flags": ["range_mismatch"],
            "review_priority": "high"
        }
    ],
    "confidence_check": {
        "hard_conflict": False,
        "identity_match_score": 95,
        "extraction_confidence": 75
    }
}

print("=" * 60)
print("策略C触发条件验证")
print("=" * 60)

# 测试用例1
print("\n【测试用例1】指标异常但无识别风险")
print("-" * 60)
risk1 = parse_risks(test_case_1)
print(f"全局风险等级: {risk1['global_risk_level']}")
print(f"硬冲突: {risk1['has_hard_conflict']}")
print(f"关键项目风险: {risk1['critical_items_with_risk']}")
print(f"高风险项目数: {risk1['high_risk_count']}")
print(f"中风险项目数: {risk1['medium_risk_count']}")

strategy1 = determine_strategy(risk1)
print(f"\n策略结果: {strategy1.value}")
print(f"预期: {ArchiveStrategy.FULL_ARCHIVE.value} (策略A - 完全归档)")
if strategy1 == ArchiveStrategy.FULL_ARCHIVE:
    print("[PASS] 测试通过：指标异常未触发策略C")
else:
    print("[FAIL] 测试失败：指标异常错误地触发了高级别策略")

# 测试用例2
print("\n【测试用例2】关键项目有识别风险")
print("-" * 60)
risk2 = parse_risks(test_case_2)
print(f"全局风险等级: {risk2['global_risk_level']}")
print(f"硬冲突: {risk2['has_hard_conflict']}")
print(f"关键项目风险: {risk2['critical_items_with_risk']}")
print(f"高风险项目数: {risk2['high_risk_count']}")
print(f"中风险项目数: {risk2['medium_risk_count']}")

strategy2 = determine_strategy(risk2)
print(f"\n策略结果: {strategy2.value}")
print(f"预期: {ArchiveStrategy.SAVE_NOT_UPDATE_PROFILE.value} (策略C - 保存但不更新主档案)")
if strategy2 == ArchiveStrategy.SAVE_NOT_UPDATE_PROFILE:
    print("[PASS] 测试通过：识别风险正确触发策略C")
else:
    print("[FAIL] 测试失败：识别风险未正确触发策略C")

print("\n" + "=" * 60)
print("验证完成")
print("=" * 60)