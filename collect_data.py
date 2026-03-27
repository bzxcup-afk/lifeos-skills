#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import datetime
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

token = bitable_ops.get_token()
if not token:
    print('[ERROR] Token failed')
    sys.exit(1)

print('='*60)
print('生成本周计划 - 数据收集')
print('='*60)

# 1. 读取 profile
profile = bitable_ops.get_profile(token)
p = profile.get('fields', {}) if profile else {}

print('\n[Profile]')
print('  姓名:', p.get('name', '未知'))
print('  身高:', p.get('height_cm'), 'cm')
print('  目标:', p.get('long_term_goal') or '未设置')
print('  阶段:', p.get('current_phase') or '未设置')

# 2. 读取最近 daily_log
print('\n[Daily Logs]')
logs = bitable_ops.get_recent_daily_logs(token, days=7)
print('  记录数:', len(logs))

recent_fatigue = []
recent_weights = []
training_days = 0

for log in logs:
    f = log.get('fields', {})
    fatigue = f.get('fatigue_score')
    weight = f.get('weight_kg')
    had_training = f.get('had_training')
    
    if fatigue:
        recent_fatigue.append(fatigue)
    if weight:
        recent_weights.append(weight)
    if had_training:
        training_days += 1

print('  近期体重:', recent_weights if recent_weights else '无')
print('  近期疲劳:', recent_fatigue if recent_fatigue else '无')
print('  训练天数:', training_days)

# 3. 读取 rules
print('\n[Enabled Rules]')
rules = bitable_ops.get_enabled_rules(token)
print('  规则数:', len(rules))
triggered = []
for r in rules:
    f = r.get('fields', {})
    print('  -', f.get('rule_id'), ':', f.get('rule_name'), '| Priority:', f.get('priority'))

# 4. 读取 medical
print('\n[Medical Records]')
records, _ = bitable_ops.read_records(token, 'medical_records', limit=10)
print('  记录数:', len(records))
for r in records[:3]:
    f = r.get('fields', {})
    print('  -', f.get('record_date'), ':', f.get('diagnosis'), '|', f.get('key_metrics_json'))

# 5. 读取 events
print('\n[Recent Events]')
events = bitable_ops.get_recent_events(token, days=7)
print('  事件数:', len(events))
for e in events[:5]:
    f = e.get('fields', {})
    print('  -', f.get('event_type'), ':', f.get('event_title'))

# 6. 读取 medication
print('\n[Medications]')
meds = bitable_ops.get_active_medications(token)
print('  启用数:', len(meds))
for m in meds:
    f = m.get('fields', {})
    print('  -', f.get('name'), ':', f.get('dosage'), f.get('frequency'))

print('\n' + '='*60)
print('数据收集完成')
print('='*60)
