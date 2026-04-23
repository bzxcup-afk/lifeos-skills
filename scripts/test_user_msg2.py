# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")
from intervention_data_collector import run_full_intake_flow

msg = "我想改善失眠问题"
result = run_full_intake_flow(
    user_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
    profile_id="001",
    user_message=msg,
    user_answer="大概11点半睡，7点左右起，睡6个小时左右，主要是半夜容易醒，早上起来感觉还行不太累"
)

output_path = r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\output\test_user_msg2.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write(f"用户输入: {msg}\n")
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

print(f"Done. Output: {output_path}")
