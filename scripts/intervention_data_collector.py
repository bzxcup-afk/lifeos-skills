# -*- coding: utf-8 -*-
"""
问题导向干预 - 资料补全与优先事项生成模块 v1.0

在干预入口之后，继续：
1. 读取用户已有数据
2. 生成关键问题并向用户提问
3. 接收回答并结构化
4. 生成优先事项
5. 形成case文件

第一版只实现 sleep-insomnia
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# ============================================================================
# 路径配置
# ============================================================================

SKILL_DIR = Path(r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main")
KNOWLEDGE_DIR = SKILL_DIR / "knowledge" / "problems"
CASES_DIR = SKILL_DIR / "cases"

# ============================================================================
# 依赖模块
# ============================================================================

# 延迟导入，避免循环依赖
_intervention_intake = None

def get_intervention_intake():
    global _intervention_intake
    if _intervention_intake is None:
        import sys
        sys.path.insert(0, str(SKILL_DIR / "scripts"))
        import intervention_intake
        _intervention_intake = intervention_intake
    return _intervention_intake


# ============================================================================
# Step 2: 提取用户已有数据
# ============================================================================

def get_user_data_dir() -> Path:
    """获取用户数据目录"""
    return SKILL_DIR / "data"


def load_user_profile(profile_id: str) -> Dict[str, Any]:
    """读取用户资料表"""
    import sys
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    try:
        from db import query_one
        row = query_one(
            "SELECT * FROM profiles WHERE profile_id = ?",
            (profile_id,)
        )
        if row:
            return dict(row)
    except Exception as e:
        print(f"[WARN] Failed to load profile: {e}")
    return {}


def load_user_preferences(profile_id: str) -> Dict[str, Any]:
    """读取用户偏好表"""
    import sys
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    try:
        from db import query_one
        row = query_one(
            "SELECT * FROM user_preferences WHERE profile_id = ?",
            (profile_id,)
        )
        if row:
            return dict(row)
    except Exception as e:
        print(f"[WARN] Failed to load preferences: {e}")
    return {}


def load_recent_daily_logs(profile_id: str, days: int = 14) -> List[Dict[str, Any]]:
    """读取最近的每日记录"""
    import sys
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    try:
        from db import query_many
        rows = query_many(
            """SELECT * FROM daily_log 
               WHERE profile_id = ? 
               ORDER BY date DESC LIMIT ?""",
            (profile_id, days)
        )
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[WARN] Failed to load daily logs: {e}")
    return []


def load_medication_records(profile_id: str) -> List[Dict[str, Any]]:
    """读取药品记录"""
    import sys
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    try:
        from db import query_many
        rows = query_many(
            """SELECT * FROM medication_supplement_list 
               WHERE profile_id = ?""",
            (profile_id,)
        )
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[WARN] Failed to load medication records: {e}")
    return []


def load_recent_medical_records(profile_id: str, days: int = 90) -> List[Dict[str, Any]]:
    """读取最近的医疗记录"""
    import sys
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    try:
        from db import query_many
        rows = query_many(
            """SELECT * FROM medical_records 
               WHERE profile_id = ? 
               ORDER BY record_date DESC LIMIT 20""",
            (profile_id,)
        )
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[WARN] Failed to load medical records: {e}")
    return []


def build_user_known_data_summary(
    profile_id: str,
    canonical_id: str
) -> Dict[str, Any]:
    """
    构建用户已有信息摘要

    根据不同的问题类型，提取相关的已有数据
    """
    summary = {
        "profile": {},
        "preferences": {},
        "relevant_history": {},
        "medication": []
    }

    # 加载 profile
    profile = load_user_profile(profile_id)
    if profile:
        # 计算年龄
        age = None
        if profile.get("birth_date"):
            try:
                bd = datetime.strptime(profile["birth_date"], "%Y-%m-%d")
                age = (datetime.now() - bd).days // 365
            except:
                pass

        summary["profile"] = {
            "age": age,
            "gender": profile.get("gender"),
            "height_cm": profile.get("height_cm"),
            "baseline_weight_kg": profile.get("baseline_weight_kg"),
            "chronic_conditions": profile.get("chronic_conditions"),
            "long_term_goal": profile.get("long_term_goal"),
            "health_constraints": profile.get("health_constraints"),
        }

    # 加载偏好
    prefs = load_user_preferences(profile_id)
    if prefs:
        summary["preferences"] = {
            "sports_likes": prefs.get("sports_likes"),
            "sports_dislikes": prefs.get("sports_dislikes"),
            "lifestyle_constraints": prefs.get("lifestyle_constraints"),
            "execution_preferences": prefs.get("execution_preferences"),
            "notes": prefs.get("notes"),
        }

    # 根据问题类型加载相关历史
    if canonical_id == "sleep-insomnia":
        # 加载睡眠相关记录
        logs = load_recent_daily_logs(profile_id, days=14)
        sleep_logs = []
        for log in logs:
            if log.get("sleep_hours"):
                sleep_logs.append({
                    "date": log.get("date"),
                    "sleep_hours": log.get("sleep_hours"),
                    "sleep_quality": log.get("sleep_quality"),
                    "fatigue_score": log.get("fatigue_score"),
                })
        summary["relevant_history"]["sleep_logs"] = sleep_logs

        # 加载医疗记录中的睡眠相关
        med_records = load_recent_medical_records(profile_id, days=90)
        sleep_med = []
        for rec in med_records:
            tags = rec.get("tags", "")
            if "睡眠" in tags or "睡眠" in str(rec.get("complaint_or_reason", "")):
                sleep_med.append({
                    "date": rec.get("record_date"),
                    "type": rec.get("record_type"),
                    "complaint": rec.get("complaint_or_reason"),
                    "diagnosis": rec.get("diagnosis"),
                })
        summary["relevant_history"]["sleep_medical"] = sleep_med

    elif canonical_id == "hypertension":
        # 加载血压相关记录
        logs = load_recent_daily_logs(profile_id, days=14)
        summary["relevant_history"]["recent_logs"] = [
            {"date": log.get("date"), "notes": log.get("body_status_notes")}
            for log in logs if log.get("body_status_notes")
        ]

        med_records = load_recent_medical_records(profile_id, days=90)
        bp_med = []
        for rec in med_records:
            tags = rec.get("tags", "")
            if "心血管" in tags or "血压" in str(rec.get("complaint_or_reason", "")):
                bp_med.append({
                    "date": rec.get("record_date"),
                    "type": rec.get("record_type"),
                    "complaint": rec.get("complaint_or_reason"),
                    "metrics": rec.get("key_metrics_json"),
                })
        summary["relevant_history"]["bp_medical"] = bp_med

    elif canonical_id == "weight-loss":
        # 加载体重相关记录
        logs = load_recent_daily_logs(profile_id, days=30)
        weight_logs = []
        for log in logs:
            if log.get("weight_kg"):
                weight_logs.append({
                    "date": log.get("date"),
                    "weight_kg": log.get("weight_kg"),
                    "diet_status": log.get("diet_status"),
                })
        summary["relevant_history"]["weight_logs"] = weight_logs

    # 加载药品
    meds = load_medication_records(profile_id)
    if meds:
        summary["medication"] = [
            {
                "name": m.get("medication_name") or m.get("name"),
                "dosage": m.get("dosage"),
                "frequency": m.get("frequency"),
                "purpose": m.get("purpose"),
            }
            for m in meds
        ]

    return summary


def format_user_known_data_for_prompt(summary: Dict[str, Any], canonical_id: str) -> str:
    """
    将用户已有数据格式化为prompt友好格式
    """
    lines = []
    lines.append("【用户基本信息】")
    p = summary.get("profile", {})
    if p.get("age"):
        lines.append(f"- 年龄：{p['age']}岁")
    if p.get("gender"):
        lines.append(f"- 性别：{p['gender']}")
    if p.get("height_cm"):
        lines.append(f"- 身高：{p['height_cm']}cm")
    if p.get("baseline_weight_kg"):
        lines.append(f"- 基线体重：{p['baseline_weight_kg']}kg")
    if p.get("chronic_conditions"):
        lines.append(f"- 慢性病：{p['chronic_conditions']}")
    if p.get("health_constraints"):
        lines.append(f"- 健康限制：{p['health_constraints']}")

    prefs = summary.get("preferences", {})
    if prefs.get("sports_likes"):
        lines.append(f"- 喜欢的运动：{prefs['sports_likes']}")
    if prefs.get("sports_dislikes"):
        lines.append(f"- 不喜欢的运动：{prefs['sports_dislikes']}")
    if prefs.get("lifestyle_constraints"):
        lines.append(f"- 生活习惯：{prefs['lifestyle_constraints']}")
    if prefs.get("execution_preferences"):
        lines.append(f"- 执行偏好：{prefs['execution_preferences']}")

    meds = summary.get("medication", [])
    if meds:
        lines.append("\n【用药情况】")
        for m in meds:
            name = m.get("name", "")
            dosage = m.get("dosage", "")
            freq = m.get("frequency", "")
            lines.append(f"- {name} {dosage} {freq}".strip())

    # 问题相关历史
    hist = summary.get("relevant_history", {})

    if canonical_id == "sleep-insomnia":
        sleep_logs = hist.get("sleep_logs", [])
        if sleep_logs:
            lines.append("\n【近期睡眠记录】")
            for log in sleep_logs[:7]:  # 只显示最近7条
                date = log.get("date", "")
                hours = log.get("sleep_hours", "")
                quality = log.get("sleep_quality", "")
                lines.append(f"- {date}: 睡{hours}小时, 质量{quality}")

    elif canonical_id == "weight-loss":
        weight_logs = hist.get("weight_logs", [])
        if weight_logs:
            lines.append("\n【近期体重记录】")
            for log in weight_logs[:7]:
                date = log.get("date", "")
                weight = log.get("weight_kg", "")
                diet = log.get("diet_status", "")
                lines.append(f"- {date}: {weight}kg, 饮食{diet}")

    return "\n".join(lines) if lines else "暂无详细记录"


# ============================================================================
# Step 3: 生成提问 Prompt
# ============================================================================

def generate_missing_questions_prompt(
    canonical_id: str,
    display_name: str,
    knowledge_content: str,
    user_known_data: str
) -> str:
    """
    生成让LLM判断缺失问题的Prompt
    """
    prompt = f"""你是一个问题干预流程助手。

当前问题：{display_name}

问题知识摘要：
{knowledge_content[:2000]}

用户已有信息：
{user_known_data}

你的任务是：
根据当前问题知识和用户已有信息，找出"为了继续生成干预优先事项，还缺失的最关键问题"。

要求：
1. 只返回 3-4 个问题
2. 问题必须是高价值问题，即回答后会直接影响后续优先事项选择
3. 不要重复询问用户已有信息
4. 问题要自然、口语化、适合直接发给用户
5. 不要像表单，不要太专业
6. 不要一次问太多细节
7. 优先问最能影响方案方向的信息

输出格式：
{{
  "missing_questions": [
    "...",
    "...",
    "...",
    "..."
  ]
}}"""

    return prompt


# ============================================================================
# Step 4: 向用户发起提问（格式化输出）
# ============================================================================

def build_questions_reply(missing_questions: List[str]) -> str:
    """
    将问题列表格式化为发送给用户的回复
    """
    if not missing_questions:
        return None

    lines = []
    lines.append("我先了解几个最关键的情况，这样后面给你的建议会更贴合你：\n")

    for i, q in enumerate(missing_questions, 1):
        lines.append(f"{i}. {q}")

    lines.append("\n你大概说一下就可以，不用特别精确。")

    return "\n".join(lines)


# ============================================================================
# Step 6: 结构化回答
# ============================================================================

def parse_user_answer(text: str, canonical_id: str) -> Dict[str, Any]:
    """
    将用户的自然语言回答解析为结构化字段

    注意：第一版比较简单，基于规则提取；第二版可以考虑用LLM
    """
    result = {
        "raw_answer": text,
        "parsed": {},
        "confidence": "low"
    }

    text = text.strip()

    if canonical_id == "sleep-insomnia":
        # 睡眠相关字段提取
        parsed = {}

        # 睡眠时间模式
        sleep_time_match = re.search(r'(\d{1,2})[点时](\d{0,2})?[睡\s]', text)
        if sleep_time_match:
            hour = sleep_time_match.group(1)
            minute = sleep_time_match.group(2) or "00"
            parsed["sleep_time"] = f"{hour}:{minute.zfill(2)}"

        # 起床时间模式
        wake_time_match = re.search(r'([早上早晨下午晚上]+)?(\d{1,2})[点时](\d{0,2})?[起起\s床]', text)
        if wake_time_match:
            hour = wake_time_match.group(2)
            minute = wake_time_match.group(3) or "00"
            parsed["wake_time"] = f"{hour}:{minute.zfill(2)}"

        # 睡眠时长模式
        duration_match = re.search(r'(\d+\.?\d*)\s*[小时hH个]', text)
        if duration_match:
            parsed["sleep_duration"] = float(duration_match.group(1))

        # 主要问题
        if "入睡" in text or "睡不着" in text:
            parsed["main_problem"] = "入睡困难"
        elif "易醒" in text or "醒来" in text or "醒" in text:
            parsed["main_problem"] = "容易醒"
        elif "早醒" in text:
            parsed["main_problem"] = "早醒"
        elif "睡眠浅" in text or "浅" in text:
            parsed["main_problem"] = "睡眠浅"

        # 药物
        if "药" in text:
            if "不服" in text or "没有" in text or "不吃" in text:
                parsed["medication"] = "不服药"
            elif "偶尔" in text:
                parsed["medication"] = "偶尔服药"
            else:
                parsed["medication"] = "服药"

        # 困倦 - 只在明确说"不困"时才解析，其他直接保留原话
        if "不" in text and ("困" in text or "累" in text):
            parsed["daytime_drowsiness"] = "不明显"
        elif "明显" in text and ("困" in text or "累" in text):
            parsed["daytime_drowsiness"] = "明显"
        # "有点累"这种模糊表达不强制解析，保留在raw_answer里

        result["parsed"] = parsed
        if len(parsed) >= 3:
            result["confidence"] = "medium"

    elif canonical_id == "hypertension":
        parsed = {}

        # 血压值
        bp_match = re.search(r'(\d{2,3})\s*/\s*(\d{2,3})', text)
        if bp_match:
            parsed["systolic"] = int(bp_match.group(1))
            parsed["diastolic"] = int(bp_match.group(2))

        # 药物
        if "药" in text:
            if "不服" in text or "没有" in text:
                parsed["medication"] = "不服药"
            elif "偶尔" in text:
                parsed["medication"] = "偶尔服药"
            else:
                parsed["medication"] = "规律服药"

        # 盐摄入
        if "盐" in text:
            if "清淡" in text or "少盐" in text:
                parsed["salt_intake"] = "偏低"
            elif "咸" in text or "重口" in text:
                parsed["salt_intake"] = "偏高"

        result["parsed"] = parsed
        if len(parsed) >= 2:
            result["confidence"] = "medium"

    elif canonical_id == "weight-loss":
        parsed = {}

        # 体重
        weight_match = re.search(r'(\d+\.?\d*)\s*[kK克g斤]', text)
        if weight_match:
            parsed["current_weight"] = float(weight_match.group(1))

        # 身高
        height_match = re.search(r'(\d{{2,3}})\s*[cC米m]', text)
        if height_match:
            parsed["height"] = float(height_match.group(1))

        # 饮食
        if "正常" in text or "规律" in text:
            parsed["diet"] = "正常"
        elif "外卖" in text or "不规律" in text:
            parsed["diet"] = "不规律"

        # 运动
        if "运动" in text or "锻炼" in text:
            if "不" in text and ("运动" in text or "锻炼" in text):
                parsed["exercise"] = "不运动"
            else:
                parsed["exercise"] = "有运动"

        result["parsed"] = parsed
        if len(parsed) >= 2:
            result["confidence"] = "medium"

    return result


# ============================================================================
# Step 7: 生成优先事项
# ============================================================================

def generate_priorities_prompt(
    canonical_id: str,
    display_name: str,
    knowledge_content: str,
    user_known_data: str,
    structured_answers: Dict[str, Any]
) -> str:
    """
    生成优先事项的Prompt
    """
    answers_str = json.dumps(structured_answers, ensure_ascii=False, indent=2)

    prompt = f"""你是一个行为干预优先事项生成助手。

当前问题：{display_name}

问题知识摘要：
{knowledge_content[:2000]}

用户已有信息：
{user_known_data}

用户刚刚补充的信息：
{answers_str}

请生成当前最适合这个用户的优先事项。

要求：
1. 输出 3 个核心优先事项
2. 输出 1-2 个辅助事项
3. 输出 2-4 个观察记录项
4. 优先事项要具体、可执行、低负担
5. 不要假设用户执行力很高
6. 不要给过于理想化的方案
7. 不要输出完整周计划，只输出优先事项
8. 药物相关默认只做记录、提醒、风险提示，不擅自给减药方案

输出格式：

【本周重点（先做这3件事）】
1. ...
2. ...
3. ...

【可以尝试（可选）】
- ...
- ...

【这周只需要简单记录】
- ...
- ..."""

    return prompt


def format_priorities_reply(priorities_text: str) -> str:
    """
    格式化优先事项回复
    """
    return f"""

{priorities_text}

---
以上是针对你的情况整理的本周优先事项。先从这些开始，慢慢来，不着急。
"""


# ============================================================================
# Step 8: 形成 case 文件
# ============================================================================

def ensure_cases_dir(problem_id: str) -> Path:
    """确保case目录存在"""
    case_dir = CASES_DIR / problem_id
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def build_case_content(
    user_id: str,
    canonical_id: str,
    display_name: str,
    knowledge_file: str,
    user_known_data: str,
    missing_questions: List[str],
    user_answers: Dict[str, Any],
    structured_answers: Dict[str, Any],
    priorities: str
) -> str:
    """
    构建case文件内容
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 用户回答摘要
    answers_summary = []
    if isinstance(user_answers, dict):
        for k, v in user_answers.items():
            answers_summary.append(f"- {k}: {v}")
    elif isinstance(user_answers, str):
        answers_summary.append(user_answers)

    content = f"""# 用户问题干预 Case

## 基本信息
- user_id: {user_id}
- problem_id: {canonical_id}
- display_name: {display_name}
- created_at: {now}

## 知识文件
- knowledge_file: {knowledge_file}

## 用户已有信息摘要
{user_known_data}

## 本轮补充提问
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(missing_questions))}

## 用户回答摘要
{chr(10).join(answers_summary)}

## 结构化回答
```json
{json.dumps(structured_answers, ensure_ascii=False, indent=2)}
```

## 当前优先事项

{priorities}

---
*此文件由 LifeOS 问题导向干预系统自动生成*
"""

    return content


def write_case_file(
    user_id: str,
    canonical_id: str,
    case_content: str
) -> Path:
    """
    写入case文件
    """
    case_dir = ensure_cases_dir(canonical_id)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"case-{user_id}-{date_str}.md"
    file_path = case_dir / filename
    file_path.write_text(case_content, encoding="utf-8")
    return file_path


# ============================================================================
# 主入口函数
# ============================================================================

def start_intervention_session(
    user_id: str,
    profile_id: str,
    user_message: str,
    canonical_id: str = None
) -> Dict[str, Any]:
    """
    开始一个干预会话（Step 1-4）

    返回:
    {
        "phase": "asking",  # 当前阶段
        "canonical_id": "sleep-insomnia",
        "display_name": "失眠 / 睡眠改善",
        "knowledge_file": "...",
        "missing_questions": [...],  # 要问的问题
        "reply_message": "...",  # 要发送给用户的回复
        "session_data": {...}  # 保存供后续使用
    }
    """
    intake = get_intervention_intake()

    # Step 1: 如果没有canonical_id，从消息中检测
    if not canonical_id:
        intent = intake.detect_intervention_intent(user_message)
        if not intent:
            return {
                "success": False,
                "error": "无法识别干预意图"
            }
        canonical_id = intent["canonical_id"]

    # 获取知识文件
    knowledge_content = intake.read_knowledge_file(canonical_id)
    if not knowledge_content:
        # 创建最小版
        display_name = intake.CANONICAL_DISPLAY_NAMES.get(canonical_id, canonical_id)
        knowledge_content = intake.create_minimal_knowledge_file(canonical_id, display_name)

    display_name = intake.CANONICAL_DISPLAY_NAMES.get(canonical_id, canonical_id)
    knowledge_file = str(intake.get_knowledge_file_path(canonical_id))

    # Step 2: 提取用户已有数据
    user_data_summary = build_user_known_data_summary(profile_id, canonical_id)
    user_data_prompt = format_user_known_data_for_prompt(user_data_summary, canonical_id)

    # Step 3: 生成提问Prompt（这里需要LLM，但第一版先返回问题列表的格式）
    # 注意：实际LLM调用由上层Agent执行，这里只生成Prompt模板
    prompt = generate_missing_questions_prompt(
        canonical_id,
        display_name,
        knowledge_content,
        user_data_prompt
    )

    # 返回结构供Agent使用
    session_data = {
        "user_id": user_id,
        "profile_id": profile_id,
        "canonical_id": canonical_id,
        "display_name": display_name,
        "knowledge_file": knowledge_file,
        "knowledge_content": knowledge_content,
        "user_data_summary": user_data_summary,
        "user_data_prompt": user_data_prompt,
        "questions_prompt": prompt,
        "phase": "asking"
    }

    return {
        "success": True,
        "phase": "asking",
        "canonical_id": canonical_id,
        "display_name": display_name,
        "knowledge_file": knowledge_file,
        "user_data_prompt": user_data_prompt,  # 用于调试/日志
        "reply_message": None,  # 需要LLM生成问题后再填充
        "session_data": session_data
    }


def process_user_answer(
    session_data: Dict[str, Any],
    user_answer: str,
    llm_questions: List[str],
    llm_priorities: str = None
) -> Dict[str, Any]:
    """
    处理用户回答，生成case文件（Step 5-8）

    参数:
        session_data: start_intervention_session返回的session_data
        user_answer: 用户刚才的回答
        llm_questions: LLM生成的问题列表
        llm_priorities: LLM生成的优先事项（可选）
    """
    canonical_id = session_data["canonical_id"]
    profile_id = session_data["profile_id"]
    user_id = session_data["user_id"]

    # Step 5 & 6: 解析用户回答
    parsed = parse_user_answer(user_answer, canonical_id)

    structured_answers = {
        "canonical_id": canonical_id,
        "profile_id": profile_id,
        "raw_answer": user_answer,
        "parsed": parsed.get("parsed", {}),
        "confidence": parsed.get("confidence", "low"),
        "questions_asked": llm_questions
    }

    # Step 7: 如果没有传入优先事项，生成占位
    if not llm_priorities:
        # 这里应该调用LLM生成，但暂时用模板
        priorities = """【本周重点（先做这3件事）】
1. 先记录3天睡眠情况（几点睡、几点起、睡得怎么样）
2. 固定起床时间，即使没睡好也按时起
3. 晚上10点后减少看手机

【可以尝试（可选）】
- 早晨晒15分钟太阳
- 下午3点后不喝咖啡

【这周只需要简单记录】
- 每天简单记一下睡眠情况
- 记一下白天是否明显困倦"""
    else:
        priorities = llm_priorities

    # Step 8: 生成case文件
    case_content = build_case_content(
        user_id=user_id,
        canonical_id=canonical_id,
        display_name=session_data["display_name"],
        knowledge_file=session_data["knowledge_file"],
        user_known_data=session_data["user_data_prompt"],
        missing_questions=llm_questions,
        user_answers=user_answer,
        structured_answers=structured_answers,
        priorities=priorities
    )

    case_path = write_case_file(user_id, canonical_id, case_content)

    return {
        "success": True,
        "phase": "completed",
        "canonical_id": canonical_id,
        "structured_answers": structured_answers,
        "priorities": priorities,
        "case_file": str(case_path),
        "reply_message": format_priorities_reply(priorities)
    }


# ============================================================================
# 快捷函数：完整流程（单次调用）
# ============================================================================

def run_full_intake_flow(
    user_id: str,
    profile_id: str,
    user_message: str,
    missing_questions: List[str] = None,
    user_answer: str = None,
    llm_priorities: str = None
) -> Dict[str, Any]:
    """
    完整流程入口（供测试用）

    missing_questions: LLM生成的问题列表（第一版可传None，用内置问题）
    user_answer: 用户回答（第一版可传None，用空回答）
    """
    # 第一步：启动会话
    result = start_intervention_session(
        user_id=user_id,
        profile_id=profile_id,
        user_message=user_message
    )

    if not result["success"]:
        return result

    # 如果没有传入问题，使用内置问题
    if not missing_questions:
        canonical_id = result["canonical_id"]
        if canonical_id == "sleep-insomnia":
            missing_questions = [
                "你大概几点睡觉、几点起床？",
                "每天晚上大概睡几个小时？",
                "主要是什么问题——入睡难、容易醒、还是早醒？",
                "白天有没有明显犯困或很累的感觉？"
            ]
        elif canonical_id == "hypertension":
            missing_questions = [
                "你平时血压大概是多少？",
                "有没有在吃降压药？",
                "每天大概吃多咸？",
                "有没有坚持运动的习惯？"
            ]
        elif canonical_id == "weight-loss":
            missing_questions = [
                "你目前体重多少、身高多少？",
                "平时饮食大概是什么情况？",
                "有没有坚持运动的习惯？",
                "这次减重主要是因为什么——体型、健康、还是医生建议？"
            ]
        else:
            missing_questions = ["你现在的主要困扰是什么？", "出现多久了？", "有在做什么处理吗？"]

    # 构建提问回复
    result["missing_questions"] = missing_questions
    result["reply_message"] = build_questions_reply(missing_questions)

    # 如果没有用户回答，返回提问阶段
    if not user_answer:
        return result

    # 处理回答，生成case文件
    answer_result = process_user_answer(
        session_data=result["session_data"],
        user_answer=user_answer,
        llm_questions=missing_questions,
        llm_priorities=llm_priorities
    )

    # 合并结果
    return {**result, **answer_result}


# ============================================================================
# 命令行入口（调试用）
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("问题导向干预 - 资料补全模块 调试")
    print("=" * 70)

    # 测试完整流程
    print("\n【测试：sleep-insomnia 完整流程】")
    result = run_full_intake_flow(
        user_id="ou_fde56bd8d48eca22b3d57ab990ee4f02",
        profile_id="001",
        user_message="改善睡眠问题",
        user_answer="我大概11点多睡，7点多起，睡6个多小时吧，主要是容易醒，白天还好不太困"
    )

    print(f"\ncanonical_id: {result.get('canonical_id')}")
    print(f"display_name: {result.get('display_name')}")

    if result.get("missing_questions"):
        print(f"\n提问的问题：")
        for q in result["missing_questions"]:
            print(f"  - {q}")

    print(f"\n回复消息：")
    print(result.get("reply_message", ""))

    if result.get("case_file"):
        print(f"\nCase文件已生成：{result['case_file']}")

    print("\n" + "=" * 70)
