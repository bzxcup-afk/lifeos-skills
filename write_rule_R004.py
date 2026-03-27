#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import datetime
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("录入规则 - R004 聚餐后修正日")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

created_ts = int(datetime.datetime.now().timestamp() * 1000)

fields = {
    "rule_id": "R004",
    "rule_name": "聚餐后修正日",
    "rule_type": "软规则",
    "target_scope": "饮食",
    "trigger_conditions": "前一天存在 event_type = 聚餐",
    "action": "次日饮食清淡，避免额外高热量摄入，优先蛋白质和规律进食",
    "priority": 7,
    "exception_conditions": "无",
    "source_type": "知识",
    "source_ref": "initial_seed",
    "confidence": 0.82,
    "success_rate": 0,
    "enabled": True,
    "review_status": "已确认",
    "created_at": created_ts,
    "active_phase": "减脂期",
    "notes": "重点不是补偿性极端节食，而是把节奏拉回正常",
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
    print(f"  rule_id: R004")
    print(f"  rule_name: 聚餐后修正日")
    print(f"  rule_type: 软规则")
    print(f"  trigger: 前一天 event_type = 聚餐")
    print(f"  action: 次日清淡饮食，蛋白质为主")
    print(f"  priority: 7")
    print(f"  enabled: true")
    print(f"  active_phase: 减脂期")

print("="*60)
