# -*- coding: utf-8 -*-
"""查询引擎 - 支持自然语言查询和基础统计"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db import get_connection


class QueryEngine:
    """查询引擎"""
    
    # 支持的指标类型
    METRIC_TYPES = [
        "steps", "active_calories", "moderate_vigorous_minutes",
        "activity_sessions", "sleep_duration_minutes",
        "heart_rate", "weight_kg", "blood_glucose",
        "blood_pressure_systolic", "blood_pressure_diastolic"
    ]
    
    # 中文指标映射
    METRIC_CN_MAP = {
        "步数": "steps",
        "步": "steps",
        "卡路里": "active_calories",
        "热量": "active_calories",
        "中高强度": "moderate_vigorous_minutes",
        "活动次数": "active_calories",
        "睡眠": "sleep_duration_minutes",
        "心率": "heart_rate",
        "体重": "weight_kg",
        "血糖": "blood_glucose",
        "血压": "blood_pressure_systolic",
        "收缩压": "blood_pressure_systolic",
        "舒张压": "blood_pressure_diastolic",
    }
    
    @classmethod
    def parse_query(cls, query_text: str) -> Dict[str, Any]:
        """
        解析自然语言查询
        
        Args:
            query_text: 查询文本，如"查看最近7天步数"
            
        Returns:
            {
                "metric_type": str,
                "time_range": int,  # 天数
                "parsed": bool
            }
        """
        query = query_text.strip()
        
        # 解析时间范围
        time_range = 7  # 默认7天
        days_match = re.search(r"(\d+)\s*天", query)
        if days_match:
            time_range = int(days_match.group(1))
        
        # 解析指标类型
        metric_type = None
        
        # 首先检查是否是全量查询（总结类）
        if "总结" in query or "汇总" in query or "健康数据" in query:
            metric_type = "recent_summary"
        
        # 然后检查具体指标
        if not metric_type:
            for cn, en in cls.METRIC_CN_MAP.items():
                if cn in query:
                    metric_type = en
                    break
        
        if not metric_type:
            # 尝试直接匹配
            for mt in cls.METRIC_TYPES:
                if mt in query.lower():
                    metric_type = mt
                    break
        
        return {
            "metric_type": metric_type,
            "time_range": time_range,
            "parsed": metric_type is not None
        }
    
    @classmethod
    def query(cls, profile_id: str, metric_type: str, time_range: int = 7) -> Dict[str, Any]:
        """
        查询健康数据
        
        Args:
            profile_id: 用户 profile_id
            metric_type: 指标类型
            time_range: 时间范围（天）
            
        Returns:
            {
                "records": [...],
                "count": int,
                "stats": {
                    "latest": float,
                    "first": float,
                    "change": float,
                    "min": float,
                    "max": float
                }
            }
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=time_range)).strftime("%Y-%m-%d")
        
        sql = """
            SELECT * FROM health_data_logs
            WHERE profile_id = ?
            AND metric_type = ?
            AND date >= ?
            AND date <= ?
            AND is_valid = 1
            ORDER BY date DESC
        """
        
        records = []
        values = []
        
        try:
            with get_connection() as conn:
                rows = conn.execute(sql, (profile_id, metric_type, start_date, end_date)).fetchall()
                for row in rows:
                    r = dict(row)
                    records.append(r)
                    if r.get("value") is not None:
                        values.append(float(r["value"]))
        except Exception as e:
            return {
                "records": [],
                "count": 0,
                "stats": None,
                "error": str(e)
            }
        
        # 计算统计
        stats = None
        if values:
            stats = {
                "latest": values[0] if values else None,
                "first": values[-1] if values else None,
                "change": round(values[0] - values[-1], 2) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values)
            }
        
        return {
            "records": records,
            "count": len(records),
            "stats": stats
        }
    
    @classmethod
    def query_recent(cls, profile_id: str, days: int = 7) -> Dict[str, Any]:
        """
        查询最近多天的所有健康数据
        
        Args:
            profile_id: 用户 profile_id
            days: 天数
            
        Returns:
            {
                "records": [...],
                "count": int,
                "by_metric": {...}  # 按指标类型分组
            }
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        sql = """
            SELECT * FROM health_data_logs
            WHERE profile_id = ?
            AND date >= ?
            AND date <= ?
            AND is_valid = 1
            ORDER BY date DESC, metric_type
        """
        
        records = []
        by_metric = {}
        
        try:
            with get_connection() as conn:
                rows = conn.execute(sql, (profile_id, start_date, end_date)).fetchall()
                for row in rows:
                    r = dict(row)
                    records.append(r)
                    
                    mt = r.get("metric_type")
                    if mt not in by_metric:
                        by_metric[mt] = []
                    by_metric[mt].append(r)
        except Exception as e:
            return {
                "records": [],
                "count": 0,
                "by_metric": {},
                "error": str(e)
            }
        
        return {
            "records": records,
            "count": len(records),
            "by_metric": by_metric
        }
