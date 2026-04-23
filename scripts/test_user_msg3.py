# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")
from intervention_data_collector import run_full_intake_flow

# 模拟完整对话流程
# 第一句：用户说想改善失眠
msg1 = "我想改善失眠问题"

# 第二句：用户回答问题
msg2 = "我每天12点睡觉，7点起床，下午有点累"

result = run_full_intake_flow(
    user_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
    profile_id="001",
    user_message=msg1,
    user_answer=msg2
)

output_path = r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\output\test_user_msg3.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write(f"【第一句】用户: {msg1}\n")
    f.write("=" * 60 + "\n\n")

    if result.get("missing_questions"):
        f.write("【系统提问】\n")
        for i, q in enumerate(result["missing_questions"], 1):
            f.write(f"  {i}. {q}\n")
        f.write("\n")

    f.write("=" * 60 + "\n")
    f.write(f"【第二句】用户: {msg2}\n")
    f.write("=" * 60 + "\n\n")

    f.write("【系统回复】\n")
    f.write(result.get("reply_message", "") + "\n\n")

    if result.get("case_file"):
        f.write(f"【Case文件】{result['case_file']}\n")

print(f"Done. Output: {output_path}")
