#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人偏好服务 - 用户生活偏好数据的 CRUD 操作

提供统一的接口供对话层调用，屏蔽底层实现细节。
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from db import query_one, query_many, insert, update, execute


class PreferenceService:
    """个人偏好服务类"""
    
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
    
    def get_preferences(self) -> Optional[Dict[str, Any]]:
        """获取用户的偏好记录"""
        return query_one(
            "SELECT * FROM user_preferences WHERE profile_id = ?",
            (self.profile_id,)
        )
    
    def get_preferences_with_defaults(self) -> Dict[str, Any]:
        """获取偏好记录，不存在则返回默认空结构"""
        prefs = self.get_preferences()
        if prefs:
            return prefs
        
        # 返回默认空结构
        return {
            'profile_id': self.profile_id,
            'sports_likes': '',
            'sports_dislikes': '',
            'food_likes': '',
            'food_dislikes': '',
            'cuisine_likes': '',
            'nutrition_preferences': '',
            'lifestyle_constraints': '',
            'execution_preferences': '',
            'notes': '',
            'source': '',
            'confidence': '',
        }
    
    def save_preferences(self, data: Dict[str, Any]) -> bool:
        """
        保存偏好数据（插入或更新）
        
        Args:
            data: 偏好数据，包含以下可选字段:
                - sports_likes: 喜欢的运动
                - sports_dislikes: 不喜欢的运动
                - food_likes: 喜欢的食物
                - food_dislikes: 不喜欢的食物
                - cuisine_likes: 喜欢的菜系
                - nutrition_preferences: 营养方案偏好
                - execution_preferences: 执行偏好
                - notes: 备注
                - source: 来源 (dialogue_extract/guided_answer/manual)
                - confidence: 置信度 (high/medium/low)
        
        Returns:
            是否成功
        """
        existing = self.get_preferences()
        
        data['profile_id'] = self.profile_id
        data['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if existing:
            # 更新现有记录
            where_clause = "profile_id = ?"
            where_params = (self.profile_id,)
            update("user_preferences", data, where_clause, where_params)
            return True
        else:
            # 新增记录
            data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            insert("user_preferences", data)
            return True
    
    def update_single_field(self, field: str, value: str, 
                           source: str = "dialogue_extract",
                           confidence: str = "medium",
                           append_notes: Optional[str] = None) -> bool:
        """
        更新单个偏好字段
        
        Args:
            field: 字段名 (如 sports_likes, food_likes 等)
            value: 字段值
            source: 来源
            confidence: 置信度
            append_notes: 可选，要追加到 notes 的说明
        
        Returns:
            是否成功
        """
        allowed_fields = [
            'sports_likes', 'sports_dislikes',
            'food_likes', 'food_dislikes',
            'cuisine_likes', 'nutrition_preferences',
            'lifestyle_constraints', 'execution_preferences', 'notes'
        ]
        
        if field not in allowed_fields:
            return False
        
        existing = self.get_preferences()
        
        if existing:
            # 检查是否需要记录变更历史
            old_value = existing.get(field, '')
            notes = existing.get('notes', '') or ''
            
            if old_value and old_value != value:
                # 存在旧值且不同，记录变更
                change_record = f"[{datetime.now().strftime('%Y-%m-%d')}] {field}: {old_value} -> {value}"
                notes = f"{notes}\n{change_record}" if notes else change_record
            
            if append_notes:
                notes = f"{notes}\n{append_notes}" if notes else append_notes
            
            data = {
                field: value,
                'source': source,
                'confidence': confidence,
                'notes': notes,
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            update("user_preferences", data, "profile_id = ?", (self.profile_id,))
        else:
            # 新建记录
            data = {
                'profile_id': self.profile_id,
                field: value,
                'source': source,
                'confidence': confidence,
                'notes': append_notes or '',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            insert("user_preferences", data)
        
        return True
    
    def has_minimal_preferences(self) -> bool:
        """
        检查是否有最低限度的偏好信息
        
        至少有一个偏好字段有值则返回 True
        """
        prefs = self.get_preferences_with_defaults()
        
        preference_fields = [
            'sports_likes', 'sports_dislikes',
            'food_likes', 'food_dislikes',
            'cuisine_likes', 'nutrition_preferences',
            'lifestyle_constraints', 'execution_preferences'
        ]
        
        for field in preference_fields:
            if prefs.get(field):
                return True
        
        return False
    
    def is_preference_complete_for(self, pref_type: str) -> bool:
        """
        检查特定类型的偏好信息是否足够
        
        Args:
            pref_type: 'sports' | 'diet' | 'nutrition'
        
        Returns:
            偏好信息是否足够
        """
        prefs = self.get_preferences_with_defaults()
        
        if pref_type == 'sports':
            return bool(prefs.get('sports_likes') or prefs.get('sports_dislikes'))
        elif pref_type == 'diet':
            return bool(prefs.get('food_likes') or prefs.get('food_dislikes') 
                       or prefs.get('cuisine_likes'))
        elif pref_type == 'nutrition':
            return bool(prefs.get('nutrition_preferences'))
        
        return False


def get_preference_service(profile_id: str) -> PreferenceService:
    """获取 PreferenceService 实例"""
    return PreferenceService(profile_id)


def extract_preferences_from_text(text: str) -> Dict[str, Any]:
    """
    从用户文本中提取偏好信息
    
    Args:
        text: 用户输入文本
    
    Returns:
        提取到的偏好字典，包含匹配到的字段和原始文本
    """
    results = {
        'matched': False,
        'preferences': {},
        'original_text': text
    }
    
    text_lower = text.lower()
    
    # 运动偏好提取
    sports_patterns = {
        'sports_likes': [
            '喜欢散步', '喜欢跑步', '喜欢游泳', '喜欢骑车', '喜欢打球',
            '喜欢瑜伽', '喜欢爬山', '喜欢力量训练', '喜欢健身', '喜欢打球',
            '喜欢体操', '喜欢跳舞', '喜欢太极', '喜欢广场舞',
            '喜欢打篮球', '喜欢篮球', '喜欢足球', '喜欢羽毛球', '喜欢乒乓球',
            '倾向散步', '倾向跑步', '倾向游泳', '倾向打球'
        ],
        'sports_dislikes': [
            '不喜欢跑步', '不喜欢游泳', '不喜欢打球', '不喜欢剧烈运动',
            '不喜欢力量训练', '排斥跑步', '排斥游泳',
            '不喜欢篮球', '不喜欢足球', '不喜欢羽毛球'
        ],
        'cuisine_likes': [
            '喜欢粤菜', '喜欢川菜', '喜欢湘菜', '喜欢鲁菜', '喜欢浙菜',
            '喜欢闽菜', '喜欢苏菜', '喜欢徽菜', '喜欢本帮菜', '喜欢家常菜',
            '喜欢清淡', '喜欢重口味', '喜欢火锅', '喜欢烧烤', '喜欢日料',
            '喜欢韩餐', '喜欢西餐', '喜欢意大利菜', '喜欢法国菜',
            '倾向粤菜', '倾向清淡', '倾向地中海饮食'
        ],
        'nutrition_preferences': [
            '地中海饮食', '生酮饮食', '低糖饮食', '高蛋白饮食',
            '得舒饮食', '轻断食', '弹性素食', '全素食',
            '倾向地中海', '倾向低糖', '倾向高蛋白'
        ]
    }
    
    for field, patterns in sports_patterns.items():
        for pattern in patterns:
            if pattern in text_lower:
                # 提取关键词
                keyword = pattern.replace('喜欢', '').replace('倾向', '').replace('不喜欢', '不爱')
                results['preferences'][field] = keyword
                results['matched'] = True
                break
    
    # 执行偏好提取
    execution_patterns = {
        'execution_preferences': [
            '早起锻炼', '晚间锻炼', '周末集中锻炼', '碎片化运动',
            '喜欢早起', '习惯晚睡', '早起困难', '晚上更有精力'
        ]
    }

    # 生活约束提取
    lifestyle_patterns = {
        'lifestyle_constraints': [
            '不抽烟', '不吸烟', '戒烟',
            '不喝酒', '不饮酒', '戒酒',
            '不熬夜', '早睡早起', '作息规律',
            '不喝咖啡', '少油少盐', '少糖'
        ]
    }
    
    for field, patterns in lifestyle_patterns.items():
        for pattern in patterns:
            if pattern in text_lower:
                keyword = pattern
                results['preferences'][field] = keyword
                results['matched'] = True
                break
    
    for field, patterns in execution_patterns.items():
        for pattern in patterns:
            if pattern in text_lower:
                keyword = pattern
                results['preferences'][field] = keyword
                results['matched'] = True
                break
    
    return results


# ========== 引导提问模板 ==========

GUIDANCE_QUESTIONS = {
    'sports': {
        'trigger': 'sports',
        'question': '你平时更喜欢什么运动方式？比如散步、游泳、力量训练、瑜伽等',
        'fields': ['sports_likes', 'sports_dislikes']
    },
    'diet': {
        'trigger': 'diet',
        'question': '你更喜欢哪类菜系？清淡家常、粤菜、川菜、日式还是别的？',
        'fields': ['cuisine_likes', 'food_likes']
    },
    'nutrition': {
        'trigger': 'nutrition',
        'question': '你有没有偏好的营养方案？比如地中海饮食、高蛋白、控糖、低脂等',
        'fields': ['nutrition_preferences']
    }
}


def get_guidance_question(pref_type: str) -> Optional[str]:
    """
    获取指定类型的引导问题
    
    Args:
        pref_type: 'sports' | 'diet' | 'nutrition'
    
    Returns:
        引导问题文本，如果不需要则返回 None
    """
    template = GUIDANCE_QUESTIONS.get(pref_type)
    if template:
        return template['question']
    return None


# ========== 集成到周计划/建议的上下文构建 ==========

def build_preference_context(profile_id: str) -> str:
    """
    构建偏好上下文字符串，供周计划/建议生成时注入
    
    Args:
        profile_id: 用户 ID
    
    Returns:
        偏好上下文描述字符串
    """
    svc = get_preference_service(profile_id)
    prefs = svc.get_preferences_with_defaults()
    
    lines = []
    lines.append("【用户偏好信息】")
    
    if prefs.get('sports_likes'):
        lines.append(f"- 喜欢的运动: {prefs['sports_likes']}")
    if prefs.get('sports_dislikes'):
        lines.append(f"- 不喜欢的运动: {prefs['sports_dislikes']}")
    if prefs.get('cuisine_likes'):
        lines.append(f"- 喜欢的菜系: {prefs['cuisine_likes']}")
    if prefs.get('food_likes'):
        lines.append(f"- 喜欢的食物: {prefs['food_likes']}")
    if prefs.get('food_dislikes'):
        lines.append(f"- 不喜欢的食物: {prefs['food_dislikes']}")
    if prefs.get('nutrition_preferences'):
        lines.append(f"- 营养偏好: {prefs['nutrition_preferences']}")
    if prefs.get('lifestyle_constraints'):
        lines.append(f"- 生活约束: {prefs['lifestyle_constraints']}")
    if prefs.get('execution_preferences'):
        lines.append(f"- 执行偏好: {prefs['execution_preferences']}")
    if prefs.get('notes'):
        lines.append(f"- 备注: {prefs['notes']}")
    
    if len(lines) == 1:
        return ""
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    print("=== PreferenceService Test ===")
    
    # 测试提取
    test_texts = [
        "我喜欢散步，不喜欢跑步",
        "我比较喜欢粤菜，倾向清淡饮食",
        "我现在倾向地中海饮食方式",
        "家里老人适合清淡一点",
        "今天想吃火锅",
        "今晚吃清淡点"
    ]
    
    print("\n--- 提取测试 ---")
    for text in test_texts:
        result = extract_preferences_from_text(text)
        print(f"输入: {text}")
        print(f"提取: {result}")
        print()
    
    # 测试服务
    print("\n--- 服务测试 (profile_id=001) ---")
    svc = get_preference_service("001")
    prefs = svc.get_preferences_with_defaults()
    print(f"当前偏好: {prefs}")
    print(f"是否有最低偏好: {svc.has_minimal_preferences()}")
