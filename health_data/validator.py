# -*- coding: utf-8 -*-
"""数据校验器 - 验证数据合法性"""

from typing import Dict, Any, List, Tuple


class Validator:
    """数据校验器"""
    
    # 各指标的有效范围
    VALID_RANGES = {
        "heart_rate": (30, 220),           # 心率
        "blood_glucose": (1.0, 40),        # 血糖
        "weight_kg": (20, 300),            # 体重
        "blood_pressure_systolic": (60, 260),  # 收缩压
        "blood_pressure_diastolic": (30, 180),  # 舒张压
    }
    
    @classmethod
    def validate_record(cls, record: Dict[str, Any]) -> Tuple[bool, str]:
        """
        校验单条记录
        
        Args:
            record: 记录数据
            
        Returns:
            (is_valid, error_message)
        """
        metric_type = record.get("metric_type")
        value = record.get("value")
        
        if not metric_type:
            return False, "缺少 metric_type"
        
        if value is None:
            return False, f"{metric_type} 缺少数值"
        
        # 检查是否有有效范围定义
        if metric_type in cls.VALID_RANGES:
            min_val, max_val = cls.VALID_RANGES[metric_type]
            if not (min_val <= float(value) <= max_val):
                return False, f"{metric_type} 数值 {value} 超出有效范围 [{min_val}, {max_val}]"
        
        # 血压特殊校验：收缩压 > 舒张压
        if metric_type == "blood_pressure_systolic":
            diastolic = record.get("_diastolic_value")
            if diastolic is not None:
                if float(value) <= float(diastolic):
                    return False, f"收缩压({value}) 必须大于 舒张压({diastolic})"
        
        # 日期校验
        if not record.get("date"):
            return False, "缺少日期"
        
        return True, ""
    
    @classmethod
    def validate_batch(cls, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量校验记录
        
        Args:
            records: 记录列表
            
        Returns:
            {
                "valid_records": [...],      # 合法的记录
                "invalid_records": [...],    # 非法的记录（含 error 字段）
                "valid_count": int,
                "invalid_count": int
            }
        """
        valid_records = []
        invalid_records = []
        
        # 预先处理血压配对
        bp_records = {}
        other_records = []
        
        for r in records:
            if r.get("metric_type") in ("blood_pressure_systolic", "blood_pressure_diastolic"):
                date = r.get("date")
                if date not in bp_records:
                    bp_records[date] = {}
                bp_records[date][r.get("metric_type")] = r
            else:
                other_records.append(r)
        
        # 处理血压配对校验
        for date, bp_pair in bp_records.items():
            systolic = bp_pair.get("blood_pressure_systolic")
            diastolic = bp_pair.get("blood_pressure_diastolic")
            
            if systolic and diastolic:
                # 两条都有，先校验范围
                systolic_val = float(systolic.get("value"))
                diastolic_val = float(diastolic.get("value"))
                
                # 添加配对信息用于交叉校验
                systolic["_diastolic_value"] = diastolic_val
                diastolic["_systolic_value"] = systolic_val
                
                # 收缩压 > 舒张压校验
                if systolic_val <= diastolic_val:
                    systolic["is_valid"] = False
                    systolic["validation_notes"] = f"收缩压({systolic_val})必须大于舒张压({diastolic_val})"
                    invalid_records.append(systolic)
                    diastolic["is_valid"] = False
                    diastolic["validation_notes"] = f"舒张压({diastolic_val})必须小于收缩压({systolic_val})"
                    invalid_records.append(diastolic)
                    continue
                
                # 分别校验范围
                for r in [systolic, diastolic]:
                    valid, err = cls.validate_record(r)
                    if valid:
                        valid_records.append(r)
                    else:
                        r["is_valid"] = False
                        r["validation_notes"] = err
                        invalid_records.append(r)
            elif systolic and not diastolic:
                # 只有收缩压，无法校验配对，但记录（血压模块但无数值的情况）
                systolic["is_valid"] = False
                systolic["validation_notes"] = "检测到血压模块，但未识别到有效舒张压数值"
                invalid_records.append(systolic)
            elif diastolic and not systolic:
                diastolic["is_valid"] = False
                diastolic["validation_notes"] = "检测到血压模块，但未识别到有效收缩压数值"
                invalid_records.append(diastolic)
        
        # 处理其他记录
        for r in other_records:
            valid, err = cls.validate_record(r)
            if valid:
                valid_records.append(r)
            else:
                r["is_valid"] = False
                r["validation_notes"] = err
                invalid_records.append(r)
        
        return {
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "valid_count": len(valid_records),
            "invalid_count": len(invalid_records)
        }
