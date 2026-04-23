# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")
from intervention_intake import handle_intervention_intake

msg = "我想改善睡眠问题"
result = handle_intervention_intake(msg)

# Write to file to avoid GBK encoding issues
output_path = r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\output\test_reply.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(result["reply_message"])
    f.write("\n\n--- Structured Data ---\n")
    f.write(f"canonical_id: {result['structured_data']['canonical_id']}\n")
    f.write(f"display_name: {result['structured_data']['display_name']}\n")
    f.write(f"file_was_newly_created: {result['structured_data']['file_was_newly_created']}\n")
    f.write(f"dimensions: {len(result['structured_data']['intervention_dimensions'])}\n")
    f.write(f"candidate_actions: {len(result['structured_data']['candidate_actions'])}\n")
    f.write(f"required_info: {len(result['structured_data']['required_info_to_ask'])}\n")
    f.write(f"risk_boundaries: {len(result['structured_data']['risk_boundaries'])}\n")

print(f"Output written to: {output_path}")
