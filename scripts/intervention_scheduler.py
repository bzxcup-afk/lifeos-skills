# -*- coding: utf-8 -*-
"""
问题导向干预 - Phase 3: 从优先事项到计划、提醒、反馈收集

在已生成优先事项后：
1. 生成本周调整计划（给用户看）
2. 生成提醒候选项
3. 读取当前已有 cron 任务
4. 合并提醒时间（优先药品提醒时间）
5. 写入干预计划到 JSON
6. 生成反馈收集任务
7. 更新 case 文件

配置项（可调）：
- MERGE_TIME_DIFF_MINUTES: 时间差 <= 此值则合并（1小时）
- MAX_DAILY_REMINDERS: 每天最大主动提醒数
- FEEDBACK_DELAY_MINUTES: 反馈比主提醒晚几分钟
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# ============================================================================
# 配置
# ============================================================================

SKILL_DIR = Path(r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main")
MEDICINE_DIR = SKILL_DIR / "medicine"

# 可配置参数
MERGE_TIME_DIFF_MINUTES = 60  # 时间差 <= 此值则合并（1小时）
MAX_DAILY_REMINDERS = 3      # 每天最大主动提醒数
FEEDBACK_DELAY_MINUTES = 10  # 反馈比主提醒晚几分钟

# 时间槽到小时的映射（参考 check_medicine_reminders.py）
TIME_SLOTS = {
    '起床后': 7,
    '早餐前': 7,
    '早餐后': 8,
    '午餐前': 11,
    '午餐后': 12,
    '晚餐前': 17,
    '晚餐后': 18,
    '睡前': 20
}

# 反向映射：小时 -> 时间槽
HOUR_TO_SLOT = {v: k for k, v in TIME_SLOTS.items()}

# ============================================================================
# 数据文件路径
# ============================================================================

def get_medicine_plans_file() -> Path:
    return MEDICINE_DIR / "medicine_plans.json"

def get_intervention_plans_file() -> Path:
    return MEDICINE_DIR / "intervention_plans.json"

def get_cases_dir() -> Path:
    return SKILL_DIR / "cases"


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
# Step 1: 生成给用户的调整计划
# ============================================================================

def build_user_plan_message(
    priority_items: Dict[str, Any],
    display_name: str = ""
) -> str:
    """
    把优先事项整理成用户能看懂的本周调整计划

    返回给用户看的调整计划文本
    """
    # 提取重点和可选
    key_items = []
    optional_items = []
    record_items = []

    # 从 priority_items 解析
    # 假设格式是：
    # priority_items = {
    #     "key": ["item1", "item2", "item3"],
    #     "optional": ["item1", "item2"],
    #     "record": ["item1", "item2"]
    # }

    if isinstance(priority_items, dict):
        key_items = priority_items.get("key", [])
        optional_items = priority_items.get("optional", [])
        record_items = priority_items.get("record", [])
    elif isinstance(priority_items, list):
        # 如果是纯文本，尝试解析
        lines = str(priority_items).split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if '【本周重点' in line or '1.' in line or '2.' in line or '3.' in line:
                key_items.append(line)
            elif '【可以尝试' in line or '-' in line:
                optional_items.append(line)

    lines = []
    lines.append("【这周我们先这样调整】")
    lines.append("")
    lines.append("这周先不求一下子改很多，我们先抓最关键的几件事：")
    lines.append("")

    if key_items:
        for i, item in enumerate(key_items[:3], 1):
            # 清理格式
            item = item.strip().lstrip('0123456789.、 ')
            lines.append(f"{i}. {item}")
    else:
        lines.append("1. 先从记录开始，了解现状")
        lines.append("2. 保持现有习惯，不做太大改变")
        lines.append("3. 观察一周再看下一步")

    lines.append("")

    if optional_items:
        lines.append("如果做得动，还可以试着做：")
        for item in optional_items[:2]:
            item = item.strip().lstrip('-、 ')
            lines.append(f"- {item}")
        lines.append("")

    lines.append("我会在几个关键时间点提醒你，不会提醒太多。")
    lines.append("到这周后面，我也会简单问你一下执行情况和感受，再一起调整下一步。")

    return "\n".join(lines)


# ============================================================================
# Step 2: 生成提醒候选项
# ============================================================================

REMINDER_TEMPLATES = {
    "sleep-insomnia": {
        "morning": {
            "title": "早间提醒",
            "default_time": "07:00",
            "items": ["起床", "如果方便的话晒太阳"]
        },
        "afternoon": {
            "title": "下午提醒",
            "default_time": "14:00",
            "items": ["之后不要再喝咖啡或浓茶"]
        },
        "evening": {
            "title": "晚间提醒",
            "default_time": "21:00",
            "items": ["减少看手机，慢慢准备休息"]
        }
    },
    "hypertension": {
        "morning": {
            "title": "早间提醒",
            "default_time": "07:00",
            "items": ["记得按时吃药", "适当活动"]
        },
        "noon": {
            "title": "午间提醒",
            "default_time": "12:00",
            "items": ["饮食清淡一些"]
        },
        "evening": {
            "title": "晚间提醒",
            "default_time": "21:00",
            "items": ["记得按时吃药", "减少盐分摄入"]
        }
    },
    "weight-loss": {
        "morning": {
            "title": "早间提醒",
            "default_time": "07:00",
            "items": ["记得吃早餐", "适当活动"]
        },
        "noon": {
            "title": "午间提醒",
            "default_time": "12:00",
            "items": ["控制饭量", "少吃油腻"]
        },
        "evening": {
            "title": "晚间提醒",
            "default_time": "18:00",
            "items": ["晚餐吃少一点", "饭后散步"]
        }
    }
}


def generate_reminder_candidates(
    canonical_id: str,
    priority_items: Dict[str, Any],
    user_data: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    生成提醒候选项

    返回:
        [
            {
                "title": "早间提醒",
                "suggested_time": "07:00",
                "items": ["起床", "晒太阳"],
                "source": ["sleep-insomnia"]
            },
            ...
        ]
    """
    candidates = []

    # 获取对应问题的模板
    templates = REMINDER_TEMPLATES.get(canonical_id, REMINDER_TEMPLATES["sleep-insomnia"])

    for slot_name, template in templates.items():
        candidates.append({
            "title": template["title"],
            "suggested_time": template["default_time"],
            "items": template["items"].copy(),
            "source": [canonical_id]
        })

    return candidates


# ============================================================================
# Step 3: 读取当前已有 cron 任务
# ============================================================================

def load_existing_tasks(user_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    读取当前用户的所有 cron 任务

    返回按时间分组的任务字典
    {
        "07:00": [...],
        "21:00": [...],
    }
    """
    # 读取药品提醒
    medicine_file = get_medicine_plans_file()
    medicine_plans = load_json(medicine_file, [])

    # 读取干预提醒
    intervention_file = get_intervention_plans_file()
    intervention_plans = load_json(intervention_file, [])

    # 合并
    all_tasks = []

    for plan in medicine_plans:
        if plan.get('user_id') == user_id and plan.get('active', True):
            all_tasks.append({
                "task_type": "medication",
                "id": plan.get('id'),
                "time_slot": plan.get('time_slot'),
                "time": _slot_to_time(plan.get('time_slot')),
                "drug_name": plan.get('drug_name'),
                "channel_id": plan.get('channel_id'),
                "channel_type": plan.get('channel_type'),
                "mention_target": plan.get('mention_target'),
                "user_name": plan.get('user_name'),
                "original": plan
            })

    for plan in intervention_plans:
        if plan.get('user_id') == user_id and plan.get('active', True):
            all_tasks.append({
                "task_type": "intervention",
                "id": plan.get('id'),
                "time": plan.get('time'),
                "reminder_title": plan.get('title'),
                "items": plan.get('items', []),
                "channel_id": plan.get('channel_id'),
                "channel_type": plan.get('channel_type'),
                "mention_target": plan.get('mention_target'),
                "user_name": plan.get('user_name'),
                "original": plan
            })

    # 按时间分组
    grouped = {}
    for task in all_tasks:
        time = task.get('time') or task.get('time_slot')
        if time:
            # 标准化时间格式
            if ':' not in str(time):
                time = _slot_to_time(time)
            if time not in grouped:
                grouped[time] = []
            grouped[time].append(task)

    return grouped


def _slot_to_time(slot: str) -> str:
    """时间槽转时间字符串"""
    if not slot:
        return ""
    hour = TIME_SLOTS.get(slot)
    if hour is not None:
        return f"{hour:02d}:00"
    return str(slot)


# ============================================================================
# Step 4: 合并提醒时间
# ============================================================================

def merge_reminders(
    existing_tasks: Dict[str, List[Dict[str, Any]]],
    new_candidates: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    将新提醒合并到已有时间点

    合并规则：
    1. 时间差 <= MERGE_TIME_DIFF_MINUTES 必须合并
    2. 药品提醒时间优先级最高
    3. 每天不超过 MAX_DAILY_REMINDERS 条
    """
    merged = []

    # 已有时间点
    existing_times = set(existing_tasks.keys())

    for candidate in new_candidates:
        suggested_time = candidate.get("suggested_time", "08:00")
        candidate_hour = int(suggested_time.split(":")[0])

        # 找最接近的已有时间点
        best_match = None
        best_diff = float('inf')

        for exist_time in existing_times:
            exist_hour = int(exist_time.split(":")[0])
            diff = abs(exist_hour * 60 + int(exist_time.split(":")[1]) -
                       candidate_hour * 60)
            if diff <= MERGE_TIME_DIFF_MINUTES and diff < best_diff:
                best_match = exist_time
                best_diff = diff

        if best_match:
            # 合并到已有时间点
            candidate["merged_time"] = best_match
            candidate["merged_with"] = existing_tasks[best_match]
        else:
            # 需要新时间点
            candidate["merged_time"] = suggested_time
            candidate["merged_with"] = []

        merged.append(candidate)

    # 检查每天提醒数
    time_count = {}
    for m in merged:
        t = m.get("merged_time", "08:00")
        time_count[t] = time_count.get(t, 0) + 1

    # 如果某时间点超过 MAX_DAILY_REMINDERS，标记需要拆分
    for m in merged:
        t = m.get("merged_time", "08:00")
        if time_count[t] > MAX_DAILY_REMINDERS:
            m["exceed_max"] = True

    return merged


def build_merged_reminder_messages(
    merged: List[Dict[str, Any]],
    existing_tasks: Dict[str, List[Dict[str, Any]]],
    daily_feedback_message: str = None,
    daily_feedback_time: str = "08:00"
) -> List[Dict[str, Any]]:
    """
    构建合并后的提醒消息

    参数:
        merged: 合并后的提醒候选
        existing_tasks: 已有任务
        daily_feedback_message: 每日轻反馈内容（会合并到晚间提醒）

    返回:
        [
            {
                "time": "07:00",
                "message": "@用户 早上提醒你一下：...",
                "channel_id": "...",
                "channel_type": "...",
                "mention_target": "@金",
                "sources": ["medication", "sleep-insomnia"]
            },
            ...
        ]
    """
    messages = []

    # 按时间分组
    time_groups = {}
    for m in merged:
        t = m.get("merged_time", "08:00")
        if t not in time_groups:
            time_groups[t] = []
        time_groups[t].append(m)

    for time_str, group in time_groups.items():
        # 获取渠道信息（从第一个任务的已有任务中获取）
        channel_info = {
            "channel_id": None,
            "channel_type": None,
            "mention_target": None,
            "user_name": None
        }

        # 优先从药品提醒获取渠道
        for task_list in existing_tasks.values():
            for task in task_list:
                if task.get('task_type') == 'medication':
                    channel_info = {
                        "channel_id": task.get('channel_id'),
                        "channel_type": task.get('channel_type'),
                        "mention_target": task.get('mention_target'),
                        "user_name": task.get('user_name')
                    }
                    break

        # 如果没有药品提醒，从干预提醒获取
        if not channel_info["channel_id"]:
            for task_list in existing_tasks.values():
                for task in task_list:
                    if task.get('task_type') == 'intervention':
                        channel_info = {
                            "channel_id": task.get('channel_id'),
                            "channel_type": task.get('channel_type'),
                            "mention_target": task.get('mention_target'),
                            "user_name": task.get('user_name')
                        }
                        break

        # 构建消息
        message_parts = []
        sources = []

        # 只获取当前时间段的已有任务内容
        current_time_tasks = existing_tasks.get(time_str, [])

        # 添加当前时间段已有任务的内容（药品）
        for task in current_time_tasks:
            if task.get('task_type') == 'medication':
                message_parts.append(f"记得按时吃{task.get('drug_name', '药')}")
                sources.append("medication")

        # 添加新提醒内容
        for item in group:
            if item.get("title"):
                sources.append(item.get("source", [item.get("merged_with", [])]))
            for itm in item.get("items", []):
                message_parts.append(itm)

        # 构建最终消息
        if 5 <= int(time_str.split(":")[0]) < 12:
            greeting = "早上"
        elif 12 <= int(time_str.split(":")[0]) < 18:
            greeting = "下午"
        else:
            greeting = "晚上"

        mention = channel_info.get("mention_target", "")
        message = f"{mention} {greeting}提醒你一下：{'，'.join(message_parts)}"

        # 如果是晚间提醒，并且有每日轻反馈内容，合并进去
        # 如果是早间提醒（5-12点），合并每日反馈
        hour = int(time_str.split(":")[0])
        if 5 <= hour <= 12 and daily_feedback_message:
            message = f"{message} {daily_feedback_message}"

        messages.append({
            "time": time_str,
            "message": message.strip(),
            "channel_id": channel_info.get("channel_id"),
            "channel_type": channel_info.get("channel_type"),
            "mention_target": channel_info.get("mention_target"),
            "user_name": channel_info.get("user_name"),
            "sources": list(set([s if isinstance(s, str) else str(s) for s in sources]))
        })

    return messages


# ============================================================================
# Step 5: 写入干预计划
# ============================================================================

def write_intervention_plans(
    user_id: str,
    user_name: str,
    channel_id: str,
    channel_type: str,
    mention_target: str,
    case_id: str,
    canonical_id: str,
    merged_messages: List[Dict[str, Any]],
    priority_items: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    将干预计划写入 JSON 文件
    """
    intervention_file = get_intervention_plans_file()
    existing = load_json(intervention_file, [])

    # 找到该用户的同类问题旧提醒，标记为非活跃
    for plan in existing:
        if (plan.get('user_id') == user_id and
            plan.get('problem_id') == canonical_id and
            plan.get('active', True)):
            plan['active'] = False
            plan['superseded_by'] = case_id
            plan['superseded_at'] = datetime.now().isoformat()

    # 生成新计划
    new_plans = []
    for msg in merged_messages:
        plan = {
            "id": f"int_{datetime.now().strftime('%Y%m%d%H%M%S')}_{canonical_id[:4]}",
            "user_id": user_id,
            "user_name": user_name,
            "problem_id": canonical_id,
            "case_id": case_id,
            "title": msg.get("sources", [canonical_id])[0] if msg.get("sources") else canonical_id,
            "time": msg.get("time"),
            "repeat": "daily",
            "message": msg.get("message"),
            "channel_id": channel_id,
            "channel_type": channel_type,
            "mention_target": mention_target,
            "sources": msg.get("sources", []),
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        new_plans.append(plan)
        existing.append(plan)

    # 写入
    if save_json(intervention_file, existing):
        return new_plans
    return []


# ============================================================================
# Step 6 & 7: 生成反馈收集任务
# ============================================================================

FEEDBACK_TEMPLATES = {
    "sleep-insomnia": {
        "morning": {
            "time": "08:00",
            "message": "昨晚睡得怎么样？大概几点睡、几点起的？"
        },
        "weekly": {
            "time": "周日 21:00",
            "message": "这周睡眠有没有好一点？"
        }
    },
    "hypertension": {
        "morning": {
            "time": "08:00",
            "message": "今早血压怎么样？"
        },
        "weekly": {
            "time": "周日 21:00",
            "message": "这周血压控制得怎么样？"
        }
    },
    "weight-loss": {
        "morning": {
            "time": "08:00",
            "message": "今早体重多少？"
        },
        "weekly": {
            "time": "周日 21:00",
            "message": "这周体重有变化吗？"
        }
    }
}


def generate_feedback_prompt(
    canonical_id: str,
    display_name: str,
    priority_items: Dict[str, Any],
    reminder_times: List[str]
) -> str:
    """
    生成让LLM判断反馈收集内容和时间的Prompt

    注意：第一版使用模板，第二版可升级为LLM
    """
    template = FEEDBACK_TEMPLATES.get(canonical_id, FEEDBACK_TEMPLATES["sleep-insomnia"])

    prompt = f"""你是一个问题干预反馈设计助手。

当前问题：{display_name}
问题优先事项：{priority_items}
已有提醒时间点：{reminder_times}

你的任务是设计反馈收集任务：
1. 每天收集什么反馈？
2. 每天在什么时间收集？

规则：
- 睡眠问题应在早上收集昨晚的情况
- 高血压应在早上收集刚测的血压
- 体重问题应在早上收集体重
- 反馈要简单，一句话即可

输出格式：
{{
  "daily_feedback": {{
    "time": "08:00",
    "message": "反馈内容"
  }},
  "weekly_feedback": {{
    "time": "周日 21:00",
    "message": "周复盘内容"
  }}
}}"""

    return prompt


def generate_feedback_tasks(
    user_id: str,
    user_name: str,
    channel_id: str,
    channel_type: str,
    mention_target: str,
    case_id: str,
    canonical_id: str,
    priority_items: Dict[str, Any],
    reminder_times: List[str]
) -> List[Dict[str, Any]]:
    """
    生成反馈收集任务

    规则：
    - 根据问题类型确定反馈内容和时间
    - 睡眠问题：早上问昨晚情况
    - 高血压：早上问血压
    - 体重：早上问体重
    - 每周1个周复盘
    """
    feedback_tasks = []
    daily_feedback_message = None

    # 获取问题对应的反馈模板
    template = FEEDBACK_TEMPLATES.get(canonical_id, FEEDBACK_TEMPLATES["sleep-insomnia"])

    # 每日轻反馈时间（早上，问昨晚情况）
    daily_time = template.get("morning", {}).get("time", "08:00")
    daily_message = template.get("morning", {}).get("message", "今天怎么样？")

    # 周复盘（每周日晚上）
    # 每日轻反馈：合并到早上提醒里
    # 返回给调用方，让它合并到早间提醒消息中
    daily_feedback_message = daily_message

    # 周复盘（每周日晚上）
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    next_sunday = today + timedelta(days=days_until_sunday)
    review_date = next_sunday.strftime("%Y-%m-%d")

    weekly_time = template.get("weekly", {}).get("time", "周日 21:00").split(" ")[1] if " " in template.get("weekly", {}).get("time", "周日 21:00") else "21:00"
    weekly_message = template.get("weekly", {}).get("message", "这周情况怎么样？")

    weekly_review = {
        "id": f"fb_{datetime.now().strftime('%Y%m%d%H%M%S')}_weekly",
        "task_type": "intervention_weekly_review",
        "user_id": user_id,
        "user_name": user_name,
        "problem_id": canonical_id,
        "case_id": case_id,
        "scheduled_date": review_date,
        "time": weekly_time,
        "repeat": "weekly",
        "message": f"{mention_target} {weekly_message}",
        "week_index": 1,
        "channel_id": channel_id,
        "channel_type": channel_type,
        "mention_target": mention_target,
        "active": True,
        "created_at": datetime.now().isoformat()
    }
    feedback_tasks.append(weekly_review)

    return feedback_tasks, daily_feedback_message, daily_time


def write_feedback_tasks(
    feedback_tasks: List[Dict[str, Any]]
) -> bool:
    """写入反馈任务到 JSON"""
    intervention_file = get_intervention_plans_file()
    existing = load_json(intervention_file, [])

    for task in feedback_tasks:
        existing.append(task)

    return save_json(intervention_file, existing)


# ============================================================================
# Step 8: 更新 case 文件
# ============================================================================

def update_case_file(
    case_file_path: Path,
    user_plan: str,
    reminder_schedule: List[Dict[str, Any]],
    feedback_schedule: List[Dict[str, Any]],
    cron_write_results: Dict[str, Any]
) -> bool:
    """
    更新 case 文件，追加本周计划、提醒、反馈收集安排
    """
    if not case_file_path.exists():
        print(f"[WARN] Case 文件不存在: {case_file_path}")
        return False

    try:
        content = case_file_path.read_text(encoding="utf-8")

        # 追加内容
        append_content = f"""

## 本周调整计划
{user_plan}

## 提醒安排
"""

        for r in reminder_schedule:
            append_content += f"- {r.get('time')} {r.get('title', '提醒')}：{r.get('message', '')[:50]}...\n"

        append_content += "\n## 反馈收集安排\n"
        for f in feedback_schedule:
            fb_type = "每日轻反馈" if "daily" in f.get('id', '') else "周复盘反馈"
            append_content += f"- {fb_type}：{f.get('time', f.get('scheduled_date'))}\n"

        append_content += "\n## cron任务写入结果\n"
        append_content += f"- 已创建提醒：{cron_write_results.get('created_reminders', 0)} 条\n"
        append_content += f"- 已创建反馈：{cron_write_results.get('created_feedback', 0)} 条\n"
        append_content += f"- 已合并时间点：{', '.join(cron_write_results.get('merged_times', []))}\n"

        content += append_content

        case_file_path.write_text(content, encoding="utf-8")
        return True

    except Exception as e:
        print(f"[ERROR] 更新 case 文件失败: {e}")
        return False


# ============================================================================
# 主入口函数
# ============================================================================

def run_intervention_scheduler(
    user_id: str,
    user_name: str,
    channel_id: str,
    channel_type: str,
    mention_target: str,
    case_file_path: str,
    canonical_id: str,
    display_name: str,
    priority_items: Dict[str, Any],
    user_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    完整的干预调度流程

    参数:
        user_id: 用户ID
        user_name: 用户名
        channel_id: 渠道ID（群ID或用户open_id）
        channel_type: "group" 或 "direct"
        mention_target: @目标
        case_file_path: case文件路径
        canonical_id: 问题ID
        display_name: 问题显示名
        priority_items: 优先事项
        user_data: 用户已有数据（可选）

    返回:
        {
            "success": bool,
            "user_plan": "给用户看的调整计划",
            "reminder_schedule": [...],  # 提醒安排
            "feedback_schedule": [...],   # 反馈安排
            "cron_write_results": {...}, # cron写入结果
        }
    """
    # Step 1: 生成给用户的调整计划
    user_plan = build_user_plan_message(priority_items, display_name)

    # Step 2: 生成提醒候选项
    reminder_candidates = generate_reminder_candidates(canonical_id, priority_items, user_data)

    # Step 3: 读取当前已有 cron 任务
    existing_tasks = load_existing_tasks(user_id)

    # Step 4: 合并提醒时间
    merged = merge_reminders(existing_tasks, reminder_candidates)

    # 生成 case_id（提前定义，供后续使用）
    case_id = f"case_{canonical_id}_{datetime.now().strftime('%Y%m%d')}"

    # Step 6: 先生成反馈任务（获取每日轻反馈内容）
    feedback_result = generate_feedback_tasks(
        user_id=user_id,
        user_name=user_name,
        channel_id=channel_id,
        channel_type=channel_type,
        mention_target=mention_target,
        case_id=case_id,
        canonical_id=canonical_id,
        priority_items=priority_items,
        reminder_times=[c.get("suggested_time") for c in reminder_candidates]
    )
    feedback_tasks, daily_feedback_message, daily_feedback_time = feedback_result

    # 构建合并后的提醒消息（将每日轻反馈合并到早间提醒）
    merged_messages = build_merged_reminder_messages(merged, existing_tasks, daily_feedback_message, daily_feedback_time)

    # Step 5: 写入干预计划
    new_plans = write_intervention_plans(
        user_id=user_id,
        user_name=user_name,
        channel_id=channel_id,
        channel_type=channel_type,
        mention_target=mention_target,
        case_id=case_id,
        canonical_id=canonical_id,
        merged_messages=merged_messages,
        priority_items=priority_items
    )

    # Step 7: 写入反馈任务（只有周复盘）
    write_feedback_tasks(feedback_tasks)

    # Step 8: 更新 case 文件
    cron_results = {
        "created_reminders": len(new_plans),
        "created_feedback": len(feedback_tasks),
        "merged_times": [m.get("time") for m in merged_messages]
    }

    if case_file_path:
        case_path = Path(case_file_path)
        update_case_file(
            case_path,
            user_plan,
            [
                {"time": m.get("time"), "title": m.get("sources", [canonical_id])[0], "message": m.get("message")}
                for m in merged_messages
            ],
            [
                {"id": f.get("id"), "time": f.get("time") or f.get("scheduled_date"), "message": f.get("message")}
                for f in feedback_tasks
            ],
            cron_results
        )

    return {
        "success": True,
        "user_plan": user_plan,
        "reminder_schedule": [
            {"time": m.get("time"), "message": m.get("message")}
            for m in merged_messages
        ],
        "feedback_schedule": [
            {"id": f.get("id"), "time": f.get("time") or f.get("scheduled_date"), "message": f.get("message")}
            for f in feedback_tasks
        ],
        "cron_write_results": cron_results
    }


# ============================================================================
# 测试入口
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 3: 干预调度测试")
    print("=" * 60)

    # 模拟优先事项
    priority_items = {
        "key": [
            "每天固定在 7:00 起床",
            "下午 2 点后不再喝咖啡或浓茶",
            "晚上 22:30 后不再刷手机，开始准备睡觉"
        ],
        "optional": [
            "晚饭后散步 15 分钟"
        ],
        "record": [
            "实际睡觉时间",
            "实际起床时间",
            "夜间醒来次数"
        ]
    }

    result = run_intervention_scheduler(
        user_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
        user_name="金",
        channel_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
        channel_type="direct",
        mention_target="@金",
        case_file_path=str(SKILL_DIR / "cases" / "sleep-insomnia" / "case-ou_fde56bd8d48eca22b3d57ab990ee4f02-20260405.md"),
        canonical_id="sleep-insomnia",
        display_name="失眠 / 睡眠改善",
        priority_items=priority_items
    )

    print(f"\n[success] {result['success']}")
    print(f"\n【给用户的调整计划】\n{result['user_plan']}")
    print(f"\n【提醒安排】")
    for r in result.get("reminder_schedule", []):
        print(f"  {r.get('time')}: {r.get('message')[:50]}...")
    print(f"\n【反馈安排】")
    for f in result.get("feedback_schedule", []):
        print(f"  {f.get('time')}: {f.get('message')[:40]}...")
    print(f"\n【cron写入结果】")
    print(f"  {result.get('cron_write_results')}")
    print()
