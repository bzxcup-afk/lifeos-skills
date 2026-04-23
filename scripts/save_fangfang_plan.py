import sys
import os
sys.path.insert(0, '.')
from db import query_one, insert
from datetime import datetime, timedelta

# 写入周计划主表
week_start = '2026-03-31'  # 周一开始
week_end = '2026-04-06'

plan_data = {
    'profile_id': '002',
    'week_start': week_start,
    'week_end': week_end,
    'plan_status': 'active',
    'weekly_goal': '减脂为主，提升体能',
    'key_focus': '瑜伽为主，避免跑步，清淡饮食',
    'risk_notes': '不吃肉和糖，控制碳水',
    'adjustment_principles': '根据身体状态调整训练强度'
}

result = insert('weekly_plans', plan_data)
print('insert weekly_plans result:', result)

# 获取刚插入的 plan_id
plan = query_one('SELECT * FROM weekly_plans WHERE profile_id = ? AND week_start = ?', ['002', week_start])
if plan:
    plan_id = plan['plan_id']
    print('plan_id:', plan_id)
    
    # 写入每天的明细
    base_date = datetime(2026, 3, 31)
    days = [
        {'weekday': '周一', 'theme': '流瑜伽', 'training': '瑜伽45分钟（流瑜伽）', 'diet': '早餐燕麦+水果，午餐蔬菜沙拉+鱼肉，晚餐蔬菜+豆腐', 'recovery': '睡前拉伸10分钟', 'notes': '训练日'},
        {'weekday': '周二', 'theme': '休息恢复', 'training': '休息', 'diet': '清淡饮食，多吃蔬菜', 'recovery': '泡沫轴放松', 'notes': '休息日'},
        {'weekday': '周三', 'theme': '力量瑜伽', 'training': '瑜伽60分钟（力量瑜伽）', 'diet': '低糖饮食，避免肉类', 'recovery': '热敷肩颈', 'notes': '训练日'},
        {'weekday': '周四', 'theme': '休息恢复', 'training': '休息', 'diet': '轻食为主', 'recovery': '散步30分钟', 'notes': '休息日'},
        {'weekday': '周五', 'theme': '晨间拉伸', 'training': '瑜伽45分钟（晨间拉伸）', 'diet': '高蛋白早餐，午餐正常，晚餐少碳水', 'recovery': '足浴放松', 'notes': '训练日'},
        {'weekday': '周六', 'theme': '核心平衡', 'training': '瑜伽60分钟（核心+平衡）', 'diet': '周末补充蛋白质', 'recovery': '充足睡眠', 'notes': '训练日'},
        {'weekday': '周日', 'theme': '休养', 'training': '休息', 'diet': '清淡饮食，间歇性断食16:8', 'recovery': '休养为主', 'notes': '休息日'},
    ]
    
    for i, day in enumerate(days):
        plan_date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
        detail = {
            'plan_id': plan_id,
            'profile_id': '002',
            'plan_date': plan_date,
            'weekday': day['weekday'],
            'daily_theme': day['theme'],
            'training_detail': day['training'],
            'diet_detail': day['diet'],
            'supplement_medication_detail': '维生素B族 晚餐后',
            'recovery_detail': day['recovery'],
            'notes': day['notes']
        }
        r = insert('weekly_plan_details', detail)
        print(f'insert {day["weekday"]} result:', r)
    
    print('done - weekly plan saved')
else:
    print('failed to get plan after insert')
