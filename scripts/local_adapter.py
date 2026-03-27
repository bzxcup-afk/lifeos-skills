#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeOS 本地数据库适配器

提供与 bitable_ops.py 兼容的接口，但底层使用本地 SQLite。

使用方式：
    # 原来使用 bitable_ops.py
    from bitable_ops import save_daily_log, get_profile
    
    # 现在可以直接替换为：
    from local_adapter import save_daily_log, get_profile
    
    # 或者通过 bitable_ops 的兼容性模式自动切换
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# 确保可以导入同级模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from db import query_one, query_many, insert, update
from health_service import get_service as get_health_service


# ============================================================================
# 兼容性常量
# ============================================================================

# 模拟飞书的表名常量，实际使用本地表
TABLE_PROFILE = "profiles"
TABLE_DAILY_LOG = "daily_logs"
TABLE_WEEKLY_PLAN = "weekly_plans"
TABLE_MEDICAL_RECORDS = "medical_records"
TABLE_EVENTS = "events"
TABLE_RULES = "rules"


# ============================================================================
# Token 相关（本地模式不需要，但为了兼容性提供空实现）
# ============================================================================

def get_token() -> Optional[str]:
    """
    获取访问令牌（本地模式不需要，返回 None）
    
    为了保持与 bitable_ops.py 的接口兼容，返回 None
    调用方应检查返回值，如果是 None 则使用本地模式
    """
    return None


def is_local_mode() -> bool:
    """
    检查是否处于本地模式
    
    可以通过环境变量 LIFEOS_MODE 强制指定：
    - LIFEOS_MODE=local: 强制本地模式
    - LIFEOS_MODE=feishu: 强制飞书模式（会检查 token）
    
    默认行为：
    - 如果 config/config.json 中 database.path 存在且有效，使用本地模式
    """
    mode = os.environ.get('LIFEOS_MODE', '').lower()
    if mode == 'local':
        return True
    if mode == 'feishu':
        return False
    
    # 自动检测：检查数据库文件是否存在
    try:
        from db import get_db_path
        db_path = get_db_path()
        return os.path.exists(db_path)
    except:
        return False


# ============================================================================
# Profile 相关操作
# ============================================================================

def get_profile(profile_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    获取用户资料
    
    Args:
        profile_id: 用户ID，默认使用当前配置的 profile
    
    Returns:
        用户资料字典，未找到返回 None
    """
    svc = get_health_service(profile_id)
    return svc.get_profile()


def get_current_bitable():
    """
    获取当前 Bitable 配置（本地模式下返回模拟配置）
    
    为了兼容性，返回一个包含 profile_id 的字典
    """
    return {
        "profile_id": os.environ.get('LIFEOS_PROFILE_ID', '001'),
        "mode": "local"
    }


# ============================================================================
# Daily Log 相关操作
# ============================================================================

def save_daily_log(token: Optional[str], fields: Dict[str, Any], 
                   profile_id: Optional[str] = None) -> Dict[str, Any]:
    """
    保存每日记录（兼容 bitable_ops.py 接口）
    
    Args:
        token: 飞书 token（本地模式忽略）
        fields: 要保存的字段
        profile_id: 用户ID
    
    Returns:
        包含 record_id 和 err 的字典
    """
    try:
        # 确保有 profile_id
        if not profile_id:
            profile_id = fields.get('profile_id', '001')
        
        svc = get_health_service(profile_id)
        
        # 提取并转换字段
        data = {}
        
        # 日期处理
        if 'date' in fields:
            date_val = fields['date']
            if isinstance(date_val, (int, float)):
                # 时间戳转字符串
                from datetime import datetime
                date_val = datetime.fromtimestamp(date_val / 1000).strftime('%Y-%m-%d')
            data['date'] = date_val
        
        # 数字字段
        for key in ['sleep_hours', 'sleep_quality', 'fatigue_score', 
                   'energy_score', 'weight_kg']:
            if key in fields:
                data[key] = fields[key]
        
        # 布尔字段
        if 'had_training' in fields:
            data['had_training'] = bool(fields['had_training'])
        
        # 文本字段
        for key in ['training_brief', 'diet_status', 'body_status_notes',
                   'today_summary', 'state_tags']:
            if key in fields:
                data[key] = fields[key]
        
        # 保存
        log_id = svc.save_daily_log(data)
        
        return {
            'record_id': str(log_id),
            'err': None
        }
        
    except Exception as e:
        return {
            'record_id': None,
            'err': str(e)
        }


def get_recent_daily_logs(token: Optional[str], days: int = 7,
                          profile_id: Optional[str] = None):
    """
    获取最近 N 天的每日记录（兼容接口）
    """
    svc = get_health_service(profile_id)
    return svc.get_recent_logs(days=days)


# ============================================================================
# 其他兼容接口
# ============================================================================

def read_records(token: Optional[str], table_key: str, 
                 filterformula: Optional[str] = None, 
                 limit: int = 100,
                 profile_id: Optional[str] = None):
    """
    读取记录（兼容接口，目前仅支持 daily_logs）
    """
    if table_key in ['daily_log', 'daily_logs', '每日记录']:
        svc = get_health_service(profile_id)
        return svc.get_recent_logs(days=limit), None
    
    return [], f"Table {table_key} not supported in local mode"


def update_record(token: Optional[str], table_key: str, 
                  record_id: str, fields: Dict[str, Any],
                  profile_id: Optional[str] = None):
    """
    更新记录（兼容接口）
    """
    try:
        from db import update
        table_map = {
            'daily_log': 'daily_logs',
            'daily_logs': 'daily_logs',
            'profile': 'profiles'
        }
        table = table_map.get(table_key, table_key)
        
        # 移除不能更新的字段
        data = {k: v for k, v in fields.items() 
                if k not in ['log_id', 'profile_id', 'created_at']}
        data['updated_at'] = __import__('datetime').datetime.now().isoformat()
        
        update(table, data, "log_id = ?", (record_id,))
        
        return True, None
    except Exception as e:
        return False, str(e)


# ============================================================================
# 模块自测
# ============================================================================

if __name__ == "__main__":
    print("Local Adapter Test")
    print("==================")
    
    # 测试模式检测
    print(f"\nLocal mode: {is_local_mode()}")
    
    # 测试获取 profile
    print("\nTest get_profile:")
    profile = get_profile('001')
    if profile:
        print(f"  Found: {profile.get('name')} (ID: {profile.get('profile_id')})")
    else:
        print("  Not found")
    
    # 测试保存 daily log
    print("\nTest save_daily_log:")
    result = save_daily_log(
        None,  # token
        {
            'date': '2026-03-26',
            'sleep_hours': 7.5,
            'fatigue_score': 4,
            'had_training': True,
            'training_brief': 'Test training'
        },
        '001'
    )
    if result.get('err'):
        print(f"  Error: {result['err']}")
    else:
        print(f"  Saved: ID {result['record_id']}")
    
    print("\nTest completed!")
