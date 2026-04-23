# -*- coding: utf-8 -*-
"""
问题导向干预 - Phase 4: 周复盘与下一周计划生成

在用户完成一周执行并收集到周复盘反馈后：
1. 总结本周执行情况（变化，不是流水账）
2. 判断哪些策略有效/无效
3. 生成正向反馈 + 温和引导
4. 生成下一周调整策略（小幅调整，不推翻）
5. 生成新的优先事项
6. 复用阶段3逻辑，生成新的提醒与反馈任务
7. 更新 case 文件（形成连续记录）
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# ============================================================================
# 路径配置
# ============================================================================

SKILL_DIR = Path(r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main")
CASES_DIR = SKILL_DIR / "cases"

# ============================================================================
# 工具函数
# ============================================================================

def load_json(filepath: Path, default: Any = None) -> Any:
    """安全读取JSON文件"""
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] 读取文件失败 {filepath}: {e}")
    return default if default is not None else []


def save_json(filepath: Path, data: Any) -> bool:
    """安全写入JSON文件"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] 写入文件失败 {filepath}: {e}")
        return False


# ============================================================================
# Step 1: 读取上一周 case 数据
# ============================================================================

def find_latest_case(user_id: str, problem_id: str) -> Optional[Path]:
    """找到最新的 case 文件"""
    case_dir = CASES_DIR / problem_id
    if not case_dir.exists():
        return None
    
    cases = list(case_dir.glob(f"case-{user_id}-*.md"))
    if not cases:
        return None
    
    # 按修改时间排序，取最新的
    cases.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return cases[0]


def parse_case_content(case_path: Path) -> Dict[str, Any]:
    """解析 case 文件内容"""
    if not case_path.exists():
        return {}
    
    content = case_path.read_text(encoding="utf-8")
    
    result = {
        "path": str(case_path),
        "created_at": None,
        "priority_items": [],
        "reminders": [],
        "weekly_reviews": [],
        "week_summaries": []
    }
    
    # 提取基本信息
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- created_at:"):
            result["created_at"] = line.split(":", 1)[1].strip()
        elif "## 本周调整计划" in line:
            result["_section"] = "plan"
        elif "## 提醒安排" in line:
            result["_section"] = "reminders"
        elif "## 周复盘" in line or "## Week" in line:
            result["_section"] = "review"
        elif "## 本周总结" in line:
            result["_section"] = "summary"
    
    return result


# ============================================================================
# Step 2: 生成周复盘总结（给用户）
# ============================================================================

def build_weekly_summary(
    display_name: str,
    last_week_items: List[str],
    user_feedback: str,
    canonical_id: str
) -> str:
    """
    生成周复盘总结
    
    规则：
    1. 先说进展，再说问题
    2. 不否定用户
    3. 用"很正常""这个阶段常见"降低压力
    """
    
    # 分析用户反馈，提取关键词
    feedback_lower = user_feedback.lower()
    
    # 判断哪些有进展
    positive_keywords = ["好", "改善", "不错", "开始", "尝试", "做到", "有"]
    negative_keywords = ["难", "困难", "做不到", "没", "不", "还是"]
    
    has_progress = any(k in feedback_lower for k in positive_keywords)
    has_difficulty = any(k in feedback_lower for k in negative_keywords)
    
    # 生成总结
    lines = []
    lines.append("【这周的情况我帮你简单总结一下】")
    lines.append("")
    
    # 整体趋势判断
    if has_progress and has_difficulty:
        lines.append("整体来看，是一个「开始在变化，但还没稳定下来」的阶段，这是正常的。")
    elif has_progress:
        lines.append("整体来看，这周有一些积极的信号，继续保持就好。")
    elif has_difficulty:
        lines.append("整体来看，还在适应的阶段，这个很正常，不用着急。")
    else:
        lines.append("整体来看，这周可能变化还不明显，我们可以下周再看看。")
    
    lines.append("我们可以在这个基础上稍微调整一下，继续往前走。")
    
    return "\n".join(lines)


# ============================================================================
# Step 3: 生成下周策略说明（给用户）
# ============================================================================

def build_next_week_strategy(
    keep_items: List[str],
    adjust_items: List[str],
    display_name: str
) -> str:
    """生成下周策略说明"""
    
    lines = []
    lines.append("")
    lines.append("【下周我们稍微调整一下】")
    lines.append("")
    lines.append("这周我们不需要推翻重来，而是在你已经做过的基础上，稍微做一点调整：")
    lines.append("")
    
    # 保持的
    if keep_items:
        lines.append("继续保持：")
        for item in keep_items[:2]:
            lines.append(f"- {item}")
        lines.append("")
    
    # 调整的
    if adjust_items:
        lines.append("稍微调整：")
        for item in adjust_items[:2]:
            # 提取关键动作，生成温和调整建议
            lines.append(f"- {item}（这个可以慢慢来，不着急）")
        lines.append("")
    
    return "\n".join(lines)


# ============================================================================
# Step 4: 生成下一周优先事项
# ============================================================================

NEXT_WEEK_PRIORITY_TEMPLATES = {
    "sleep-insomnia": {
        "easier": [  # 降低难度版本
            "尝试比平时早15分钟上床",
            "晚上提前半小时放下手机",
            "记录一下大概几点睡的",
        ],
        "keep": [  # 保持版本
            "继续固定起床时间",
            "继续保持晚上少看手机",
            "继续保持这个节奏",
        ],
        "new": [  # 新增版本
            "试试看睡前泡个脚",
            "注意一下午睡时间别太长",
        ]
    },
    "hypertension": {
        "easier": [
            "今天记得量一下血压",
            "做菜盐少放一点",
        ],
        "keep": [
            "继续按时吃药",
            "继续保持清淡饮食",
        ],
        "new": [
            "每天走走路",
        ]
    },
    "weight-loss": {
        "easier": [
            "每餐稍微少吃点",
            "记录一下今天吃了什么",
        ],
        "keep": [
            "继续保持现在的节奏",
        ],
        "new": [
            "试试看饭后站一会儿",
        ]
    }
}


def generate_next_week_priorities(
    canonical_id: str,
    keep_items: List[str],
    adjust_items: List[str],
    user_feedback: str,
    confidence: str = "low"
) -> Dict[str, Any]:
    """
    生成下一周优先事项
    
    规则：
    1. 不要和上周完全一样（必须有微调）
    2. 不要新增太多新事项
    3. 优先延续已建立的行为
    4. 如果用户执行困难，要降低难度
    """
    
    templates = NEXT_WEEK_PRIORITY_TEMPLATES.get(
        canonical_id, 
        NEXT_WEEK_PRIORITY_TEMPLATES["sleep-insomnia"]
    )
    
    # 分析置信度
    feedback_len = len(user_feedback)
    if feedback_len > 20:
        confidence = "medium"
    if feedback_len > 50:
        confidence = "high"
    
    user_feedback_lower = user_feedback.lower()
    
    # 生成最终优先事项
    final_items = []
    
    # 1. 先处理 adjust_items（降低难度版本）
    for item in adjust_items:
        if "起床" in item:
            # 起床相关的：推迟时间/降低要求
            adjusted = item.replace("7:00", "7:30").replace("固定", "尽量")
            if adjusted not in final_items:
                final_items.append(adjusted)
        elif "咖啡" in item or "饮食" in item:
            # 饮食相关的：降低要求
            if "不再" in item:
                adjusted = item.replace("不再", "尽量少")
            else:
                adjusted = item
            if adjusted not in final_items:
                final_items.append(adjusted)
        elif "手机" in item or "睡前" in item:
            # 睡前相关的：稍微调整
            if adjusted not in final_items:
                final_items.append(item)
    
    # 2. 再处理 keep_items（保持，但可以稍微强化）
    for item in keep_items:
        if item not in final_items:
            final_items.append(item)
    
    # 3. 如果还不够，用模板补充（基于置信度）
    if len(final_items) < 3:
        if confidence == "low":
            extras = templates.get("easier", [])[:2]
        else:
            extras = templates.get("keep", [])[:2]
        
        for item in extras:
            if item not in final_items and len(final_items) < 3:
                final_items.append(item)
    
    # 可选和记录项
    optional_items = templates.get("new", [])[:2]
    record_items = ["简单记录一下睡眠情况"]
    
    return {
        "key": final_items[:3],
        "optional": optional_items[:2],
        "record": record_items[:2]
    }


# ============================================================================
# Step 5: 复用 Phase 3 生成新提醒和反馈
# ============================================================================

def run_scheduler_for_next_week(
    user_id: str,
    user_name: str,
    channel_id: str,
    channel_type: str,
    mention_target: str,
    case_file_path: str,
    canonical_id: str,
    display_name: str,
    priority_items: Dict[str, Any]
) -> Dict[str, Any]:
    """
    复用 Phase 3 的干预调度逻辑
    """
    # 延迟导入避免循环依赖
    import sys
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    from intervention_scheduler import run_intervention_scheduler
    
    return run_intervention_scheduler(
        user_id=user_id,
        user_name=user_name,
        channel_id=channel_id,
        channel_type=channel_type,
        mention_target=mention_target,
        case_file_path=case_file_path,
        canonical_id=canonical_id,
        display_name=display_name,
        priority_items=priority_items
    )


# ============================================================================
# Step 6: 更新 case 文件
# ============================================================================

def update_case_for_week2(
    case_path: Path,
    week_number: int,
    weekly_summary: str,
    user_feedback: str,
    next_week_strategy: str,
    next_week_priorities: Dict[str, Any],
    scheduler_result: Dict[str, Any]
) -> bool:
    """
    更新 case 文件，追加 Week N 的记录
    """
    if not case_path.exists():
        print(f"[WARN] Case 文件不存在: {case_path}")
        return False
    
    try:
        content = case_path.read_text(encoding="utf-8")
        
        # 追加内容
        append_content = f"""

---
## Week {week_number}

### 执行情况总结
{weekly_summary}

### 用户反馈
{user_feedback}

### 下周调整思路
{next_week_strategy}

### 下周优先事项
"""
        
        for i, item in enumerate(next_week_priorities.get("key", []), 1):
            append_content += f"{i}. {item}\n"
        
        if next_week_priorities.get("optional"):
            append_content += "\n可选：\n"
            for item in next_week_priorities["optional"]:
                append_content += f"- {item}\n"
        
        append_content += "\n### 提醒安排\n"
        for r in scheduler_result.get("reminder_schedule", []):
            append_content += f"- {r.get('time')}: {r.get('message')[:50]}...\n"
        
        append_content += "\n### cron写入结果\n"
        append_content += f"- 创建提醒：{scheduler_result.get('cron_write_results', {}).get('created_reminders', 0)} 条\n"
        append_content += f"- 创建反馈：{scheduler_result.get('cron_write_results', {}).get('created_feedback', 0)} 条\n"
        append_content += f"- 时间点：{', '.join(scheduler_result.get('cron_write_results', {}).get('merged_times', []))}\n"
        
        content += append_content
        case_path.write_text(content, encoding="utf-8")
        return True
        
    except Exception as e:
        print(f"[ERROR] 更新 case 文件失败: {e}")
        return False


# ============================================================================
# 主入口函数
# ============================================================================

def run_weekly_review(
    user_id: str,
    problem_id: str,
    user_name: str,
    channel_id: str,
    channel_type: str,
    mention_target: str,
    user_feedback: str,
    last_week_items: List[str] = None,
    execution_logs: str = ""
) -> Dict[str, Any]:
    """
    完整的周复盘流程
    
    参数:
        user_id: 用户ID
        problem_id: 问题ID (e.g. "sleep-insomnia")
        user_name: 用户名
        channel_id: 渠道ID
        channel_type: 渠道类型
        mention_target: @目标
        user_feedback: 用户周复盘反馈
        last_week_items: 上周优先事项（可选）
        execution_logs: 执行记录（可选）
    
    返回:
        {
            "success": bool,
            "week_summary": "给用户的周总结",
            "next_week_strategy": "下周策略说明",
            "next_week_priorities": {...},
            "scheduler_result": {...},  # Phase 3 结果
        }
    """
    # 找最新 case 文件
    case_path = find_latest_case(user_id, problem_id)
    if not case_path:
        return {
            "success": False,
            "error": f"找不到用户 {user_id} 的 {problem_id} case 文件"
        }
    
    # 解析 case 内容
    case_data = parse_case_content(case_path)
    
    # 获取显示名
    display_names = {
        "sleep-insomnia": "失眠 / 睡眠改善",
        "hypertension": "高血压",
        "weight-loss": "减肥 / 体重控制"
    }
    display_name = display_names.get(problem_id, problem_id)
    
    # 如果没有提供上周事项，从 case 中尝试提取
    if not last_week_items:
        last_week_items = case_data.get("priority_items", [])
    if not last_week_items:
        # 默认模板
        last_week_items = [
            "固定起床时间",
            "晚上少看手机",
            "记录睡眠情况"
        ]
    
    # Step 1: 生成周复盘总结
    week_summary = build_weekly_summary(
        display_name=display_name,
        last_week_items=last_week_items,
        user_feedback=user_feedback,
        canonical_id=problem_id
    )
    
    # Step 2: 策略判断（内部）
    # 分类结果：
    # - fully_achieved: 完全做到
    # - partially_achieved: 部分做到/有时能做到
    # - difficult: 有困难
    # - not_tried: 未尝试
    fully_achieved = []
    partially_achieved = []
    difficult = []
    
    feedback_lower = user_feedback.lower()
    
    # 特殊处理："有时候能做到"不算完全做到
    feedback_lower_modified = feedback_lower.replace("有时候能", "").replace("有时候", "")
    
    for item in last_week_items:
        item_keywords = item.lower()
        
        # 检查是否有"难"相关的困难
        has_difficulty = any(k in feedback_lower for k in ["难", "困难", "做不到"])
        
        # 检查是否有明确的"做到"信号（排除"有时候"）
        has_success = any(k in feedback_lower_modified for k in ["好", "做到", "开始", "不错"])
        
        if has_difficulty and has_success:
            # 既有进展又有困难 -> 部分做到
            if item not in partially_achieved:
                partially_achieved.append(item)
        elif has_success:
            # 有进展 -> 完全做到
            if item not in fully_achieved:
                fully_achieved.append(item)
        elif has_difficulty:
            # 有困难 -> 需要调整
            if item not in difficult:
                difficult.append(item)
    
    # 合并为 keep/adjust/drop
    keep_items = fully_achieved
    adjust_items = partially_achieved + difficult
    
    # Step 3: 生成下周策略说明
    next_week_strategy = build_next_week_strategy(
        keep_items=keep_items,
        adjust_items=adjust_items,
        display_name=display_name
    )
    
    # Step 4: 生成下周优先事项
    confidence = "low" if len(user_feedback) < 30 else "medium"
    next_week_priorities = generate_next_week_priorities(
        canonical_id=problem_id,
        keep_items=keep_items,
        adjust_items=adjust_items,
        user_feedback=user_feedback,
        confidence=confidence
    )
    
    # Step 5: 复用 Phase 3 生成新提醒和反馈
    scheduler_result = run_scheduler_for_next_week(
        user_id=user_id,
        user_name=user_name,
        channel_id=channel_id,
        channel_type=channel_type,
        mention_target=mention_target,
        case_file_path=str(case_path),
        canonical_id=problem_id,
        display_name=display_name,
        priority_items=next_week_priorities
    )
    
    # Step 6: 更新 case 文件
    week_number = 2  # 简化的周数计算
    update_case_for_week2(
        case_path=case_path,
        week_number=week_number,
        weekly_summary=week_summary,
        user_feedback=user_feedback,
        next_week_strategy=next_week_strategy,
        next_week_priorities=next_week_priorities,
        scheduler_result=scheduler_result
    )
    
    return {
        "success": True,
        "week_summary": week_summary,
        "next_week_strategy": next_week_strategy,
        "next_week_priorities": next_week_priorities,
        "scheduler_result": scheduler_result,
        "case_file": str(case_path)
    }


# ============================================================================
# 测试入口
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4: 周复盘与下一周计划测试")
    print("=" * 60)
    
    result = run_weekly_review(
        user_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
        problem_id="sleep-insomnia",
        user_name="金",
        channel_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
        channel_type="direct",
        mention_target="@金",
        user_feedback="睡眠稍微好一点了，但还是会醒，晚上少看手机有时候能做到，早起比较难",
        last_week_items=[
            "每天固定在 7:00 起床",
            "下午 2 点后不再喝咖啡或浓茶",
            "晚上 22:30 后不再刷手机"
        ]
    )
    
    print(f"\n[success] {result['success']}")
    
    if result.get("week_summary"):
        print(f"\n【周总结】\n{result['week_summary']}")
    
    if result.get("next_week_strategy"):
        print(f"\n【下周策略】\n{result['next_week_strategy']}")
    
    if result.get("next_week_priorities"):
        print(f"\n【下周优先事项】")
        for i, item in enumerate(result['next_week_priorities'].get("key", []), 1):
            print(f"  {i}. {item}")
    
    if result.get("scheduler_result"):
        print(f"\n【提醒安排】")
        for r in result['scheduler_result'].get("reminder_schedule", []):
            print(f"  {r.get('time')}: {r.get('message')[:50]}...")
    
    print(f"\n[case文件] {result.get('case_file', '')}")
