#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""健康数据服务 - 本地SQLite版"""

import json
from datetime import datetime, timedelta
from db import query_one, query_many, insert, update


class HealthService:
    """健康数据服务类"""
    
    def __init__(self, profile_id=None):
        self.profile_id = profile_id
    
    # ========== Profile ==========
    
    def get_profile(self, profile_id=None):
        pid = profile_id or self.profile_id
        if not pid:
            return None
        return query_one("SELECT * FROM profiles WHERE profile_id = ?", (pid,))
    
    def update_profile(self, data, profile_id=None):
        pid = profile_id or self.profile_id
        if not pid:
            return False
        
        data = {k: v for k, v in data.items() if k not in ['profile_id', 'created_at']}
        data['updated_at'] = datetime.now().isoformat()
        
        update("profiles", data, "profile_id = ?", (pid,))
        return True
    
    # ========== Daily Log ==========
    
    def get_daily_log(self, date, profile_id=None):
        pid = profile_id or self.profile_id
        if not pid:
            return None
        return query_one(
            "SELECT * FROM daily_logs WHERE profile_id = ? AND date = ?",
            (pid, date)
        )
    
    def get_recent_logs(self, days=7, profile_id=None):
        pid = profile_id or self.profile_id
        if not pid:
            return []
        
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return query_many(
            "SELECT * FROM daily_logs WHERE profile_id = ? AND date >= ? ORDER BY date DESC",
            (pid, since)
        )
    
    def save_daily_log(self, data, profile_id=None):
        pid = profile_id or self.profile_id
        if not pid:
            return None
        
        data['profile_id'] = pid
        if 'date' not in data:
            data['date'] = datetime.now().strftime("%Y-%m-%d")
        
        existing = self.get_daily_log(data['date'], pid)
        
        data = {k: v for k, v in data.items() if k not in ['log_id', 'created_at']}
        data['updated_at'] = datetime.now().isoformat()
        
        if existing:
            update("daily_logs", data, "log_id = ?", (existing['log_id'],))
            return existing['log_id']
        else:
            return insert("daily_logs", data)
    
    # ========== Summary ==========
    
    def get_summary(self, days=7, profile_id=None):
        pid = profile_id or self.profile_id
        logs = self.get_recent_logs(days, pid)
        
        if not logs:
            return {}
        
        total_fatigue = sum(l.get('fatigue_score', 0) or 0 for l in logs)
        total_energy = sum(l.get('energy_score', 0) or 0 for l in logs)
        total_sleep = sum(l.get('sleep_hours', 0) or 0 for l in logs)
        training_days = sum(1 for l in logs if l.get('had_training'))
        
        n = len(logs)
        recent_weight = None
        for l in logs:
            if l.get('weight_kg'):
                recent_weight = l['weight_kg']
                break
        
        return {
            'avg_fatigue': round(total_fatigue / n, 1) if n else 0,
            'avg_energy': round(total_energy / n, 1) if n else 0,
            'avg_sleep_hours': round(total_sleep / n, 1) if n else 0,
            'training_days': training_days,
            'total_days': n,
            'recent_weight': recent_weight
        }


def get_service(profile_id=None):
    return HealthService(profile_id)
