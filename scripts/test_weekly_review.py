# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts")
from intervention_weekly_review import run_weekly_review

result = run_weekly_review(
    user_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
    problem_id="sleep-insomnia",
    user_name="金",
    channel_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
    channel_type="direct",
    mention_target="@金",
    user_feedback="睡眠稍微好一点了，但还是会醒，晚上少看手机有时候能做到，早起比较难",
    last_week_items=[
        "每天固定在 7:00 起床",
        "下午 2 点后不再喝咖啡或浓茶",
        "晚上 22:30 后不再刷手机"
    ]
)

output_path = r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\output\test_weekly_review.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("Phase 4: 周复盘与下一周计划测试\n")
    f.write("=" * 60 + "\n\n")
    
    f.write(f"[success] {result['success']}\n")
    
    if result.get("week_summary"):
        f.write(f"\n【周总结】\n{result['week_summary']}\n")
    
    if result.get("next_week_strategy"):
        f.write(f"\n【下周策略】\n{result['next_week_strategy']}\n")
    
    if result.get("next_week_priorities"):
        f.write(f"\n【下周优先事项】\n")
        for i, item in enumerate(result['next_week_priorities'].get("key", []), 1):
            f.write(f"  {i}. {item}\n")
    
    if result.get("scheduler_result"):
        f.write(f"\n【提醒安排】\n")
        for r in result['scheduler_result'].get("reminder_schedule", []):
            f.write(f"  {r.get('time')}: {r.get('message')}\n\n")
    
    if result.get("scheduler_result", {}).get("feedback_schedule"):
        f.write(f"【反馈安排】\n")
        for fb in result['scheduler_result'].get("feedback_schedule", []):
            f.write(f"  {fb.get('time')}: {fb.get('message')}\n\n")
    
    f.write(f"[case文件] {result.get('case_file', '')}\n")

print(f"Output: {output_path}")
