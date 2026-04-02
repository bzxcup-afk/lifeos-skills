# -*- coding: utf-8 -*-
"""端到端集成测试（无需真实图片）"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile
import hashlib

print("=== 端到端测试：模拟完整导入流程 ===\n")

# 创建临时文件用于测试 hash
with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
    f.write(b"fake image content for testing")
    temp_image_path = f.name

print(f"临时测试图片: {temp_image_path}")

# 模拟 LLM 返回的识图结果
llm_result = {
    "source_app": "xiaomi_health",
    "records": [
        {"metric_type": "步数", "value": 5665, "unit": "步", "date": "2026-04-02", "granularity": "day", "raw_text": "5665 /6000步"},
        {"metric_type": "卡路里", "value": 209, "unit": "千卡", "date": "2026-04-02", "granularity": "day", "raw_text": "209 千卡"},
        {"metric_type": "心率", "value": 83, "unit": "bpm", "date": "2026-04-02", "granularity": "instant", "raw_text": "83 bpm"},
        {"metric_type": "血压", "value": 128, "unit": "mmHg", "date": "2026-04-02", "granularity": "instant", "raw_text": "128/84 mmHg"},
    ]
}

from health_data.service import HealthDataService

svc = HealthDataService(profile_id="001", user_id="ou_fde56bd8d48eca22b3d57ab990ee4f02")

result = svc.import_from_llm_result(temp_image_path, llm_result)

print("\n导入结果:")
print(f"  Success: {result['success']}")
print(f"  导入条数: {result['imported_count']}")
print(f"  跳过条数: {result['skipped_count']}")
print(f"  回复消息:\n{result['reply_message']}")

print("\n=== 查询测试 ===")

from health_data.entry import query_health_data

query_result = query_health_data("001", "查看最近7天步数")
print(f"\n查询 '查看最近7天步数':")
print(f"  Success: {query_result['success']}")
print(f"  记录数: {query_result['record_count']}")
print(f"  Stats: {query_result['stats']}")
print(f"  格式化数据:\n{query_result['formatted_data']}")

print("\n=== 全量查询测试 ===")
query_result2 = query_health_data("001", "总结最近7天健康数据")
print(f"查询 '总结最近7天健康数据':")
print(f"  Success: {query_result2['success']}")
print(f"  记录数: {query_result2['record_count']}")
print(f"  格式化数据:\n{query_result2['formatted_data']}")

print("\n=== 重复导入测试（去重验证）===")
result2 = svc.import_from_llm_result(temp_image_path, llm_result)
print(f"第二次导入（同一图片）:")
print(f"  导入条数: {result2['imported_count']} (应为0，触发去重)")
print(f"  跳过条数: {result2['skipped_count']}")

print("\n=== 测试完成 ===")

# 清理
import os
os.unlink(temp_image_path)
