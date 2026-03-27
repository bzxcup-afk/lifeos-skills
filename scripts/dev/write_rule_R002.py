#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import datetime
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("录入规则 - R002 高疲劳转恢复日")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

created_ts = int(datetime.datetime.now().timestamp() * 1000)

fields = {
    "rule_id": "R002",
    "rule_name": "高疲劳转恢复日",
    "rule_type": "硬规则",
    "target_scope": "恢复",
    "trigger_conditions": "fatigue_score >= 8",
    "action": "当天转为恢复日，减少任务量，不安排高负荷训练",
    "priority": 9,
    "exception_conditions": "无",
    "source_type": "知识",
    "source_ref": "initial_seed",
    "confidence": 0.88,
    "success_rate": 0,
    "enabled": True,
    "review_status": "已确认",
    "created_at": created_ts,
    "active_phase": "通用",
    "notes": "高疲劳时优先恢复，比硬撑更重要",
    "created_by": "系统"
}

record_id, err = bitable_ops.create_record(token, "rules", fields)

if err:
    print(f"[ERROR] {err}")
else:
    print(f"[OK] 规则创建成功")
    print(f"     record_id: {record_id}")
    print()
    print("规则详情:")
    print(f"  rule_id: R002")
    print(f"  rule_name: 高疲劳转恢复日")
    print(f"  rule_type: 硬规则")
    print(f"  trigger: fatigue_score >= 8")
    print(f"  action: 当天转为恢复日")
    print(f"  priority: 9")
    print(f"  enabled: true")
    print(f"  review_status: 已确认")

print("="*60)
