#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import datetime
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace\skills\lifeos-main\scripts')
import bitable_ops

print("="*60)
print("录入规则 - R012 医疗异常优先保护")
print("="*60)

token = bitable_ops.get_token()
if not token:
    print("[ERROR] Token failed")
    sys.exit(1)

created_ts = int(datetime.datetime.now().timestamp() * 1000)

fields = {
    "rule_id": "R012",
    "rule_name": "医疗异常优先保护",
    "rule_type": "硬规则",
    "target_scope": "医疗提醒",
    "trigger_conditions": "medical_records 中存在近期异常项或明确医生建议",
    "action": "优先遵循医疗建议，对训练、饮食或补剂做保守调整",
    "priority": 10,
    "exception_conditions": "无",
    "source_type": "医疗",
    "source_ref": "medical_records",
    "confidence": 0.95,
    "success_rate": 0,
    "enabled": True,
    "review_status": "已确认",
    "created_at": created_ts,
    "active_phase": "通用",
    "notes": "医疗建议优先于一般生活规则",
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
    print(f"  rule_id: R012")
    print(f"  rule_name: 医疗异常优先保护")
    print(f"  rule_type: 硬规则")
    print(f"  trigger: medical_records 有异常/医生建议")
    print(f"  action: 保守调整，遵循医嘱")
    print(f"  priority: 10 (最高)")
    print(f"  enabled: true")

print("="*60)
