# -*- coding: utf-8 -*-
"""
Phase 3 测试脚本
"""
import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")
from intervention_scheduler import (
    run_intervention_scheduler,
    load_existing_tasks,
    generate_reminder_candidates,
    MERGE_TIME_DIFF_MINUTES
)

output_path = r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\output\test_scheduler.txt"

user_id = "ou_fde56bd8d48eca22b3d57ab990ee4f02"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("Phase 3: 干预调度测试\n")
    f.write("=" * 60 + "\n\n")

    # Step 1-2: 读取已有任务和生成候选
    f.write("【Step 1-2】已有任务 & 提醒候选\n")
    existing = load_existing_tasks(user_id)
    f.write(f"已有时间点: {list(existing.keys())}\n")
    for t, tasks in existing.items():
        for task in tasks:
            f.write(f"  - {t}: {task.get('task_type')} - {task.get('drug_name') or task.get('reminder_title')}\n")

    candidates = generate_reminder_candidates("sleep-insomnia", {})
    f.write(f"\n提醒候选:\n")
    for c in candidates:
        f.write(f"  - {c.get('suggested_time')} {c.get('title')}: {c.get('items')}\n")

    f.write(f"\n合并阈值: {MERGE_TIME_DIFF_MINUTES} 分钟\n")
    f.write("(药品时间槽: 早餐前=07:00, 晚餐前=17:00, 晚餐后=18:00)\n")
    f.write("(干预时间: 07:00, 14:00, 21:00)\n")
    f.write("(时间差都超过30分钟，不会合并，这是正确的)\n\n")

    # Step 3: 完整流程
    priority_items = {
        "key": [
            "每天固定在 7:00 起床",
            "下午 2 点后不再喝咖啡或浓茶",
            "晚上 22:30 后不再刷手机，开始准备睡觉"
        ],
        "optional": ["晚饭后散步 15 分钟"],
        "record": ["实际睡觉时间", "实际起床时间", "夜间醒来次数"]
    }

    result = run_intervention_scheduler(
        user_id=user_id,
        user_name="金",
        channel_id=user_id,
        channel_type="direct",
        mention_target="@金",
        case_file_path=str(r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\cases\sleep-insomnia\case-ou_fde56bd8d48eca22b3d57ab990ee4f02-20260405.md"),
        canonical_id="sleep-insomnia",
        display_name="失眠 / 睡眠改善",
        priority_items=priority_items
    )

    f.write("=" * 60 + "\n")
    f.write("【完整流程结果】\n")
    f.write("=" * 60 + "\n\n")

    f.write(f"[success] {result['success']}\n\n")

    f.write("【给用户的调整计划】\n")
    f.write(result['user_plan'] + "\n\n")

    f.write("【提醒安排】\n")
    for r in result.get("reminder_schedule", []):
        f.write(f"  {r.get('time')}: {r.get('message')}\n\n")

    f.write("【反馈安排】\n")
    for fb in result.get("feedback_schedule", []):
        f.write(f"  {fb.get('id')}: {fb.get('time')} - {fb.get('message')[:50]}...\n\n")

    f.write("【cron写入结果】\n")
    f.write(f"  {result.get('cron_write_results')}\n")

print(f"Output: {output_path}")
