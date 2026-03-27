#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import datetime
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("录入规则 - R008 身体不适保护")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

created_ts = int(datetime.datetime.now().timestamp() * 1000)

fields = {
    "rule_id": "R008",
    "rule_name": "身体不适保护",
    "rule_type": "硬规则",
    "target_scope": "恢复",
    "trigger_conditions": "body_status_notes 包含 胃不适/头痛/疼痛/发热/明显不适",
    "action": "暂停高强度训练和刺激性行为，优先恢复与观察",
    "priority": 10,
    "exception_conditions": "无",
    "source_type": "医疗",
    "source_ref": "initial_seed",
    "confidence": 0.93,
    "success_rate": 0,
    "enabled": True,
    "review_status": "已确认",
    "created_at": created_ts,
    "active_phase": "通用",
    "notes": "保护性规则，优先级应高于一般训练推进规则",
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
    print(f"  rule_id: R008")
    print(f"  rule_name: 身体不适保护")
    print(f"  rule_type: 硬规则")
    print(f"  trigger: body_status_notes 含不适关键词")
    print(f"  action: 暂停高强度，优先恢复")
    print(f"  priority: 10 (最高)")
    print(f"  enabled: true")

print("="*60)
