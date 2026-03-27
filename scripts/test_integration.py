#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话层集成测试 - 验证本地数据库调用

此脚本模拟对话层调用 LifeOS 服务，验证数据是否正确写入本地 SQLite。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lifeos_service import get_service


def test_basic_operations():
    """测试基本操作"""
    print("=" * 60)
    print("LifeOS 本地数据库集成测试")
    print("=" * 60)
    
    # 1. 获取服务实例（金 - profile_id: 001）
    print("\n[1] 获取服务实例 (profile_id=001)")
    svc = get_service('001')
    print(f"  - 服务实例创建成功")
    
    # 2. 获取用户资料
    print("\n[2] 获取用户资料")
    profile = svc.health.get_profile()
    if profile:
        print(f"  - Profile ID: {profile.get('profile_id')}")
        print(f"  - Name: {profile.get('name')}")
    else:
        print("  - 未找到用户资料")
    
    # 3. 记录睡眠
    print("\n[3] 记录睡眠数据")
    result = svc.record_sleep(hours=7.5, quality=8)
    print(f"  - 结果: {result.get('message')}")
    print(f"  - Log ID: {result.get('log_id')}")
    
    # 4. 记录疲劳度
    print("\n[4] 记录疲劳度")
    result = svc.record_fatigue(score=4, notes='状态还行')
    print(f"  - 结果: {result.get('message')}")
    print(f"  - Log ID: {result.get('log_id')}")
    
    # 5. 记录训练
    print("\n[5] 记录训练")
    result = svc.record_training(brief='跑步3公里，力量训练20分钟', had_training=True)
    print(f"  - 结果: {result.get('message')}")
    print(f"  - Log ID: {result.get('log_id')}")
    
    # 6. 获取今日概览
    print("\n[6] 获取今日概览")
    summary = svc.get_today_summary()
    if summary.get('has_data'):
        print(f"  - 日期: {summary.get('date')}")
        print(f"  - 睡眠: {summary.get('sleep_hours')} 小时")
        print(f"  - 疲劳度: {summary.get('fatigue_score')}")
        print(f"  - 是否训练: {'是' if summary.get('had_training') else '否'}")
    else:
        print(f"  - {summary.get('message')}")
    
    # 7. 查询数据库验证
    print("\n[7] 数据库验证")
    from db import query_one
    record = query_one(
        "SELECT * FROM daily_logs WHERE profile_id = ? AND date = ?",
        ('001', datetime.now().strftime("%Y-%m-%d"))
    )
    if record:
        print(f"  - 数据库记录验证成功")
        print(f"  - Log ID: {record.get('log_id')}")
        print(f"  - Sleep: {record.get('sleep_hours')}h")
        print(f"  - Fatigue: {record.get('fatigue_score')}")
    else:
        print("  - 未找到数据库记录")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    from datetime import datetime
    test_basic_operations()
