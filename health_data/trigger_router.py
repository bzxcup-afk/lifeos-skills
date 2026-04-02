# -*- coding: utf-8 -*-
"""触发路由 - 判断是否应激活健康数据导入模块"""

import re
from typing import List, Dict, Any, Optional


class TriggerRouter:
    """健康数据导入触发路由"""
    
    # 触发关键词（必须同时满足：有图片）
    TRIGGER_PATTERNS = [
        r"记录健康数据",
        r"健康数据",
    ]
    
    @classmethod
    def should_activate(cls, text: str, has_image: bool = False) -> Dict[str, Any]:
        """
        判断是否应激活健康数据导入模块
        
        Args:
            text: 消息文本
            has_image: 消息是否包含图片
            
        Returns:
            {
                "should_activate": bool,
                "reason": str,
                "missing_image_tip": str  # 如果缺图片，给出提示
            }
        """
        # 检查文本是否匹配触发关键词
        matched_pattern = None
        for pattern in cls.TRIGGER_PATTERNS:
            if re.search(pattern, text):
                matched_pattern = pattern
                break
        
        if not matched_pattern:
            return {
                "should_activate": False,
                "reason": "文本不包含触发关键词",
                "matched_pattern": None
            }
        
        # 匹配到关键词，但没有图片
        if not has_image:
            return {
                "should_activate": False,
                "reason": "缺少图片",
                "matched_pattern": matched_pattern,
                "missing_image_tip": "请附上小米健康截图，我来帮你识别并记录。"
            }
        
        return {
            "should_activate": True,
            "reason": "文本匹配触发关键词且包含图片",
            "matched_pattern": matched_pattern
        }
    
    @classmethod
    def get_no_image_tip(cls) -> str:
        """获取缺图片时的提示"""
        return "请附上小米健康截图，我来帮你识别并记录。"
