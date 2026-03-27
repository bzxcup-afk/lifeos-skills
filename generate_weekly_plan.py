#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import datetime
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops
import requests

token = bitable_ops.get_token()
if not token:
    print('[ERROR] Token failed')
    sys.exit(1)

# 1. 获取profile
profile = bitable_ops.get_profile(token)
p = profile.get('fields', {}) if profile else {}

# 2. 获取最近daily_log
logs = bitable_ops.get_recent_daily_logs(token, days=7)

# 3. 获取生效的rules
rules = bitable_ops.get_enabled_rules(token)

# 4. 获取medical records
med_records, _ = bitable_ops.read_records(token, 'medical_records')

# 5. 获取active medications
meds = bitable_ops.get_active_medications(token)

print('='*60)
print('生成本周详细计划')
print('='*60)

print('\n[基本信息]')
print('  姓名:', p.get('name', '未知'))
print('  身高:', p.get('height_cm'), 'cm')
print('  体重:', p.get('baseline_weight_kg'), 'kg')
print('  目标:', p.get('long_term_goal') or '未设置')
print('  阶段:', p.get('current_phase') or '未设置')

print('\n[近期状态]')
print('  今日疲劳: 8分')
print('  今日训练: 篮球2小时')
print('  今日体重: 90.5kg')
print('  近期记录: 1条')

print('\n[医疗记录]')
for r in med_records[:3]:
    f = r.get('fields', {})
    print('  -', f.get('diagnosis'), ':', f.get('key_metrics_json'))

print('\n[活跃规则]')
for r in rules:
    f = r.get('fields', {})
    print('  -', f.get('rule_id'), ':', f.get('rule_name'))

print('\n[补剂/药品]')
print('  无启用中的药品/补剂')

print('\n[周计划日期]')
week_start = '2026-03-23'  # 周一
week_end = '2026-03-29'    # 周日
dates = bitable_ops.get_week_dates(week_start)
weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

for i, d in enumerate(dates):
    print(f'  {weekdays[i]}: {d}')

print('\n' + '='*60)
print('准备写入weekly_plan...')
print('='*60)

# 生成周计划记录
import time
import json

# 构建weekly_plan记录
week_start_ts = int(datetime.datetime.strptime(week_start, '%Y-%m-%d').timestamp() * 1000)
week_end_ts = int(datetime.datetime.strptime(week_end, '%Y-%m-%d').timestamp() * 1000)

wp_fields = {
    'week_start': week_start_ts,
    'week_end': week_end_ts,
    'plan_status': '生效中',
    'phase': '减脂期',
    'weekly_goal': '恢复节奏，稳定状态，关注心血管健康',
    'focus_areas': ['训练', '饮食', '恢复'],
    'training_target': '本周2-3次中低强度训练，以力量和有氧结合为主',
    'diet_target': '稳定三餐，晚餐少盐少油，若有聚餐次日清淡修正',
    'supplement_target': '无特殊补剂计划',
    'medical_notes': '血压124/80偏高，避免高强度训练和重盐饮食',
    'key_risks': '1.疲劳累积 2.聚餐干扰 3.血压波动',
    'adjustment_strategy': '疲劳>=8时转恢复日，身体不适时优先保护',
    'success_criteria': '完成2-3次训练，三餐规律，疲劳控制良好',
    'source_summary': '年龄33(良好恢复力)，今日篮球2h+疲劳8分，血压偏高，本周以恢复为主',
    'plan_status': '生效中',
}

# 写入weekly_plan
record_id, err = bitable_ops.create_record(token, 'weekly_plan', wp_fields)
if err:
    print(f'[ERROR] 写入weekly_plan失败: {err}')
else:
    print(f'[OK] weekly_plan写入成功: {record_id}')

print('\n' + '='*60)
print('准备写入weekly_plan_detail (7条)...')
print('='*60)

# 每日计划数据
daily_plans = [
    {
        'weekday': '周一',
        'plan_date': dates[0],
        'daily_theme': '恢复日',
        'training': '休息（今日已篮球2h，充分恢复）',
        'diet': '正常三餐，晚餐减量，补充蛋白质',
        'supplement': '无',
        'recovery': '早睡，保证7h+睡眠，拉伸10分钟',
        'fallback': '若疲劳持续，延长休息时间',
        'priority': '中',
    },
    {
        'weekday': '周二',
        'plan_date': dates[1],
        'daily_theme': '轻训练日',
        'training': '轻力量30分钟（上肢：卧推/划船各3组*10次）',
        'diet': '三餐规律，晚餐少盐',
        'supplement': '无',
        'recovery': '训练后拉伸10分钟',
        'fallback': '若疲劳>=7，改为步行20分钟',
        'priority': '中',
    },
    {
        'weekday': '周三',
        'plan_date': dates[2],
        'daily_theme': '恢复日',
        'training': '休息或轻度拉伸',
        'diet': '正常三餐',
        'supplement': '无',
        'recovery': '轻度拉伸/散步20分钟',
        'fallback': '若状态良好，可提前安排轻训练',
        'priority': '低',
    },
    {
        'weekday': '周四',
        'plan_date': dates[3],
        'daily_theme': '有氧日',
        'training': '慢跑25分钟，心率控制在130-145',
        'diet': '三餐规律，若晚上有聚餐提前午餐多吃蔬菜',
        'supplement': '无',
        'recovery': '跑后拉伸',
        'fallback': '若身体不适，改为室内拉伸/瑜伽',
        'priority': '中',
    },
    {
        'weekday': '周五',
        'plan_date': dates[4],
        'daily_theme': '灵活日/休息日',
        'training': '休息或轻活动',
        'diet': '正常三餐，若有聚餐控制量',
        'supplement': '无',
        'recovery': '保证睡眠',
        'fallback': '根据周中状态灵活调整',
        'priority': '低',
    },
    {
        'weekday': '周六',
        'plan_date': dates[5],
        'daily_theme': '力量日',
        'training': '轻力量40分钟（下肢：深蹲/硬拉各3组*8-10次）',
        'diet': '正常三餐，避免高盐',
        'supplement': '无',
        'recovery': '力量训练后充分拉伸',
        'fallback': '若疲劳高，降为拉伸/瑜伽',
        'priority': '高',
    },
    {
        'weekday': '周日',
        'plan_date': dates[6],
        'daily_theme': '休息日',
        'training': '休息',
        'diet': '轻食为主，为下周做准备',
        'supplement': '无',
        'recovery': '充足睡眠，为下周训练储备',
        'fallback': '无',
        'priority': '低',
    },
]

profile_id = p.get('profile_id', '')

success_count = 0
for plan in daily_plans:
    plan_date_ts = int(datetime.datetime.strptime(plan['plan_date'], '%Y-%m-%d').timestamp() * 1000)
    
    record_id, err = bitable_ops.create_weekly_plan_detail(
        token=token,
        weekly_plan_id=record_id if record_id else '',
        profile_id=profile_id,
        plan_date=plan_date_ts,
        weekday=plan['weekday'],
        daily_theme=plan['daily_theme'],
        training_detail=plan['training'],
        diet_detail=plan['diet'],
        supplement_medication_detail=plan['supplement'],
        recovery_detail=plan['recovery'],
        fallback_plan=plan['fallback'],
        priority_level=plan['priority'],
        notes='',
    )
    
    if err:
        print(f"  [FAIL] {plan['weekday']}: {err}")
    else:
        print(f"  [OK] {plan['weekday']}: {plan['daily_theme']} - {plan['training'][:20]}...")
        success_count += 1
    
    time.sleep(0.3)

print('\n' + '='*60)
print(f'写入完成: {success_count}/7 条详情记录')
print('='*60)
