# -*- coding: utf-8 -*-
"""健康数据服务 - 统一入口"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db import get_connection

from .trigger_router import TriggerRouter
from .image_parser import ImageParser, IMAGE_PARSE_PROMPT
from .metric_normalizer import MetricNormalizer
from .validator import Validator
from .deduplicator import Deduplicator
from .writer import Writer
from .query_engine import QueryEngine
from .summary_generator import SummaryGenerator


class HealthDataService:
    """健康数据服务统一入口"""
    
    def __init__(self, profile_id: str, user_id: str):
        self.profile_id = profile_id
        self.user_id = user_id
    
    # ==================== 导入流程 ====================
    
    def should_activate(self, text: str, has_image: bool = False) -> Dict[str, Any]:
        """判断是否应激活导入模块"""
        return TriggerRouter.should_activate(text, has_image)
    
    def get_no_image_tip(self) -> str:
        """获取缺图片提示"""
        return TriggerRouter.get_no_image_tip()
    
    def get_image_parse_prompt(self) -> str:
        """获取识图 prompt"""
        return IMAGE_PARSE_PROMPT
    
    def import_from_llm_result(self, image_path: str, llm_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 LLM 识图结果导入数据
        
        Args:
            image_path: 图片本地路径
            llm_json: LLM 返回的 JSON 数据
            
        Returns:
            {
                "success": bool,
                "imported_count": int,
                "skipped_count": int,
                "error_count": int,
                "reply_message": str
            }
        """
        # 1. 解析图片
        parse_result = ImageParser().parse_with_llm_result(image_path, llm_json)
        if not parse_result.get("success"):
            return {
                "success": False,
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "reply_message": f"识图失败：{parse_result.get('error')}"
            }
        
        records = parse_result.get("records", [])
        if not records:
            return {
                "success": False,
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "reply_message": "未识别到有效健康数据"
            }
        
        # 2. 标准化
        normalized = MetricNormalizer.normalize_records(records)
        
        # 3. 校验
        validation = Validator.validate_batch(normalized)
        valid_records = validation.get("valid_records", [])
        invalid_records = validation.get("invalid_records", [])
        
        # 4. 去重
        dedup = Deduplicator.filter_duplicates(self.profile_id, valid_records)
        new_records = dedup.get("new_records", [])
        duplicate_records = dedup.get("duplicate_records", [])
        
        # 5. 写入
        write_result = Writer.write_batch(self.profile_id, self.user_id, new_records)
        
        # 6. 生成回复
        reply_message = self._build_import_reply(
            imported_count=write_result.get("written_count", 0),
            duplicate_count=len(duplicate_records),
            invalid_count=len(invalid_records),
            records=new_records
        )
        
        return {
            "success": write_result.get("success", False),
            "imported_count": write_result.get("written_count", 0),
            "skipped_count": len(duplicate_records) + len(invalid_records),
            "error_count": write_result.get("failed_count", 0),
            "reply_message": reply_message
        }
    
    def _build_import_reply(self, imported_count: int, duplicate_count: int, 
                           invalid_count: int, records: List[Dict]) -> str:
        """构建导入结果回复"""
        if imported_count == 0:
            return "没有新数据需要导入"
        
        # 按指标分组
        by_metric = {}
        for r in records:
            mt = r.get("metric_type", "")
            if mt not in by_metric:
                by_metric[mt] = r
        
        lines = [f"已记录 {imported_count} 条健康数据："]
        
        METRIC_CN = {
            "steps": "步数",
            "active_calories": "卡路里",
            "sleep_duration_minutes": "睡眠",
            "heart_rate": "心率",
            "weight_kg": "体重",
            "blood_glucose": "血糖",
            "blood_pressure_systolic": "收缩压",
            "blood_pressure_diastolic": "舒张压",
        }
        
        UNIT_CN = {
            "steps": "步",
            "kcal": "千卡",
            "min": "分钟",
            "bpm": "次/分",
            "kg": "kg",
            "mmol/L": "mmol/L",
            "mmHg": "mmHg",
        }
        
        for mt, r in by_metric.items():
            cn_name = METRIC_CN.get(mt, mt)
            val = r.get("value")
            unit = r.get("unit", "")
            cn_unit = UNIT_CN.get(unit, unit)
            
            if mt == "sleep_duration_minutes":
                total_min = float(val) if val else 0
                hours = int(total_min // 60)
                mins = int(total_min % 60)
                val_str = f"{hours}小时{mins}分" if hours else f"{mins}分钟"
                lines.append(f"- {cn_name}：{val_str}")
            elif mt in ("blood_pressure_systolic", "blood_pressure_diastolic"):
                # 血压需要配对显示
                continue
            else:
                lines.append(f"- {cn_name}：{val} {cn_unit}")
        
        # 处理血压配对
        if "blood_pressure_systolic" in by_metric and "blood_pressure_diastolic" in by_metric:
            sys_val = by_metric["blood_pressure_systolic"].get("value")
            dia_val = by_metric["blood_pressure_diastolic"].get("value")
            if sys_val and dia_val:
                lines.append(f"- 血压：{int(sys_val)}/{int(dia_val)} mmHg")
        
        if duplicate_count > 0:
            lines.append(f"\n（{duplicate_count}条重复已跳过）")
        
        return "\n".join(lines)
    
    # ==================== 查询流程 ====================
    
    def parse_query(self, query_text: str) -> Dict[str, Any]:
        """解析自然语言查询"""
        return QueryEngine.parse_query(query_text)
    
    def query(self, metric_type: str, time_range: int = 7) -> Dict[str, Any]:
        """查询指定指标"""
        return QueryEngine.query(self.profile_id, metric_type, time_range)
    
    def query_recent(self, days: int = 7) -> Dict[str, Any]:
        """查询最近多天的所有数据"""
        return QueryEngine.query_recent(self.profile_id, days)
    
    def build_summary(self, query_type: str, query_params: Dict[str, Any],
                     records: List[Dict], stats: Dict = None) -> str:
        """构建总结 prompt（供 LLM 调用）"""
        return SummaryGenerator.build_summary_prompt(query_type, query_params, records, stats)
    
    def format_records_for_llm(self, records: List[Dict], stats: Dict = None) -> str:
        """格式化记录供 LLM 使用"""
        return SummaryGenerator.format_records_for_llm(records, stats)
