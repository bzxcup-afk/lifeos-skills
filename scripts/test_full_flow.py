# -*- coding: utf-8 -*-
"""
完整流程测试：从干预入口 -> 资料补全 -> 调度
"""
import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")

from intervention_intake import handle_intervention_intake
from intervention_data_collector import run_full_intake_flow, build_questions_reply
from intervention_scheduler import run_intervention_scheduler

output_path = r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\output\test_full_flow.txt"

user_id = "ou_fde56bd8d48eca22b3d57ab990ee4f02"
user_name = "金"
channel_id = user_id
channel_type = "direct"
mention_target = "@金"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("完整流程测试：从干预入口 -> 资料补全 -> 调度\n")
    f.write("=" * 60 + "\n\n")

    # ===== Phase 1: 干预入口 =====
    user_msg = "我想改善一下失眠问题"

    f.write("【Phase 1 - 干预入口】\n")
    f.write(f"用户: {user_msg}\n\n")

    intake_result = handle_intervention_intake(user_msg)

    f.write(f"识别: {intake_result['structured_data']['canonical_id']}\n")
    f.write(f"显示名: {intake_result['structured_data']['display_name']}\n\n")

    f.write("系统回复:\n")
    f.write(intake_result['reply_message'] + "\n\n")

    # ===== Phase 2: 资料补全 =====
    f.write("=" * 60 + "\n")
    f.write("【Phase 2 - 资料补全】\n")
    f.write("=" * 60 + "\n\n")

    # 用户回答
    user_answer = "我每天12点睡觉，7点起床，睡6个多小时，主要是容易醒"

    collector_result = run_full_intake_flow(
        user_id=user_id,
        profile_id="001",
        user_message=user_msg,
        user_answer=user_answer
    )

    f.write(f"用户回答: {user_answer}\n\n")

    f.write("系统提问:\n")
    for i, q in enumerate(collector_result.get("missing_questions", []), 1):
        f.write(f"  {i}. {q}\n")
    f.write("\n")

    f.write("系统回复（优先事项）:\n")
    f.write(collector_result.get("reply_message", "") + "\n\n")

    # ===== Phase 3: 调度 =====
    f.write("=" * 60 + "\n")
    f.write("【Phase 3 - 调度】\n")
    f.write("=" * 60 + "\n\n")

    # 模拟优先事项（从 Phase 2 结果中提取）
    priority_items = {
        "key": [
            "每天固定在 7:00 起床",
            "下午 2 点后不再喝咖啡或浓茶",
            "晚上 22:30 后不再刷手机，开始准备睡觉"
        ],
        "optional": ["晚饭后散步 15 分钟"],
        "record": ["实际睡觉时间", "实际起床时间", "夜间醒来次数"]
    }

    scheduler_result = run_intervention_scheduler(
        user_id=user_id,
        user_name=user_name,
        channel_id=channel_id,
        channel_type=channel_type,
        mention_target=mention_target,
        case_file_path=collector_result.get("case_file", ""),
        canonical_id=collector_result.get("canonical_id", "sleep-insomnia"),
        display_name=collector_result.get("display_name", "失眠 / 睡眠改善"),
        priority_items=priority_items
    )

    f.write("给用户的调整计划:\n")
    f.write(scheduler_result.get("user_plan", "") + "\n\n")

    f.write("提醒安排:\n")
    for r in scheduler_result.get("reminder_schedule", []):
        f.write(f"  {r.get('time')}: {r.get('message')}\n")
    f.write("\n")

    f.write("反馈安排:\n")
    for fb in scheduler_result.get("feedback_schedule", []):
        f.write(f"  {fb.get('id')}: {fb.get('time')} - {fb.get('message')[:50]}...\n")
    f.write("\n")

    f.write("cron写入结果:\n")
    f.write(f"  {scheduler_result.get('cron_write_results')}\n\n")

    f.write("case文件:\n")
    f.write(f"  {collector_result.get('case_file', '')}\n")

print(f"Output: {output_path}")
