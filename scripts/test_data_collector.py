# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")
from intervention_data_collector import run_full_intake_flow

# 测试完整流程
result = run_full_intake_flow(
    user_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
    profile_id="001",
    user_message="改善睡眠问题",
    user_answer="我大概11点多睡，7点多起，睡6个多小时吧，主要是容易醒，白天还好不太困"
)

output_path = r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\output\test_collector_output.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("干预资料补全模块 - 测试输出\n")
    f.write("=" * 60 + "\n\n")

    f.write(f"[canonical_id] {result.get('canonical_id')}\n")
    f.write(f"[display_name] {result.get('display_name')}\n\n")

    if result.get("missing_questions"):
        f.write("【提问的问题】\n")
        for i, q in enumerate(result["missing_questions"], 1):
            f.write(f"  {i}. {q}\n")
        f.write("\n")

    f.write("【用户回答后的回复】\n")
    f.write(result.get("reply_message", "") + "\n\n")

    if result.get("case_file"):
        f.write(f"[Case文件] {result['case_file']}\n")

print(f"Output written to: {output_path}")
