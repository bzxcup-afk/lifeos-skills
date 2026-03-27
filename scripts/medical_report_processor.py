#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeOS 医疗报告归档处理器
整合视觉分析(阶段A)和风险归档(阶段B)
直接调用 Doubao-1.5-thinking-vision-pro
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# 添加技能目录到路径
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR))

from scripts.vision_analyzer import analyze_medical_report, load_config


def check_hard_conflict(report_meta: Dict, sender_profile: Dict) -> Tuple[bool, str]:
    """
    检测硬冲突
    返回: (is_conflict, conflict_reason)
    """
    # 年龄冲突（相差超过20岁）
    if report_meta.get("age") and sender_profile.get("age"):
        age_diff = abs(report_meta["age"] - sender_profile["age"])
        if age_diff > 20:
            return True, f"年龄冲突：报告患者{report_meta['age']}岁，发言者{sender_profile['age']}岁，相差{age_diff}岁"

    # 性别冲突
    if report_meta.get("gender") and sender_profile.get("gender"):
        if report_meta["gender"] != sender_profile["gender"]:
            return True, f"性别冲突：报告患者{report_meta['gender']}，发言者{sender_profile['gender']}"

    # 患者姓名缺失或模糊，且年龄明显不符
    if not report_meta.get("patient_name") or report_meta.get("patient_name") == "":
        if report_meta.get("age") and sender_profile.get("age"):
            if abs(report_meta["age"] - sender_profile["age"]) > 10:
                return True, f"身份不明：报告患者年龄{report_meta['age']}岁与发言者年龄{sender_profile['age']}岁不符，且患者姓名缺失"

    return False, ""


def determine_archive_strategy(risk_assessment: Dict, report_meta: Dict, sender_profile: Dict) -> str:
    """
    确定归档策略
    返回: A/B/C/D/E 策略标识
    """
    # 首先检测硬冲突
    hard_conflict, conflict_reason = check_hard_conflict(report_meta, sender_profile)
    
    if hard_conflict:
        risk_assessment["has_hard_conflict"] = True
        risk_assessment["conflict_notes"] = conflict_reason
        return "E"  # BLOCKED
    
    # D: 全局高风险（表级问题）
    if risk_assessment.get("global_risk_level") == "high":
        return "D"  # RAW_ONLY
    
    # C: 关键项目有识别风险（非指标异常）
    if risk_assessment.get("critical_items_with_risk") and risk_assessment.get("high_risk_count", 0) > 0:
        return "C"  # SAVE_NOT_UPDATE_PROFILE
    
    # B: 中风险（识别过程问题）
    if risk_assessment.get("medium_risk_count", 0) > 0 or risk_assessment.get("global_risk_level") == "medium":
        return "B"  # ARCHIVE_WITH_WARNING
    
    # A: 无识别风险 + 无硬冲突
    return "A"  # FULL_ARCHIVE


def process_medical_report(
    image_path: str,
    sender_profile: Dict = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    处理医疗报告的主入口函数
    
    Args:
        image_path: 报告图片路径
        sender_profile: 发送者档案（用于身份匹配和风险评估）
        output_dir: 输出目录（可选）
        
    Returns:
        包含完整处理结果的字典
    """
    result = {
        "success": False,
        "stage_a": None,
        "stage_b": None,
        "error": None
    }
    
    # === 阶段A: 视觉识别 ===
    print("[阶段A] 开始视觉识别...")
    vision_result = analyze_medical_report(image_path)
    
    if not vision_result.get("success"):
        result["error"] = f"视觉识别失败: {vision_result.get('error', '未知错误')}"
        print(f"[错误] {result['error']}")
        return result
    
    result["stage_a"] = vision_result["data"]
    print("[阶段A] 视觉识别完成")
    
    # === 阶段B: 风险分析与归档策略 ===
    print("[阶段B] 开始风险分析...")
    
    # 提取关键信息
    report_meta = vision_result["data"].get("report_meta", {})
    confidence_check = vision_result["data"].get("confidence_check", {})
    table_analysis = vision_result["data"].get("table_structure_analysis", {})
    
    # 构建风险评估
    risk_assessment = {
        "global_risk_level": table_analysis.get("overall_risk_level", "low"),
        "has_possible_shift": table_analysis.get("has_possible_shift", False),
        "high_risk_count": sum(1 for item in vision_result["data"].get("items", []) 
                               if any(r.get("risk_level") == "high" for r in item.get("risks", []))),
        "medium_risk_count": sum(1 for item in vision_result["data"].get("items", []) 
                                 if any(r.get("risk_level") == "medium" for r in item.get("risks", []))),
        "critical_items_with_risk": any(
            item.get("review_priority") == "high" 
            for item in vision_result["data"].get("items", [])
        ),
        "extraction_confidence": confidence_check.get("extraction_confidence", 0),
        "total_archive_confidence": confidence_check.get("total_archive_confidence", 0),
        "has_hard_conflict": confidence_check.get("hard_conflict", False),
        "conflict_notes": confidence_check.get("conflict_notes", "")
    }
    
    # 确定归档策略
    sender_profile = sender_profile or {"age": 35, "gender": "男"}  # 默认值，实际应从数据库读取
    strategy = determine_archive_strategy(risk_assessment, report_meta, sender_profile)
    
    # 构建阶段B结果
    stage_b_result = {
        "risk_assessment": risk_assessment,
        "archive_strategy": strategy,
        "strategy_name": {
            "A": "FULL_ARCHIVE - 完整归档",
            "B": "ARCHIVE_WITH_WARNING - 带警告归档",
            "C": "SAVE_NOT_UPDATE_PROFILE - 保存但不更新档案",
            "D": "RAW_ONLY - 仅保存原始数据",
            "E": "BLOCKED - 禁止归档"
        }.get(strategy, "UNKNOWN"),
        "recommendations": generate_recommendations(strategy, risk_assessment)
    }
    
    result["stage_b"] = stage_b_result
    result["success"] = True
    
    print(f"[阶段B] 风险分析完成，归档策略: {strategy}")
    
    # 保存结果（如果指定了输出目录）
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = os.path.basename(image_path).split('.')[0]
        result_file = output_path / f"{timestamp}_analysis.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"[输出] 结果已保存: {result_file}")
    
    return result


def generate_recommendations(strategy: str, risk_assessment: Dict) -> list:
    """生成归档建议"""
    recommendations = []
    
    if strategy == "A":
        recommendations.append("✓ 数据质量良好，建议完整归档")
        recommendations.append("✓ 可更新健康档案主表")
        
    elif strategy == "B":
        recommendations.append("⚠ 存在中等风险，建议带警告归档")
        recommendations.append("⚠ 标记为'已归档-含警告'，建议用户核实")
        
    elif strategy == "C":
        recommendations.append("⚠ 关键项目有识别风险")
        recommendations.append("⚠ 建议保存原始数据和指标明细，但不更新健康档案主表")
        
    elif strategy == "D":
        recommendations.append("❌ 表格结构存在高风险")
        recommendations.append("❌ 建议仅保存原始报告图片和OCR文本")
        recommendations.append("❌ 需人工核对后再决定是否归档")
        
    elif strategy == "E":
        recommendations.append("🚫 检测到硬冲突（身份不匹配）")
        recommendations.append("🚫 禁止自动归档")
        recommendations.append("🚫 请用户确认：强制归档 / 放弃归档")
    
    # 添加通用建议
    if risk_assessment.get("extraction_confidence", 0) < 80:
        recommendations.append("ℹ 提取置信度较低，建议人工复核")
    
    if risk_assessment.get("has_hard_conflict"):
        recommendations.append("⚠ 身份匹配存在冲突，请核实")
    
    return recommendations


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='医疗报告归档处理器')
    parser.add_argument('image_path', help='报告图片路径')
    parser.add_argument('-o', '--output', help='输出目录')
    parser.add_argument('-p', '--pretty', action='store_true', help='格式化输出')
    
    args = parser.parse_args()
    
    # 检查图片是否存在
    if not os.path.exists(args.image_path):
        print(f"错误: 图片不存在: {args.image_path}", file=sys.stderr)
        sys.exit(1)
    
    # 处理报告
    print(f"处理: {args.image_path}")
    result = process_medical_report(args.image_path, output_dir=args.output)
    
    # 输出结果
    if result['success']:
        print("\n=== 处理成功 ===")
        print(f"归档策略: {result['stage_b']['archive_strategy']}")
        print(f"策略说明: {result['stage_b']['strategy_name']}")
        print("\n建议:")
        for rec in result['stage_b']['recommendations']:
            print(f"  {rec}")
    else:
        print(f"\n=== 处理失败 ===")
        print(f"错误: {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()
