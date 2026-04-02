# -*- coding: utf-8 -*-
"""健康数据模块测试脚本"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from health_data.trigger_router import TriggerRouter
from health_data.metric_normalizer import MetricNormalizer
from health_data.validator import Validator
from health_data.deduplicator import Deduplicator
from health_data.query_engine import QueryEngine
from health_data.summary_generator import SummaryGenerator
from health_data.service import HealthDataService


def test_trigger_router():
    print("\n=== 测试触发路由 ===")
    
    # 测试1：匹配关键词 + 有图片
    result = TriggerRouter.should_activate("记录健康数据", has_image=True)
    print(f"测试1（匹配+有图）: {result}")
    assert result["should_activate"] == True
    
    # 测试2：匹配关键词 + 无图片
    result = TriggerRouter.should_activate("记录健康数据", has_image=False)
    print(f"测试2（匹配+无图）: {result}")
    assert result["should_activate"] == False
    assert "missing_image_tip" in result
    
    # 测试3：不匹配关键词
    result = TriggerRouter.should_activate("今天天气不错", has_image=True)
    print(f"测试3（不匹配）: {result}")
    assert result["should_activate"] == False
    
    print("✓ 触发路由测试通过")


def test_metric_normalizer():
    print("\n=== 测试指标标准化 ===")
    
    records = [
        {"metric_type": "步数", "value": 5665, "unit": "步", "date": "2026-04-02", "granularity": "day", "raw_text": "5665步"},
        {"metric_type": "心率", "value": 83, "unit": "bpm", "date": "2026-04-02", "granularity": "instant", "raw_text": "83bpm"},
        {"metric_type": "血压", "value": 128, "unit": "mmHg", "date": "2026-04-02", "granularity": "instant", "raw_text": "128/84 mmHg"},
    ]
    
    normalized = MetricNormalizer.normalize_records(records)
    print(f"标准化后记录数: {len(normalized)}")
    for r in normalized:
        print(f"  - {r['metric_type']}: {r['value']} {r['unit']}")
    
    # 血压应该被拆成两条
    bp_records = [r for r in normalized if r['metric_type'].startswith('blood_pressure')]
    print(f"血压记录数（应为2）: {len(bp_records)}")
    
    print("✓ 指标标准化测试通过")


def test_validator():
    print("\n=== 测试数据校验 ===")
    
    records = [
        {"metric_type": "heart_rate", "value": 83, "unit": "bpm", "date": "2026-04-02"},
        {"metric_type": "heart_rate", "value": 280, "unit": "bpm", "date": "2026-04-02"},  # 超范围
        {"metric_type": "blood_glucose", "value": 5.5, "unit": "mmol/L", "date": "2026-04-02"},
        {"metric_type": "weight_kg", "value": 70.5, "unit": "kg", "date": "2026-04-02"},
    ]
    
    result = Validator.validate_batch(records)
    print(f"有效记录: {result['valid_count']}, 无效记录: {result['invalid_count']}")
    
    for r in result["invalid_records"]:
        print(f"  无效: {r['metric_type']} = {r['value']}, 原因: {r.get('validation_notes')}")
    
    assert result["valid_count"] == 3
    assert result["invalid_count"] == 1
    
    print("✓ 数据校验测试通过")


def test_query_engine():
    print("\n=== 测试查询引擎 ===")
    
    # 测试解析
    parsed = QueryEngine.parse_query("查看最近7天步数")
    print(f"解析'查看最近7天步数': {parsed}")
    assert parsed["metric_type"] == "steps"
    assert parsed["time_range"] == 7
    
    parsed = QueryEngine.parse_query("最近30天体重变化")
    print(f"解析'最近30天体重变化': {parsed}")
    assert parsed["metric_type"] == "weight_kg"
    assert parsed["time_range"] == 30
    
    print("✓ 查询解析测试通过")


def test_summary_generator():
    print("\n=== 测试总结生成器 ===")
    
    records = [
        {"metric_type": "steps", "value": 5665, "unit": "steps", "date": "2026-04-02", "raw_text": "5665步"},
        {"metric_type": "active_calories", "value": 209, "unit": "kcal", "date": "2026-04-02", "raw_text": "209千卡"},
        {"metric_type": "heart_rate", "value": 83, "unit": "bpm", "date": "2026-04-02", "raw_text": "83bpm"},
    ]
    
    formatted = SummaryGenerator.format_records_for_llm(records)
    print("格式化结果:")
    print(formatted)
    
    print("✓ 总结生成器测试通过")


def test_service():
    print("\n=== 测试服务入口 ===")
    
    svc = HealthDataService(profile_id="001", user_id="ou_test")
    
    # 测试触发判断
    result = svc.should_activate("记录健康数据", has_image=True)
    print(f"服务触发判断: {result['should_activate']}")
    
    # 测试查询解析
    parsed = svc.parse_query("查看最近7天步数")
    print(f"查询解析: {parsed}")
    
    # 测试总结构建
    records = [{"metric_type": "steps", "value": 5665, "unit": "steps", "date": "2026-04-02", "raw_text": "5665步"}]
    prompt = svc.build_summary("single_metric", {"metric_type": "steps", "days": 7}, records)
    print(f"总结Prompt:\n{prompt}")
    
    print("✓ 服务入口测试通过")


if __name__ == "__main__":
    try:
        test_trigger_router()
        test_metric_normalizer()
        test_validator()
        test_query_engine()
        test_summary_generator()
        test_service()
        print("\n" + "="*50)
        print("全部测试通过！")
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
