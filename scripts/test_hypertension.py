# -*- coding: utf-8 -*-
"""
测试：高血压问题干预流程
"""
import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")

from intervention_intake import handle_intervention_intake

user_msg = "我想改善高血压问题"
result = handle_intervention_intake(user_msg)

output_path = r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\output\test_hypertension.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write(f"用户输入: {user_msg}\n")
    f.write("=" * 60 + "\n\n")

    f.write(f"[canonical_id] {result['structured_data']['canonical_id']}\n")
    f.write(f"[display_name] {result['structured_data']['display_name']}\n\n")

    f.write("【系统回复】\n")
    f.write(result['reply_message'] + "\n")

print(f"Output: {output_path}")
