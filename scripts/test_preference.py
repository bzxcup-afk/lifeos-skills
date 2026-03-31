#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""个人偏好模块测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from preference_service import (
    get_preference_service,
    extract_preferences_from_text,
    build_preference_context,
    get_guidance_question
)


def test_extraction():
    """测试偏好提取"""
    print("=== 提取测试 ===\n")
    
    test_cases = [
        # 明确表达偏好 -> 应该提取
        ("我喜欢散步，不喜欢跑步", ["sports_likes"], ["sports_dislikes"]),
        ("我比较喜欢粤菜", ["cuisine_likes"], []),
        ("我现在倾向地中海饮食", ["nutrition_preferences"], []),
        ("家里老人适合清淡一点", ["cuisine_likes"], []),
        ("倾向高蛋白饮食", ["nutrition_preferences"], []),
        
        # 临时性表达 -> 不应提取
        ("今天想吃火锅", [], []),
        ("今晚吃清淡点", [], []),
        ("明天去跑步", [], []),
        ("最近胖了", [], []),
    ]
    
    for text, expected_likes, expected_dislikes in test_cases:
        result = extract_preferences_from_text(text)
        prefs = result['preferences']
        
        print(f"输入: {text}")
        print(f"提取结果: {prefs if prefs else '无匹配'}")
        
        # 简单验证
        for field in expected_likes:
            if field not in prefs:
                print(f"  [WARNING] 期望提取 {field} 但未提取")
        
        for field in expected_dislikes:
            if field not in prefs:
                print(f"  [WARNING] 期望提取 {field} 但未提取")
        
        print()


def test_service():
    """测试偏好服务"""
    print("=== 服务测试 ===\n")
    
    profile_id = "001"
    svc = get_preference_service(profile_id)
    
    # 1. 获取空偏好
    print(f"1. 获取 profile_id={profile_id} 的偏好:")
    prefs = svc.get_preferences_with_defaults()
    print(f"   {prefs}")
    print(f"   是否有最低偏好: {svc.has_minimal_preferences()}")
    print()
    
    # 2. 写入一条偏好
    print("2. 写入喜欢的运动: 散步, 游泳")
    svc.update_single_field(
        'sports_likes', 
        '散步, 游泳',
        source='test',
        confidence='high'
    )
    
    prefs = svc.get_preferences()
    print(f"   写入后: sports_likes={prefs['sports_likes']}")
    print()
    
    # 3. 写入菜系偏好
    print("3. 写入喜欢的菜系: 粤菜, 清淡")
    svc.update_single_field(
        'cuisine_likes',
        '粤菜, 清淡',
        source='dialogue_extract',
        confidence='high'
    )
    
    prefs = svc.get_preferences()
    print(f"   写入后: cuisine_likes={prefs['cuisine_likes']}")
    print()
    
    # 4. 覆盖旧值（测试变更记录）
    print("4. 覆盖为不喜欢游泳（测试变更记录）")
    svc.update_single_field(
        'sports_dislikes',
        '游泳',
        source='dialogue_extract',
        confidence='medium'
    )
    
    prefs = svc.get_preferences()
    print(f"   sports_dislikes={prefs['sports_dislikes']}")
    print(f"   notes={prefs.get('notes', '')[:100] if prefs.get('notes') else '(无)'}")
    print()
    
    # 5. 检查完整性
    print("5. 检查偏好完整性:")
    print(f"   运动偏好是否足够: {svc.is_preference_complete_for('sports')}")
    print(f"   饮食偏好是否足够: {svc.is_preference_complete_for('diet')}")
    print(f"   营养偏好是否足够: {svc.is_preference_complete_for('nutrition')}")
    print()


def test_guidance():
    """测试引导提问"""
    print("=== 引导提问测试 ===\n")
    
    for pref_type in ['sports', 'diet', 'nutrition']:
        question = get_guidance_question(pref_type)
        print(f"{pref_type}: {question}")
    
    print()


def test_context():
    """测试上下文构建"""
    print("=== 上下文构建测试 ===\n")
    
    ctx = build_preference_context("001")
    print(f"profile_id=001 的偏好上下文:")
    print(ctx if ctx else "(无偏好数据)")
    print()


def test_integration_with_service():
    """测试与 LifeOS Service 的集成"""
    print("=== 与 LifeOS Service 集成测试 ===\n")
    
    # 测试是否能正常导入
    try:
        from lifeos_service import get_service
        print("[OK] lifeos_service 导入成功")
    except ImportError as e:
        print(f"[SKIP] lifeos_service 导入失败: {e}")
        return
    
    # 获取金的 service
    svc = get_service("001")
    print(f"[OK] LifeOSService for 001: {svc}")
    print()


if __name__ == "__main__":
    test_extraction()
    test_service()
    test_guidance()
    test_context()
    test_integration_with_service()
    
    print("=== 测试完成 ===")
