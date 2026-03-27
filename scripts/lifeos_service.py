#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeOS 核心服务入口 - 对话层调用接口

此模块为对话层提供统一的数据访问入口，屏蔽底层实现细节。
调用方只需知道 profile_id，无需关心数据来源。
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from db import query_one, query_many, insert, update
from health_service import HealthService, get_service as get_health_service


class LifeOSService:
    """LifeOS 核心服务类 - 对话层统一入口"""
    
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        self._health_svc = None
    
    @property
    def health(self) -> HealthService:
        """懒加载健康服务"""
        if self._health_svc is None:
            self._health_svc = get_health_service(self.profile_id)
        return self._health_svc
    
    # ========== 快捷操作方法 ==========
    
    def record_sleep(self, hours: float, quality: Optional[int] = None, 
                     date: Optional[str] = None) -> Dict[str, Any]:
        """
        记录睡眠
        
        Args:
            hours: 睡眠时长（小时）
            quality: 睡眠质量（1-10）
            date: 日期，默认今天
        
        Returns:
            操作结果
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 获取现有记录（如果有）
        existing = self.health.get_daily_log(date)
        
        data = {
            'date': date,
            'sleep_hours': hours,
        }
        if quality is not None:
            data['sleep_quality'] = quality
        
        # 合并现有数据
        if existing:
            for key in ['fatigue_score', 'energy_score', 'weight_kg', 'had_training',
                       'training_brief', 'diet_status', 'body_status_notes', 
                       'today_summary', 'state_tags']:
                if existing.get(key) and key not in data:
                    data[key] = existing[key]
        
        log_id = self.health.save_daily_log(data)
        
        return {
            'success': True,
            'log_id': log_id,
            'date': date,
            'message': f'已记录 {date} 睡眠 {hours} 小时'
        }
    
    def record_fatigue(self, score: int, notes: Optional[str] = None,
                       date: Optional[str] = None) -> Dict[str, Any]:
        """记录疲劳度"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        existing = self.health.get_daily_log(date)
        
        data = {
            'date': date,
            'fatigue_score': score,
        }
        if notes:
            data['body_status_notes'] = notes
        
        # 合并现有数据
        if existing:
            for key in ['sleep_hours', 'sleep_quality', 'energy_score', 'weight_kg',
                       'had_training', 'training_brief', 'diet_status', 
                       'today_summary', 'state_tags']:
                if existing.get(key) and key not in data:
                    data[key] = existing[key]
        
        log_id = self.health.save_daily_log(data)
        
        return {
            'success': True,
            'log_id': log_id,
            'date': date,
            'message': f'已记录 {date} 疲劳度 {score}'
        }
    
    def record_training(self, brief: str, had_training: bool = True,
                        date: Optional[str] = None) -> Dict[str, Any]:
        """记录训练"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        existing = self.health.get_daily_log(date)
        
        data = {
            'date': date,
            'had_training': had_training,
            'training_brief': brief,
        }
        
        # 合并现有数据
        if existing:
            for key in ['sleep_hours', 'sleep_quality', 'fatigue_score', 'energy_score',
                       'weight_kg', 'diet_status', 'body_status_notes', 
                       'today_summary', 'state_tags']:
                if existing.get(key) and key not in data:
                    data[key] = existing[key]
        
        log_id = self.health.save_daily_log(data)
        
        return {
            'success': True,
            'log_id': log_id,
            'date': date,
            'message': f'已记录 {date} 训练：{brief}'
        }
    
    def get_today_summary(self) -> Dict[str, Any]:
        """获取今日概览"""
        today = datetime.now().strftime("%Y-%m-%d")
        log = self.health.get_daily_log(today)
        
        if not log:
            return {
                'has_data': False,
                'date': today,
                'message': '今日暂无记录'
            }
        
        return {
            'has_data': True,
            'date': today,
            'sleep_hours': log.get('sleep_hours'),
            'sleep_quality': log.get('sleep_quality'),
            'fatigue_score': log.get('fatigue_score'),
            'had_training': log.get('had_training'),
            'training_brief': log.get('training_brief'),
            'body_status_notes': log.get('body_status_notes')
        }


def get_service(profile_id: str) -> LifeOSService:
    """获取 LifeOS 服务实例"""
    return LifeOSService(profile_id)
