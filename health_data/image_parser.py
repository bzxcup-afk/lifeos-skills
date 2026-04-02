# -*- coding: utf-8 -*-
"""图片解析器 - 调用 LLM 解析小米健康截图"""

import json
import hashlib
from typing import Dict, Any, List, Optional


# LLM 识图 prompt
IMAGE_PARSE_PROMPT = """你是一个专业的小米健康APP数据识别助手。
请从截图中提取健康数据，输出结构化JSON。

支持的指标类型：
- steps: 步数
- active_calories: 卡路里
- moderate_vigorous_minutes:中高强度分钟
- activity_sessions: 活动次数
- sleep_duration_minutes: 睡眠时长（分钟）
- heart_rate: 心率
- weight_kg: 体重（公斤）
- blood_glucose: 血糖
- blood_pressure_systolic: 收缩压
- blood_pressure_diastolic: 舒张压

输出格式：
{
  "source_app": "xiaomi_health",
  "records": [
    {
      "metric_type": "steps",
      "value": 5665,
      "unit": "步",
      "date": "2026-04-02",
      "granularity": "day",
      "raw_text": "5665 /6000步"
    }
  ]
}

注意：
1. 日期格式统一为 YYYY-MM-DD
2. 睡眠时长单位转换为分钟
3. 血压如果只提到"佩戴设备"但无数值，不记录
4. 如果是单次测量，granularity 为 "instant"
5. 日汇总类 granularity 为 "day"
6. 只提取确切数值，模糊描述不记录
"""


class ImageParser:
    """图片解析器 - 调用 LLM 解析截图"""
    
    def __init__(self):
        self.prompt = IMAGE_PARSE_PROMPT
    
    def parse(self, image_path: str) -> Dict[str, Any]:
        """
        解析小米健康截图
        
        Args:
            image_path: 图片本地路径
            
        Returns:
            {
                "success": bool,
                "source_app": "xiaomi_health",
                "records": [...],
                "image_hash": str,
                "error": str (如果失败)
            }
        """
        try:
            # 计算图片 hash
            image_hash = self._compute_hash(image_path)
            
            # TODO: 调用 LLM 解析图片
            # 目前先用占位逻辑，后续接入 LLM
            raise NotImplementedError("需要接入 LLM 解析能力")
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source_app": "xiaomi_health",
                "records": [],
                "image_hash": None
            }
    
    def parse_with_llm_result(self, image_path: str, llm_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        接收 LLM 返回的 JSON 结果，标准化处理
        
        Args:
            image_path: 图片路径
            llm_json: LLM 返回的结构化数据
            
        Returns:
            标准化后的记录列表
        """
        image_hash = self._compute_hash(image_path)
        
        records = []
        for r in llm_json.get("records", []):
            records.append({
                "metric_type": r.get("metric_type"),
                "value": r.get("value"),
                "unit": r.get("unit"),
                "date": r.get("date"),
                "granularity": r.get("granularity", "instant"),
                "raw_text": r.get("raw_text", ""),
                "source_app": llm_json.get("source_app", "xiaomi_health"),
                "image_hash": image_hash
            })
        
        return {
            "success": True,
            "source_app": llm_json.get("source_app", "xiaomi_health"),
            "records": records,
            "image_hash": image_hash
        }
    
    @staticmethod
    def _compute_hash(image_path: str) -> str:
        """计算图片 MD5 hash"""
        import hashlib
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
