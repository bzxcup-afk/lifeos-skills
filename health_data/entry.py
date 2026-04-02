# -*- coding: utf-8 -*-
"""健康数据模块便捷入口 - 供对话层调用"""

from typing import Dict, Any, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db import query_one


def get_health_data_service(profile_id: str, user_id: str):
    """
    获取健康数据服务实例
    
    Args:
        profile_id: 用户 profile_id (如 "001")
        user_id: 用户 sender_id (飞书 open_id)
        
    Returns:
        HealthDataService 实例
    """
    from .service import HealthDataService
    return HealthDataService(profile_id, user_id)


def check_trigger_and_tip(text: str, has_image: bool = False) -> Dict[str, Any]:
    """
    检查是否应触发健康数据导入，返回提示
    
    Args:
        text: 消息文本
        has_image: 是否包含图片
        
    Returns:
        {
            "should_activate": bool,
            "tip": str (如果缺图片，返回提示)
        }
    """
    from .trigger_router import TriggerRouter
    
    result = TriggerRouter.should_activate(text, has_image)
    
    if result["should_activate"]:
        return {"should_activate": True, "tip": None}
    
    if not has_image and result.get("matched_pattern"):
        return {
            "should_activate": False,
            "tip": result.get("missing_image_tip", "请附上小米健康截图")
        }
    
    return {"should_activate": False, "tip": None}


def import_from_screenshot(profile_id: str, user_id: str, 
                          image_path: str, llm_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    从截图导入健康数据（供对话层调用）
    
    Args:
        profile_id: 用户 profile_id
        user_id: 用户 sender_id
        image_path: 图片本地路径
        llm_json: LLM 识图返回的 JSON
        
    Returns:
        {
            "success": bool,
            "reply_message": str
        }
    """
    svc = get_health_data_service(profile_id, user_id)
    result = svc.import_from_llm_result(image_path, llm_json)
    return {
        "success": result["success"],
        "reply_message": result.get("reply_message", "")
    }


def query_health_data(profile_id: str, query_text: str) -> Dict[str, Any]:
    """
    查询健康数据（供对话层调用）
    
    Args:
        profile_id: 用户 profile_id
        query_text: 查询文本，如"查看最近7天步数"
        
    Returns:
        {
            "success": bool,
            "query_type": str,
            "query_params": dict,
            "records": list,
            "stats": dict,
            "formatted_data": str (供LLM使用的格式化数据),
            "prompt": str (LLM总结prompt)
        }
    """
    from .service import HealthDataService
    from .query_engine import QueryEngine
    
    svc = HealthDataService(profile_id, profile_id)  # user_id 在这里不太重要
    
    # 解析查询
    parsed = QueryEngine.parse_query(query_text)
    
    if not parsed["parsed"]:
        return {
            "success": False,
            "error": "无法解析查询，请明确指标类型（步数、心率、体重、血糖、血压、睡眠）"
        }
    
    # 执行查询
    if parsed["metric_type"] == "recent_summary":
        query_result = QueryEngine.query_recent(profile_id, parsed["time_range"])
        query_type = "recent_summary"
        query_params = {"days": parsed["time_range"]}
    else:
        query_result = QueryEngine.query(profile_id, parsed["metric_type"], parsed["time_range"])
        query_type = "single_metric"
        query_params = {
            "metric_type": parsed["metric_type"],
            "days": parsed["time_range"]
        }
    
    # 格式化数据供 LLM 使用
    formatted_data = svc.format_records_for_llm(
        query_result.get("records", []),
        query_result.get("stats")
    )
    
    # 构建总结 prompt
    prompt = svc.build_summary(
        query_type,
        query_params,
        query_result.get("records", []),
        query_result.get("stats")
    )
    
    return {
        "success": True,
        "query_type": query_type,
        "query_params": query_params,
        "records": query_result.get("records", []),
        "stats": query_result.get("stats"),
        "formatted_data": formatted_data,
        "prompt": prompt,
        "record_count": query_result.get("count", 0)
    }
