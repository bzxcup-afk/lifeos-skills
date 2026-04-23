# -*- coding: utf-8 -*-
"""
测试：两步对话模拟
Step 1: 用户说"我想改善失眠问题" → 只返回提问
Step 2: 用户回答 → 返回优先事项
"""
import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")
from intervention_data_collector import start_intervention_session, process_user_answer

output_path = r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\output\test_two_step.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("两步对话模拟\n")
    f.write("=" * 60 + "\n\n")

    # ===== Step 1: 用户第一句话 =====
    user_message = "我想改善失眠问题"

    session = start_intervention_session(
        user_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
        profile_id="001",
        user_message=user_message
    )

    # 内置问题（第一版）
    missing_questions = [
        "你大概几点睡觉、几点起床？",
        "每天晚上大概睡几个小时？",
        "主要是什么问题——入睡难、容易醒、还是早醒？",
        "白天有没有明显犯困或很累的感觉？"
    ]

    from intervention_data_collector import build_questions_reply
    reply_step1 = build_questions_reply(missing_questions)

    f.write("【Step 1 - 用户说】" + user_message + "\n\n")
    f.write("【系统回复】\n")
    f.write(reply_step1 + "\n")
    f.write("\n" + "=" * 60 + "\n\n")

    # ===== Step 2: 用户回答 =====
    user_answer = "我每天12点睡觉，7点起床，下午有点累"

    answer_result = process_user_answer(
        session_data=session["session_data"],
        user_answer=user_answer,
        llm_questions=missing_questions
    )

    f.write("【Step 2 - 用户说】" + user_answer + "\n\n")
    f.write("【系统回复】\n")
    f.write(answer_result.get("reply_message", "") + "\n")
    f.write("\n" + "=" * 60 + "\n\n")
    f.write("【Case文件】" + answer_result.get("case_file", "") + "\n")

print(f"Done. Output: {output_path}")
