#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

token = bitable_ops.get_token()
print('Token:', 'OK' if token else 'FAIL')

# 1. 读取 profile
profile = bitable_ops.get_profile(token)
print('\n=== Profile ===')
if profile:
    fields = profile.get('fields', {})
    bd = fields.get('birth_date', '')
    age = bitable_ops.calculate_age(bd)
    print('Name:', fields.get('name'))
    print('Birth:', bd, '-> Age:', age)
    print('Height:', fields.get('height_cm'), 'cm')
    print('Weight:', fields.get('baseline_weight_kg'), 'kg')
    print('Goal:', fields.get('long_term_goal'))
    print('Phase:', fields.get('current_phase'))
    print('Constraints:', fields.get('health_constraints'))
    print('Chronic:', fields.get('chronic_conditions'))
else:
    print('No profile found')

# 2. 读取最近7天 daily_log
print('\n=== Recent Daily Logs (7 days) ===')
logs = bitable_ops.get_recent_daily_logs(token, days=7)
print('Found:', len(logs), 'records')
for log in logs[:7]:
    f = log.get('fields', {})
    date = f.get('date', '')
    # 转换时间戳
    if isinstance(date, (int, float)):
        import datetime
        date = datetime.datetime.fromtimestamp(date/1000).strftime('%Y-%m-%d')
    print('  Date:', date, '| Weight:', f.get('weight_kg'), '| Fatigue:', f.get('fatigue_score'), '| Sleep:', f.get('sleep_hours'), 'h | Training:', f.get('had_training'))

# 3. 计算状态摘要
print('\n=== State Summary ===')
summary = bitable_ops.get_state_summary(logs)
print(json.dumps(summary, ensure_ascii=False, indent=2))

# 4. 读取 enabled rules
print('\n=== Enabled Rules ===')
rules = bitable_ops.get_enabled_rules(token)
print('Found:', len(rules), 'rules')
for r in rules:
    f = r.get('fields', {})
    print('  ', f.get('rule_id'), ':', f.get('rule_name'), '-', f.get('rule_type'), '- Priority:', f.get('priority'))

# 5. 读取 medical records
print('\n=== Medical Records ===')
records, _ = bitable_ops.read_records(token, 'medical_records', limit=5)
print('Found:', len(records), 'records')
for r in records:
    f = r.get('fields', {})
    print('  -', f.get('record_date'), ':', f.get('diagnosis'), '|', f.get('key_metrics_json'))

# 6. 读取 medication
print('\n=== Medications/Supplements ===')
meds = bitable_ops.get_active_medications(token)
print('Active:', len(meds), 'items')
for m in meds:
    f = m.get('fields', {})
    print('  -', f.get('name'), ':', f.get('dosage'), '(', f.get('frequency'), ')')

# 7. 读取 event_log
print('\n=== Recent Events (7 days) ===')
events = bitable_ops.get_recent_events(token, days=7)
print('Found:', len(events), 'events')
for e in events:
    f = e.get('fields', {})
    print('  -', f.get('event_type'), ':', f.get('event_title'))

# 8. 检查是否有生效中的周计划
print('\n=== Weekly Plan Check ===')
wp = bitable_ops.get_active_weekly_plan(token)
if wp:
    print('Active weekly plan exists!')
    f = wp.get('fields', {})
    print('  Week:', f.get('week_start'), '-', f.get('week_end'))
    print('  Goal:', f.get('weekly_goal'))
else:
    print('No active weekly plan - can generate one')
