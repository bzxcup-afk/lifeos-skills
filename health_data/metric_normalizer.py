# -*- coding: utf-8 -*-
"""指标标准化 - 将识图结果标准化为统一格式"""

from typing import Dict, Any, List, Optional


class MetricNormalizer:
    """指标标准化"""
    
    # 中文 metric_type 到英文的映射
    METRIC_TYPE_MAP = {
        "步数": "steps",
        "步": "steps",
        "卡路里": "active_calories",
        "热量": "active_calories",
        "中高强度": "moderate_vigorous_minutes",
        "活动次数": "activity_sessions",
        "睡眠时长": "sleep_duration_minutes",
        "睡眠": "sleep_duration_minutes",
        "心率": "heart_rate",
        "体重": "weight_kg",
        "血糖": "blood_glucose",
        "收缩压": "blood_pressure_systolic",
        "舒张压": "blood_pressure_diastolic",
        "血压": "blood_pressure_systolic",  # 血压默认拆分为收缩压/舒张压
    }
    
    # 单位标准化映射
    UNIT_MAP = {
        "步": "steps",
        "步/天": "steps",
        "千卡": "kcal",
        "千卡/天": "kcal",
        "分钟": "min",
        "分": "min",
        "次": "times",
        "次/天": "times",
        "bpm": "bpm",
        "次/分": "bpm",
        "kg": "kg",
        "公斤": "kg",
        "斤": "jin",
        "mmol/L": "mmol/L",
        "mmol/l": "mmol/L",
        "mmHg": "mmHg",
        "mmhg": "mmHg",
    }
    
    @classmethod
    def normalize_records(cls, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        标准化记录列表
        
        Args:
            records: 原始记录列表
            
        Returns:
            标准化后的记录列表
        """
        normalized = []
        
        for r in records:
            metric_type = r.get("metric_type", "")
            normalized_type = cls._normalize_metric_type(metric_type)
            
            if not normalized_type:
                continue
            
            # 标准化单位
            unit = cls._normalize_unit(r.get("unit", ""))
            
            # 标准化日期
            date = cls._normalize_date(r.get("date", ""))
            
            # 睡眠时长转换（小时转分钟）
            value = r.get("value")
            if normalized_type == "sleep_duration_minutes" and unit in ["h", "小时"]:
                value = float(value) * 60 if value else 0
                unit = "min"
            
            # 处理血压 - 拆分为两条记录
            if normalized_type == "blood_pressure_systolic":
                # 需要从 raw_text 中解析舒张压
                bp_parts = cls._parse_blood_pressure(r.get("raw_text", ""))
                if bp_parts:
                    normalized.append({
                        "metric_type": "blood_pressure_systolic",
                        "value": bp_parts["systolic"],
                        "unit": "mmHg",
                        "date": date,
                        "granularity": r.get("granularity", "instant"),
                        "raw_text": r.get("raw_text", ""),
                        "source_app": r.get("source_app", "xiaomi_health"),
                        "image_hash": r.get("image_hash")
                    })
                    normalized.append({
                        "metric_type": "blood_pressure_diastolic",
                        "value": bp_parts["diastolic"],
                        "unit": "mmHg",
                        "date": date,
                        "granularity": r.get("granularity", "instant"),
                        "raw_text": r.get("raw_text", ""),
                        "source_app": r.get("source_app", "xiaomi_health"),
                        "image_hash": r.get("image_hash")
                    })
                # 如果无法拆分，不添加任何记录
            else:
                normalized.append({
                    "metric_type": normalized_type,
                    "value": value,
                    "unit": unit,
                    "date": date,
                    "granularity": r.get("granularity", "instant"),
                    "raw_text": r.get("raw_text", ""),
                    "source_app": r.get("source_app", "xiaomi_health"),
                    "image_hash": r.get("image_hash")
                })
        
        return normalized
    
    @classmethod
    def _normalize_metric_type(cls, metric_type: str) -> Optional[str]:
        """标准化指标类型"""
        if not metric_type:
            return None
        return cls.METRIC_TYPE_MAP.get(metric_type)
    
    @classmethod
    def _normalize_unit(cls, unit: str) -> str:
        """标准化单位"""
        if not unit:
            return ""
        return cls.UNIT_MAP.get(unit, unit)
    
    @classmethod
    def _normalize_date(cls, date_str: str) -> str:
        """标准化日期格式为 YYYY-MM-DD"""
        if not date_str:
            return ""
        # 简单处理，假设输入已经是 YYYY-MM-DD 格式
        return date_str.strip()
    
    @classmethod
    def _parse_blood_pressure(cls, raw_text: str) -> Optional[Dict[str, float]]:
        """
        从 raw_text 解析血压数值
        格式如：128/84 mmHg 或 118/68
        """
        import re
        
        # 匹配 X/Y mmHg 格式
        match = re.search(r"(\d+)\s*/\s*(\d+)", raw_text)
        if match:
            return {
                "systolic": float(match.group(1)),
                "diastolic": float(match.group(2))
            }
        return None
