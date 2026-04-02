# -*- coding: utf-8 -*-
"""去重器 - 基于多字段判断重复记录"""

import sqlite3
from typing import List, Dict, Any, Set
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db import get_connection, get_db_path


class Deduplicator:
    """去重器"""
    
    # 去重判定字段
    DEDUP_FIELDS = [
        "user_id",
        "metric_type", 
        "value",
        "date",
        "source_app"
    ]
    
    @classmethod
    def filter_duplicates(cls, profile_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        过滤重复记录
        
        Args:
            profile_id: 用户 profile_id
            records: 待检查的记录列表
            
        Returns:
            {
                "new_records": [...],     # 新记录（不重复）
                "duplicate_records": [...], # 重复记录（含 reason 字段）
                "new_count": int,
                "duplicate_count": int
            }
        """
        if not records:
            return {
                "new_records": [],
                "duplicate_records": [],
                "new_count": 0,
                "duplicate_count": 0
            }
        
        # 查询已存在的记录
        existing = cls._query_existing(profile_id, records)
        
        new_records = []
        duplicate_records = []
        
        for r in records:
            if cls._is_duplicate(r, existing):
                r["dedup_reason"] = "与已存在记录重复"
                duplicate_records.append(r)
            else:
                new_records.append(r)
        
        return {
            "new_records": new_records,
            "duplicate_records": duplicate_records,
            "new_count": len(new_records),
            "duplicate_count": len(duplicate_records)
        }
    
    @classmethod
    def _query_existing(cls, profile_id: str, records: List[Dict[str, Any]]) -> Set[str]:
        """
        查询已存在的记录，返回去重 key 集合
        
        Returns:
            Set of "metric_type|value|date|extra_key" 字符串
        """
        existing_keys = set()
        
        if not records:
            return existing_keys
        
        # 收集所有需要的 date 和 metric_type
        dates = list(set(r.get("date") for r in records if r.get("date")))
        metric_types = list(set(r.get("metric_type") for r in records if r.get("metric_type")))
        
        if not dates or not metric_types:
            return existing_keys
        
        placeholders = ",".join(["?" for _ in dates])
        
        sql = f"""
            SELECT metric_type, value, date, image_hash
            FROM health_data_logs
            WHERE profile_id = ?
            AND date IN ({placeholders})
            AND metric_type IN ({"," .join(["?" for _ in metric_types])})
            AND is_valid = 1
        """
        
        params = [profile_id] + dates + metric_types
        
        try:
            with get_connection() as conn:
                rows = conn.execute(sql, params).fetchall()
                for row in rows:
                    key = cls._make_key({
                        "metric_type": row["metric_type"],
                        "value": row["value"],
                        "date": row["date"],
                        "image_hash": row["image_hash"]
                    })
                    existing_keys.add(key)
        except Exception as e:
            print(f"Query existing error: {e}")
        
        return existing_keys
    
    @classmethod
    def _is_duplicate(cls, record: Dict[str, Any], existing_keys: Set[str]) -> bool:
        """检查记录是否重复"""
        key = cls._make_key(record)
        return key in existing_keys
    
    @classmethod
    def _make_key(cls, record: Dict[str, Any]) -> str:
        """生成去重 key"""
        metric_type = record.get("metric_type", "")
        value = record.get("value", "")
        date = record.get("date", "")
        image_hash = record.get("image_hash", "") or ""
        
        return f"{metric_type}|{value}|{date}|{image_hash}"
