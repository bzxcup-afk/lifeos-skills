#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段B：医疗报告归档执行 v1.1.0
增强版：风险感知 + 有条件归档 + 用户重点核实
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

# ============================================================================
# 枚举定义
# ============================================================================

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ArchiveStatus(Enum):
    PENDING = "pending"
    ARCHIVED = "archived"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"

class ArchiveStrategy(Enum):
    FULL_ARCHIVE = "full_archive"               # A: 完全归档
    ARCHIVE_WITH_WARNING = "archive_with_warning"  # B: 带警告归档
    SAVE_NOT_UPDATE_PROFILE = "save_not_update_profile"  # C: 保存但不更新主档案
    RAW_ONLY = "raw_only"                      # D: 仅保存原始报告
    BLOCKED = "blocked"                       # E: 拦截归档

# 关键项目列表
CRITICAL_ITEMS = [
    "LDL-C", "LDL_C", "低密度脂蛋白", "HDL-C", "HDL_C",
    "TC", "总胆固醇", "TG", "甘油三酯",
    "HbA1c", "HbA1C", "糖化血红蛋白", "FPG", "空腹血糖",
    "ALT", "谷丙转氨酶", "AST", "谷草转氨酶",
    "Cr", "Creatinine", "肌酐", "BUN", "尿素氮", "UA", "尿酸",
    "血压", "收缩压", "舒张压", "SBP", "DBP"
]

# ============================================================================
# 风险解析器
# ============================================================================

def parse_risks(visual_json: Dict) -> Dict[str, Any]:
    """解析三级风险"""
    
    # 表级风险 (支持阶段A输出的两种字段名)
    table_check = visual_json.get("table_structure_analysis", {}) or visual_json.get("table_structure_check", {})
    global_risk_level = table_check.get("overall_risk_level", "low")
    has_shift = table_check.get("has_possible_shift", False)
    
    if global_risk_level == "high" or (has_shift and global_risk_level == "medium"):
        final_global_risk = "high"
    elif has_shift or global_risk_level == "medium":
        final_global_risk = "medium"
    else:
        final_global_risk = "low"
    
    # 项目级风险
    items = visual_json.get("items", [])
    item_risks = []
    critical_items_with_risk = []
    
    for item in items:
        std_name = item.get("standard_name", "")
        # 支持两种格式：risk_flags (字符串数组) 和 risks (对象数组)
        risk_flags = item.get("risk_flags", [])
        risks_array = item.get("risks", [])
        if risks_array and not risk_flags:
            # 将 risks 数组转换为 risk_flags 字符串数组
            risk_flags = [r.get("risk_type", "") for r in risks_array if r.get("risk_level") == "high"]
        review_priority = item.get("review_priority", "low")
        
        # 判断项目风险等级
        if review_priority == "high":
            item_risk = "high"
        elif risk_flags:
            critical_flags = ["column_shift", "row_shift", "unit_mismatch", "range_mismatch"]
            if any(f in critical_flags for f in risk_flags):
                item_risk = "high"
            else:
                item_risk = "medium"
        else:
            item_risk = "low"
        
        item_risks.append({
            "name": item.get("raw_name"),
            "standard_name": std_name,
            "risk_level": item_risk,
            "risk_flags": risk_flags,
            "review_priority": review_priority
        })
        
        # 检查是否为关键项目且有风险
        is_critical = any(crit.lower() in std_name.lower() for crit in CRITICAL_ITEMS)
        if is_critical and (review_priority == "high" or risk_flags):
            critical_items_with_risk.append(item.get("raw_name"))
    
    # 硬冲突检查
    confidence_check = visual_json.get("confidence_check", {})
    has_hard_conflict = confidence_check.get("hard_conflict", False)
    conflict_notes_list = []
    
    # 1. API返回的硬冲突
    if has_hard_conflict:
        conflict_notes_list.append(confidence_check.get("conflict_notes", "API检测到硬冲突"))
    
    # 合并冲突原因
    conflict_notes = "; ".join(conflict_notes_list) if conflict_notes_list else ""
    
    return {
        "global_risk_level": final_global_risk,
        "has_hard_conflict": has_hard_conflict,
        "conflict_notes": conflict_notes,
        "item_risks": item_risks,
        "critical_items_with_risk": critical_items_with_risk,
        "high_risk_count": sum(1 for i in item_risks if i["risk_level"] == "high"),
        "medium_risk_count": sum(1 for i in item_risks if i["risk_level"] == "medium")
    }


# ============================================================================
# 策略确定
# ============================================================================

def determine_strategy(risk_assessment: Dict) -> ArchiveStrategy:
    """根据风险确定归档策略"""
    
    # E: 硬冲突
    if risk_assessment["has_hard_conflict"]:
        return ArchiveStrategy.BLOCKED
    
    # D: 全局高风险
    if risk_assessment["global_risk_level"] == "high":
        return ArchiveStrategy.RAW_ONLY
    
    # C: 关键项目有识别风险（非指标异常）
    # 必须同时满足：有关键项目有风险 + 存在高风险项
    if risk_assessment["critical_items_with_risk"] and risk_assessment["high_risk_count"] > 0:
        return ArchiveStrategy.SAVE_NOT_UPDATE_PROFILE
    
    # B: 中风险
    if risk_assessment["medium_risk_count"] > 0 or risk_assessment["global_risk_level"] == "medium":
        return ArchiveStrategy.ARCHIVE_WITH_WARNING
    
    # A: 无风险
    return ArchiveStrategy.FULL_ARCHIVE


# ============================================================================
# 用户提示生成
# ============================================================================

def generate_user_prompt(visual_json: Dict, risk_assessment: Dict, strategy: ArchiveStrategy) -> str:
    """生成用户核实提示"""
    
    report_meta = visual_json.get("report_meta", {})
    summary = visual_json.get("summary", {})
    # 防御性处理：确保 summary 是字典而非字符串
    if isinstance(summary, str):
        summary = {"text": summary}
    
    lines = []
    lines.append("=" * 50)
    lines.append("📋 医疗报告归档核实")
    lines.append("=" * 50)
    lines.append("")
    
    # 报告信息
    lines.append("【识别结果摘要】")
    lines.append(f"  类型：{report_meta.get('report_type', '未知')}")
    lines.append(f"  医院：{report_meta.get('hospital', '未知')}")
    lines.append(f"  日期：{report_meta.get('exam_date', '未知')}")
    lines.append(f"  患者：{report_meta.get('patient_name', '未知')}")
    
    abnormal_count = summary.get("abnormal_count", 0)
    if abnormal_count > 0:
        lines.append("")
        lines.append(f"  关键异常项：{abnormal_count} 项")
        for item in summary.get("key_abnormal_items", []):
            lines.append(f"    {item}")
    
    lines.append("")
    lines.append("【风险提示】")
    lines.append(f"  全局风险：{risk_assessment['global_risk_level']}")
    lines.append(f"  硬冲突：{'是' if risk_assessment['has_hard_conflict'] else '否'}")
    lines.append(f"  关键项目风险：{len(risk_assessment['critical_items_with_risk'])} 项")
    lines.append(f"  中风险项目：{risk_assessment['medium_risk_count']} 项")
    
    # 关键风险项目详情
    if risk_assessment["critical_items_with_risk"]:
        lines.append("")
        lines.append("【关键风险项目】")
        for name in risk_assessment["critical_items_with_risk"][:5]:
            lines.append(f"  {name}")
    
    lines.append("")
    
    # 消息
    messages = {
        "full_archive": "✅ 报告检查通过，可以正常归档。",
        "archive_with_warning": "⚡ 风险提示：部分项目存在中等风险，建议查看风险详情后确认归档。",
        "save_not_update_profile": "⚠️ 关键指标风险：建议核实后再更新健康档案。",
        "raw_only": "⚠️ 表格结构风险：建议人工核实后再归档。",
        "blocked": "🚫 硬冲突检测：患者身份信息与档案存在冲突。"
    }
    lines.append(f"【归档建议】{messages.get(strategy.value, '')}")
    
    lines.append("")
    lines.append("【可选操作】")
    
    actions_map = {
        "full_archive": ["1. 确认归档", "2. 放弃归档"],
        "archive_with_warning": ["1. 确认归档", "2. 人工核实", "3. 放弃归档"],
        "save_not_update_profile": ["1. 确认并更新档案", "2. 仅保存报告", "3. 放弃归档"],
        "raw_only": ["1. 人工核实后归档", "2. 强制归档", "3. 放弃归档"],
        "blocked": ["1. 强制归档", "2. 放弃归档"]
    }
    
    for action in actions_map.get(strategy.value, []):
        lines.append(f"  {action}")
    
    lines.append("")
    lines.append("=" * 50)
    lines.append("请回复操作编号或关键词")
    lines.append("=" * 50)
    
    return "\n".join(lines)


# ============================================================================
# 归档执行
# ============================================================================

def execute_archive(user_choice: str, strategy: ArchiveStrategy) -> Dict[str, Any]:
    """根据用户选择执行归档"""
    
    confirm_keywords = ["确认", "confirm", "归档", "1"]
    save_only_keywords = ["仅保存", "save_only", "2"]
    manual_keywords = ["人工核实", "manual_review", "2", "3"]
    force_keywords = ["强制", "force", "2"]
    abandon_keywords = ["放弃", "abandon", "3", "no"]
    
    result = {
        "status": "pending",
        "strategy": strategy.value,
        "tables_to_write": [],
        "warnings": [],
        "next_steps": []
    }
    
    # 根据策略处理
    if strategy == ArchiveStrategy.BLOCKED:
        if any(k in user_choice for k in force_keywords):
            result["status"] = "force_archived"
            result["tables_to_write"] = ["raw_reports", "reports_master", "indicators_detail", "health_master"]
            result["warnings"].append("存在硬冲突，已强制归档")
        else:
            result["status"] = "abandoned"
            
    elif strategy == ArchiveStrategy.RAW_ONLY:
        if any(k in user_choice for k in manual_keywords):
            result["status"] = "manual_review_pending"
            result["tables_to_write"] = ["raw_reports"]
            result["warnings"].append("等待人工核实后完整归档")
        elif any(k in user_choice for k in confirm_keywords):
            result["status"] = "archived_with_warning"
            result["tables_to_write"] = ["raw_reports", "reports_master", "indicators_detail"]
            result["warnings"].append("表格结构存在风险，已归档但建议复查")
        else:
            result["status"] = "abandoned"
            
    elif strategy == ArchiveStrategy.SAVE_NOT_UPDATE_PROFILE:
        if any(k in user_choice for k in confirm_keywords):
            result["status"] = "archived_with_review"
            result["tables_to_write"] = ["raw_reports", "reports_master", "indicators_detail", "health_master"]
            result["warnings"].append("已更新健康档案，但关键指标建议复查")
        elif any(k in user_choice for k in save_only_keywords):
            result["status"] = "saved_only"
            result["tables_to_write"] = ["raw_reports", "reports_master", "indicators_detail"]
            result["warnings"].append("已保存报告但未更新健康档案")
        else:
            result["status"] = "abandoned"
            
    elif strategy == ArchiveStrategy.ARCHIVE_WITH_WARNING:
        if any(k in user_choice for k in confirm_keywords):
            result["status"] = "archived_with_warning"
            result["tables_to_write"] = ["raw_reports", "reports_master", "indicators_detail", "health_master"]
            result["warnings"].append("存在中等风险，已归档但建议复查")
        elif any(k in user_choice for k in manual_keywords):
            result["status"] = "manual_review_pending"
            result["tables_to_write"] = ["raw_reports"]
        else:
            result["status"] = "abandoned"
            
    else:  # FULL_ARCHIVE
        if any(k in user_choice for k in confirm_keywords):
            result["status"] = "archived"
            result["tables_to_write"] = ["raw_reports", "reports_master", "indicators_detail", "health_master"]
        else:
            result["status"] = "abandoned"
    
    # 添加后续步骤
    next_steps_map = {
        "archived": ["✅ 归档成功", "📊 可在系统中查看"],
        "archived_with_warning": ["⚡ 已归档但存在风险标记", "🔍 建议复查相关指标"],
        "archived_with_review": ["✅ 已归档", "🔴 关键指标建议复查"],
        "saved_only": ["📄 已保存", "👤 请核实后手动更新档案"],
        "manual_review_pending": ["⏳ 等待人工审核"],
        "force_archived": ["⚠️ 已强制归档", "🚨 建议后续核查数据一致性"],
        "abandoned": ["❌ 已放弃"]
    }
    result["next_steps"] = next_steps_map.get(result["status"], [])
    
    return result


# ============================================================================
# 主入口函数
# ============================================================================

def process_archive_v1_1_0(visual_json: Dict) -> Dict[str, Any]:
    """
    医疗报告归档主流程 v1.1.0
    
    Args:
        visual_json: 视觉识别阶段输出的JSON
        
    Returns:
        包含用户提示和执行信息的字典
    """
    # 步骤1-2: 风险解析
    risk_assessment = parse_risks(visual_json)
    
    # 步骤3: 确定策略
    strategy = determine_strategy(risk_assessment)
    
    # 步骤4: 生成用户提示
    user_prompt = generate_user_prompt(visual_json, risk_assessment, strategy)
    
    return {
        "status": "waiting_for_confirmation",
        "version": "1.1.0",
        "strategy": strategy.value,
        "risk_assessment": risk_assessment,
        "user_prompt": user_prompt,
        "message": "请选择操作并调用 execute_archive_v1_1_0() 执行归档"
    }


def execute_archive_v1_1_0(user_choice: str, previous_result: Dict) -> Dict[str, Any]:
    """
    执行归档（用户确认后调用）
    
    Args:
        user_choice: 用户选择
        previous_result: process_archive_v1_1_0() 的返回值
    """
    strategy = ArchiveStrategy(previous_result["strategy"])
    return execute_archive(user_choice, strategy)


# ============================================================================
# 示例
# ============================================================================

if __name__ == "__main__":
    # 测试示例
    test_visual_json = {
        "report_meta": {
            "report_type": "血脂检查",
            "hospital": "天津市第四中心医院",
            "exam_date": "2025-03-22",
            "patient_name": "金志远",
            "gender": "男",
            "age": "45"
        },
        "summary": {
            "abnormal_count": 2,
            "key_abnormal_items": ["LDL-C", "甘油三酯"]
        },
        "table_structure_check": {
            "table_confidence": 0.92,
            "has_possible_shift": False,
            "overall_risk_level": "low"
        },
        "items": [
            {
                "row_index": 1,
                "raw_name": "LDL-C",
                "standard_name": "LDL-C",
                "value": 4.2,
                "unit": "mmol/L",
                "reference_range": "<3.4",
                "abnormal_flag": "high",
                "confidence": 0.85,
                "risk_flags": ["range_mismatch"],
                "review_priority": "high"
            },
            {
                "row_index": 2,
                "raw_name": "甘油三酯",
                "standard_name": "TG",
                "value": 2.5,
                "unit": "mmol/L",
                "reference_range": "<1.7",
                "abnormal_flag": "high",
                "confidence": 0.90,
                "risk_flags": [],
                "review_priority": "high"
            }
        ],
        "confidence_check": {
            "hard_conflict": False,
            "identity_match_score": 95,
            "extraction_confidence": 90
        }
    }
    
    print("=" * 60)
    print("测试 v1.1.0 归档流程")
    print("=" * 60)
    
    # 执行主流程
    result = process_archive_v1_1_0(test_visual_json)
    
    print(f"\n策略: {result['strategy']}")
    print(f"风险等级: {result['risk_assessment']['global_risk_level']}")
    print(f"关键项目风险: {result['risk_assessment']['critical_items_with_risk']}")
    
    print("\n" + "-" * 60)
    print("用户提示:")
    print("-" * 60)
    print(result["user_prompt"])
    
    # 模拟用户确认
    print("\n" + "-" * 60)
    print("模拟用户选择: '确认归档'")
    print("-" * 60)
    
    execution = execute_archive_v1_1_0("确认", result)
    print(f"\n执行状态: {execution['status']}")
    print(f"写入表: {execution['tables_to_write']}")
    print(f"警告: {execution['warnings']}")
    print(f"后续: {execution['next_steps']}")
