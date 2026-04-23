# -*- coding: utf-8 -*-
"""
问题导向干预入口 - 集成测试脚本
"""

import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")

from intervention_intake import handle_intervention_intake, detect_intervention_intent

print("=" * 70)
print("问题导向干预入口 - 集成测试")
print("=" * 70)

# 测试用例
test_cases = [
    # 正例
    ("改善睡眠问题", "sleep-insomnia"),
    ("帮我制定一个改善失眠的计划", "sleep-insomnia"),
    ("最近总是睡不好，想调理一下", "sleep-insomnia"),
    ("最近总是睡不好，困扰我，帮我安排", "sleep-insomnia"),
    ("我想改善高血压", "hypertension"),
    ("帮我做一个减肥的计划", "weight-loss"),
    # 负例
    ("什么是失眠？", None),
    ("请问高血压怎么治疗？", None),
    ("帮我记录昨晚睡了7小时", None),
]

passed = 0
failed = 0

print("\n测试用例：")
print("-" * 70)

for msg, expected_id in test_cases:
    intent = detect_intervention_intent(msg)
    if expected_id is None:
        # 负例：应该不匹配
        if intent is None:
            print(f"[PASS] \"{msg}\" -> 未匹配（预期）")
            passed += 1
        else:
            print(f"[FAIL] \"{msg}\" -> 误匹配为 {intent.get('canonical_id')}（预期：不匹配）")
            failed += 1
    else:
        # 正例：应该匹配到对应 ID
        if intent and intent.get("canonical_id") == expected_id:
            print(f"[PASS] \"{msg}\" -> {expected_id}")
            passed += 1
        else:
            actual = intent.get("canonical_id") if intent else "None"
            print(f"[FAIL] \"{msg}\" -> {actual}（预期：{expected_id}）")
            failed += 1

print("-" * 70)
print(f"\n结果：{passed} 通过，{failed} 失败")

# 测试完整流程
print("\n" + "=" * 70)
print("完整流程测试（sleep-insomnia）：")
print("=" * 70)

result = handle_intervention_intake("改善睡眠问题")
if result["success"]:
    sd = result["structured_data"]
    print(f"\ncanonical_id: {sd['canonical_id']}")
    print(f"display_name: {sd['display_name']}")
    print(f"knowledge_file: {sd['knowledge_file']}")
    print(f"file_was_newly_created: {sd['file_was_newly_created']}")
    print(f"\nintervention_principles ({len(sd['intervention_principles'])}):")
    for p in sd['intervention_principles']:
        print(f"  - {p}")
    print(f"\nintervention_dimensions ({len(sd['intervention_dimensions'])}):")
    for d in sd['intervention_dimensions']:
        print(f"  - {d}")
    print(f"\nrequired_info_to_ask ({len(sd['required_info_to_ask'])}):")
    for q in sd['required_info_to_ask']:
        print(f"  - {q}")
    print(f"\nrisk_boundaries ({len(sd['risk_boundaries'])}):")
    for r in sd['risk_boundaries']:
        print(f"  - {r}")
    print(f"\n回复消息预览：\n{result['reply_message'][:200]}...")
else:
    print("[FAIL] 处理失败")

print("\n" + "=" * 70)
