#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import datetime
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("录入规则 - R003 连续疲劳累积降负荷")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

created_ts = int(datetime.datetime.now().timestamp() * 1000)

fields = {
    "rule_id": "R003",
    "rule_name": "连续疲劳累积降负荷",
    "rule_type": "软规则",
    "target_scope": "周计划",
    "trigger_conditions": "连续2天 fatigue_score >= 7",
    "action": "安排1天低强度活动或完全休息，并减少本周后续计划复杂度",
    "priority": 8,
    "exception_conditions": "若第二天状态显著恢复，可保守执行原计划",
    "source_type": "知识",
    "source_ref": "initial_seed",
    "confidence": 0.84,
    "success_rate": 0,
    "enabled": True,
    "review_status": "已确认",
    "created_at": created_ts,
    "active_phase": "通用",
    "notes": "防止疲劳在多日累积后演变成明显过载",
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
    print(f"  rule_id: R003")
    print(f"  rule_name: 连续疲劳累积降负荷")
    print(f"  rule_type: 软规则")
    print(f"  trigger: 连续2天 fatigue_score >= 7")
    print(f"  action: 安排1天低强度活动或休息")
    print(f"  priority: 8")
    print(f"  enabled: true")

print("="*60)
