#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeOS Bitable 操作脚本 v2.0
用于读写飞书多维表格数据，支持周计划驱动模式
"""

import requests
import json
import sys
import os
import re
import datetime
from contextlib import contextmanager
from pathlib import Path

# ============ 配置 ============
BASE_URL = "https://open.feishu.cn/open-apis"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = SKILL_ROOT / "config" / "bitable_config.json"

DEFAULT_APP_ID = "cli_a92ed6e39938dbd2"
DEFAULT_APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"

APP_ID = os.getenv("LIFEOS_FEISHU_APP_ID", DEFAULT_APP_ID)
APP_SECRET = os.getenv("LIFEOS_FEISHU_APP_SECRET", DEFAULT_APP_SECRET)


def load_bitable_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"bitables": {}, "default_bitable": "lifeos_jin"}


CONFIG = load_bitable_config()
BITABLES = CONFIG.get("bitables", {})
CURRENT_BITABLE = os.getenv("LIFEOS_DEFAULT_BITABLE", CONFIG.get("default_bitable", "lifeos_jin"))

TABLE_KEY_ALIASES = {
    "profile": ["profile", "个人资料", "数据表", "家庭成员表"],
    "daily_log": ["daily_log", "每日记录"],
    "event_log": ["event_log", "事件记录"],
    "medical_records": ["medical_records", "医疗记录"],
    "health_knowledge": ["health_knowledge", "健康知识"],
    "rules": ["rules", "规则"],
    "weekly_plan": ["weekly_plan", "周计划"],
    "weekly_plan_detail": ["weekly_plan_detail", "周计划详情"],
    "medication_supplement_list": ["medication_supplement_list", "药品补剂表", "药品补剂列表"],
    "health_evaluation": ["health_evaluation", "健康评估记录", "健康评估"],
}

DATE_FIELD_HINTS = {
    "date", "record_date", "next_review_date", "first_observed_at", "last_verified_at",
    "created_at", "updated_at", "week_start", "week_end", "plan_date", "start_date", "end_date",
    "event_datetime", "related_date", "last_triggered_at"
}


def _normalize_identity_name(name):
    if not name:
        return ""
    return re.sub(r"\s+", "", str(name)).strip().casefold()


def _build_runtime_chat_key(chat_id=None, chat_type=None):
    if not chat_id:
        return None
    if chat_type and chat_type != "direct":
        return f"{chat_type}:{chat_id}"
    return str(chat_id)


def _iter_identity_mappings():
    mappings = CONFIG.get("identity_mapping", [])
    if isinstance(mappings, dict):
        for _, value in mappings.items():
            if isinstance(value, dict):
                yield value
        return

    if isinstance(mappings, list):
        for item in mappings:
            if isinstance(item, dict):
                yield item


def resolve_identity(metadata=None, user_id=None, chat_id=None, sender_name=None, text_name=None, chat_type=None):
    """Resolve the target bitable from runtime identity hints."""
    metadata = metadata or {}

    meta_chat_id = metadata.get("chat_id") or chat_id
    meta_chat_type = metadata.get("chat_type") or metadata.get("channel_type") or chat_type
    runtime_chat_key = _build_runtime_chat_key(meta_chat_id, meta_chat_type)

    candidate_names = [
        metadata.get("sender_name"),
        metadata.get("sender"),
        sender_name,
        text_name,
    ]
    normalized_names = {name for name in (_normalize_identity_name(v) for v in candidate_names) if name}

    for mapping in _iter_identity_mappings():
        mapping_chat_id = mapping.get("chat_id")
        mapping_chat_type = mapping.get("chat_type")
        mapping_chat_key = mapping.get("chat_key") or _build_runtime_chat_key(mapping_chat_id, mapping_chat_type)
        if not runtime_chat_key or not mapping_chat_key or runtime_chat_key != mapping_chat_key:
            continue

        mapping_names = mapping.get("names") or [mapping.get("name")]
        mapping_name_set = {
            name for name in (_normalize_identity_name(v) for v in mapping_names) if name
        }
        if normalized_names and mapping_name_set.intersection(normalized_names):
            return {
                "bitable_key": mapping.get("bitable_key"),
                "profile_id": mapping.get("profile_id"),
                "matched_by": "chat_id_name",
                "chat_key": runtime_chat_key,
            }

    for bitable_key, bitable in BITABLES.items():
        if user_id and user_id in {
            bitable.get("owner_feishu_id"),
            bitable.get("owner_profile_id"),
            bitable.get("owner_user_id"),
        }:
            return {
                "bitable_key": bitable_key,
                "profile_id": bitable.get("owner_profile_id"),
                "matched_by": "user_id",
                "chat_key": runtime_chat_key,
            }

    return {
        "bitable_key": CURRENT_BITABLE,
        "profile_id": get_current_bitable().get("owner_profile_id"),
        "matched_by": "default",
        "chat_key": runtime_chat_key,
    }


def get_bitable_key_for_user(user_id=None, metadata=None, chat_id=None, sender_name=None, text_name=None, chat_type=None):
    """Resolve a configured bitable key from identity hints."""
    resolved = resolve_identity(
        metadata=metadata,
        user_id=user_id,
        chat_id=chat_id,
        sender_name=sender_name,
        text_name=text_name,
        chat_type=chat_type,
    )
    return resolved["bitable_key"]


def get_bitable_key_for_runtime(metadata=None, chat_id=None, sender_name=None, text_name=None, chat_type=None, user_id=None):
    """Resolve a configured bitable key for Feishu runtime metadata."""
    return get_bitable_key_for_user(
        user_id=user_id,
        metadata=metadata,
        chat_id=chat_id,
        sender_name=sender_name,
        text_name=text_name,
        chat_type=chat_type,
    )


def get_profile_id_for_runtime(metadata=None, chat_id=None, sender_name=None, text_name=None, chat_type=None, user_id=None):
    """Resolve the target profile id for Feishu runtime metadata."""
    resolved = resolve_identity(
        metadata=metadata,
        user_id=user_id,
        chat_id=chat_id,
        sender_name=sender_name,
        text_name=text_name,
        chat_type=chat_type,
    )
    return resolved.get("profile_id")

@contextmanager
def use_bitable_for_user(user_id=None, metadata=None, chat_id=None, sender_name=None, text_name=None, chat_type=None):
    """Temporarily switch the active bitable based on identity hints."""
    global CURRENT_BITABLE

    previous_bitable = CURRENT_BITABLE
    CURRENT_BITABLE = get_bitable_key_for_user(
        user_id=user_id,
        metadata=metadata,
        chat_id=chat_id,
        sender_name=sender_name,
        text_name=text_name,
        chat_type=chat_type,
    )
    try:
        yield CURRENT_BITABLE
    finally:
        CURRENT_BITABLE = previous_bitable


def get_current_bitable():
    bitable = BITABLES.get(CURRENT_BITABLE)
    if not bitable:
        raise KeyError(f"Unknown bitable config: {CURRENT_BITABLE}")
    return bitable


# 获取当前 APP_TOKEN
def get_current_app_token():
    return get_current_bitable()["app_token"]


# 表 ID 映射（优先从配置文件读取）
def get_table_ids():
    bitable = get_current_bitable()
    tables = dict(bitable.get("tables", {}))
    # 添加 health_evaluation 表（从独立配置区读取）
    he_ids = CONFIG.get("health_evaluation_table_ids", {})
    bitable_key = CURRENT_BITABLE
    if bitable_key in he_ids:
        tables["health_evaluation"] = he_ids[bitable_key]
    if tables:
        return tables
    return {
        "profile": "tbl2rpgHhR9rm6m0",
        "daily_log": "tbl9i2SehAhTZKrg",
        "event_log": "tblEyhr3CKUxqSgc",
        "medical_records": "tblIvTWyBUopNeyt",
        "health_knowledge": "tblNyrMIcXTZK3Jz",
        "rules": "tbl2Sbdeq3jXx4Lf",
        "weekly_plan": "tblkHBrurIm6f0j0",
        "weekly_plan_detail": "tblGHnXFij97QF9d",
        "medication_supplement_list": "tblDX3SHgxlFTsPI",
    }


def resolve_table_key(table_key):
    tables = get_table_ids()
    if table_key in tables:
        return table_key
    for canonical, aliases in TABLE_KEY_ALIASES.items():
        if table_key in aliases:
            for alias in aliases:
                if alias in tables:
                    return alias
            if canonical in tables:
                return canonical
    return table_key


def normalize_date_value(value):
    if value is None or value == "":
        return value
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, datetime.datetime):
        return int(value.timestamp() * 1000)
    if isinstance(value, datetime.date):
        dt = datetime.datetime.combine(value, datetime.time.min)
        return int(dt.timestamp() * 1000)
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"\d{13}", text):
            return int(text)
        if re.fullmatch(r"\d{10}", text):
            return int(text) * 1000
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
            try:
                dt = datetime.datetime.strptime(text, fmt)
                return int(dt.timestamp() * 1000)
            except ValueError:
                pass
    return value


def normalize_fields(fields):
    normalized = dict(fields)
    for key, value in list(normalized.items()):
        if key in DATE_FIELD_HINTS or key.endswith("_date") or key.endswith("_at") or key.endswith("_datetime"):
            normalized[key] = normalize_date_value(value)
    return normalized

# ============ Token 获取 ============
def get_token():
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result["tenant_access_token"]
    return None

# ============ 读取记录 ============
def read_records(token, table_key, filterformula=None, limit=100):
    """读取表中的记录"""
    table_key = resolve_table_key(table_key)
    table_id = get_table_ids().get(table_key)
    if not table_id:
        return None, f"Unknown table: {table_key}"
    
    app_token = get_current_app_token()
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": limit}
    
    if filterformula:
        params["filter"] = filterformula
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return result.get("data", {}).get("items") or [], None
        return None, f"Error {result.get('code')}: {result.get('msg')}"
    except Exception as e:
        return None, str(e)

# ============ 创建记录 ============
def create_record(token, table_key, fields):
    """在表中创建新记录"""
    table_key = resolve_table_key(table_key)
    table_id = get_table_ids().get(table_key)
    if not table_id:
        return None, f"Unknown table: {table_key}"
    
    app_token = get_current_app_token()
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"fields": normalize_fields(fields)}
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return result.get("data", {}).get("record", {}).get("record_id"), None
        return None, f"Error {result.get('code')}: {result.get('msg')}"
    except Exception as e:
        return None, str(e)

# ============ 更新记录 ============
def update_record(token, table_key, record_id, fields):
    """更新表中记录"""
    table_key = resolve_table_key(table_key)
    table_id = get_table_ids().get(table_key)
    if not table_id:
        return False, f"Unknown table: {table_key}"
    
    app_token = get_current_app_token()
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"fields": normalize_fields(fields)}
    
    try:
        resp = requests.put(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return True, None
        return False, f"Error {result.get('code')}: {result.get('msg')}"
    except Exception as e:
        return False, str(e)

# ============ 查询最近记录 ============
def get_recent_records(token, table_key, days=7, sort_field="date", descending=True):
    """获取最近 N 天的记录"""
    records, err = read_records(token, table_key)
    if err:
        return None, err
    
    if sort_field and records:
        records.sort(
            key=lambda x: x.get("fields", {}).get(sort_field, ""),
            reverse=descending
        )
    
    return records[:days], None

# ============ 用户输入解析 ============
def parse_user_input(text):
    """解析用户输入，提取结构化信息"""
    info = {
        "type": None,
        "data": {},
        "event": None,
        "needs_write": False,
    }
    
    text = text.strip()
    
    # 状态记录关键词
    status_keywords = ["累", "疲劳", "状态", "好", "不错", "差", "困"]
    for kw in status_keywords:
        if kw in text:
            info["type"] = "状态记录"
            info["data"]["mood_description"] = text
            info["needs_write"] = True
            break
    
    # 睡眠数据
    if "睡" in text:
        hours = re.search(r'(\d+\.?\d*)\s*(?:个小时?|小时|h)', text)
        if hours:
            info["type"] = "数据输入"
            info["data"]["sleep_hours"] = float(hours.group(1))
            info["needs_write"] = True
    
    # 体重数据
    if "体重" in text or "kg" in text.lower():
        weight = re.search(r'(\d+\.?\d*)\s*(?:斤|kg|公斤)', text)
        if weight:
            info["type"] = "数据输入"
            w = float(weight.group(1))
            # 斤转kg
            if "斤" in text:
                w = w / 2
            info["data"]["weight_kg"] = w
            info["needs_write"] = True
    
    # 血压数据
    if "血压" in text:
        bp = re.search(r'(\d+)[-/](\d+)', text)
        if bp:
            info["type"] = "数据输入"
            info["data"]["blood_pressure"] = {
                "systolic": int(bp.group(1)),
                "diastolic": int(bp.group(2))
            }
            info["needs_write"] = True
    
    # 事件记录
    event_keywords = ["聚餐", "出差", "熬夜", "加班", "生病", "旅行", "胃", "体检"]
    for kw in event_keywords:
        if kw in text:
            info["type"] = "事件记录"
            info["event"] = kw
            info["needs_write"] = True
            break
    
    # 请求建议
    if any(kw in text for kw in ["要不要", "怎么", "是否", "可以"]):
        if info["type"] is None:
            info["type"] = "请求建议"
    
    # 周计划请求
    if any(kw in text for kw in ["本周计划", "这周安排", "周计划", "帮我做计划"]):
        if info["type"] is None:
            info["type"] = "请求周计划"
    
    # 计划调整
    if any(kw in text for kw in ["改成", "改", "不想", "不练", "调整"]):
        if info["type"] is None:
            info["type"] = "计划调整"
    
    return info



# ============ Profile 输入解析 ============


# ============ Profile 输入解析 ============
def parse_profile_input(text):
    """
    解析用户输入中的 profile 信息（性别、年龄）
    返回: {"gender": "男"/"女"/None, "age": int/None, "birth_date": timestamp/None}
    """
    result = {"gender": None, "age": None, "birth_date": None}
    
    text = text.strip()
    
    # 性别解析 - 更宽松的模式
    gender_keywords_male = ['男', '男性', '老公', '先生']
    gender_keywords_female = ['女', '女性', '老婆', '女士']
    
    for kw in gender_keywords_male:
        if kw in text:
            result["gender"] = "男"
            break
    else:
        for kw in gender_keywords_female:
            if kw in text:
                result["gender"] = "女"
                break
    
    # 年龄解析
    age_patterns = [
        r'今年\s*(\d+)\s*岁',
        r'(\d+)\s*岁',
        r'年\s*纪?\s*(\d+)',
        r'^(\d+)\s*岁',
    ]
    for pattern in age_patterns:
        m = re.search(pattern, text)
        if m:
            age = int(m.group(1))
            if 1 <= age <= 120:
                result["age"] = age
                # 计算出生年份
                current_year = datetime.datetime.now().year
                birth_year = current_year - age
                # 估算出生日期（年中）
                try:
                    bd = datetime.datetime(birth_year, 6, 15)
                    result["birth_date"] = int(bd.timestamp() * 1000)
                except:
                    pass
            break
    
    return result






def update_profile_field(token, field_name, value):
    """
    更新 profile 表中的单个字段
    返回: (success, error)
    """
    # 获取当前 profile
    profile = get_profile(token)
    if not profile:
        return False, "No profile found"
    
    record_id = profile.get("record_id")
    if not record_id:
        return False, "Profile record has no ID"
    
    success, err = update_record(token, "profile", record_id, {field_name: value})
    return success, err


def update_profile_from_text(token, text):
    """
    从用户输入中解析 profile 信息并更新
    返回: (updated_fields, error)
    """
    parsed = parse_profile_input(text)
    updated = []
    errors = []
    
    if parsed["gender"]:
        success, err = update_profile_field(token, "gender", parsed["gender"])
        if success:
            updated.append("gender")
        else:
            errors.append("gender: {}".format(err))
    
    if parsed["birth_date"]:
        success, err = update_profile_field(token, "birth_date", parsed["birth_date"])
        if success:
            updated.append("birth_date")
        else:
            errors.append("birth_date: {}".format(err))
    
    if not updated and not errors:
        return [], "No profile info parsed from text"
    
    return updated, "; ".join(errors) if errors else None


# ============ 周计划相关函数 ============
def get_active_weekly_plan(token):
    """获取当前生效的周计划"""
    records, err = read_records(token, "weekly_plan")
    if err or not records:
        return None
    
    for r in records:
        fields = r.get("fields", {})
        if fields.get("plan_status") == "生效中":
            return r
    
    return None


def get_recent_daily_logs(token, days=14):
    """获取最近N天的每日记录"""
    records, err = read_records(token, "daily_log", limit=100)
    if err or not records:
        return []
    
    records.sort(key=lambda x: x.get("fields", {}).get("date", ""), reverse=True)
    return records[:days]


def get_recent_events(token, days=7):
    """获取最近N天的事件记录"""
    records, err = read_records(token, "event_log", limit=100)
    if err or not records:
        return []
    
    records.sort(key=lambda x: x.get("fields", {}).get("event_datetime", ""), reverse=True)
    return records[:days]


def get_enabled_rules(token):
    """获取已启用的规则"""
    records, err = read_records(token, "rules")
    if err or not records:
        return []
    
    enabled = []
    for r in records:
        fields = r.get("fields", {})
        if fields.get("enabled") == True:
            status = fields.get("review_status", "")
            confidence = fields.get("confidence", 0)
            if status == "已确认" or (status == "候选" and confidence > 0.7):
                enabled.append(r)
    
    return enabled


def get_profile(token):
    """获取用户 profile"""
    records, err = read_records(token, "profile", limit=1)
    if err or not records:
        return None
    return records[0]


def get_active_medications(token):
    """获取当前启用的药品/补剂"""
    records, err = read_records(token, "medication_supplement_list")
    if err or not records:
        return []
    
    active = []
    for r in records:
        fields = r.get("fields", {})
        if fields.get("status") == "启用":
            active.append(r)
    
    return active


def check_rule_trigger(rule, context):
    """
    检查规则是否被触发
    rule: 规则记录
    context: 上下文信息
    返回: (是否触发, 触发的action)
    """
    fields = rule.get("fields", {})
    trigger = fields.get("trigger_conditions", "")
    action = fields.get("action", "")
    
    # 高疲劳规则 R002: fatigue_score >= 8
    if "fatigue_score" in trigger and ">= 8" in trigger:
        if context.get("fatigue_score", 0) >= 8:
            return True, action
    
    # 连续疲劳规则 R003: 连续2天 >= 7
    if "连续" in trigger and "fatigue_score" in trigger:
        if context.get("consecutive_high_fatigue", 0) >= 2:
            return True, action
    
    # 聚餐后修正 R004
    if "聚餐" in trigger and "event_type" in trigger:
        if context.get("has_gathering", False):
            return True, action
    
    # 身体不适 R008
    if "身体不适" in trigger or "body_discomfort" in trigger:
        if context.get("body_discomfort", False):
            return True, action
    
    return False, ""


def calculate_age(birth_date_str):
    """计算年龄"""
    if not birth_date_str:
        return None
    
    try:
        # birth_date 可能是时间戳或日期字符串
        if isinstance(birth_date_str, (int, float)):
            birth = datetime.datetime.fromtimestamp(birth_date_str / 1000)
        else:
            birth = datetime.datetime.strptime(str(birth_date_str), "%Y-%m-%d")
        
        today = datetime.datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age
    except:
        return None


# ============ 周计划详情相关函数 ============
def create_weekly_plan_detail(token, weekly_plan_id, profile_id, plan_date, weekday, 
                             daily_theme, training_detail, diet_detail, 
                             supplement_medication_detail, recovery_detail,
                             fallback_plan, priority_level="中", notes=""):
    """创建周计划每日详情记录"""
    fields = {
        "weekly_plan_id": weekly_plan_id,
        "profile_id": profile_id,
        "plan_date": plan_date,
        "weekday": weekday,
        "daily_theme": daily_theme,
        "training_detail": training_detail,
        "diet_detail": diet_detail,
        "supplement_medication_detail": supplement_medication_detail,
        "recovery_detail": recovery_detail,
        "fallback_plan": fallback_plan,
        "priority_level": priority_level,
        "notes": notes,
    }
    return create_record(token, "weekly_plan_detail", fields)


def get_weekday_name(day_of_week):
    """获取星期几的中文名"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[day_of_week]


def get_week_dates(week_start_str):
    """获取一周的日期列表"""
    try:
        start = datetime.datetime.strptime(week_start_str, "%Y-%m-%d")
        dates = []
        for i in range(7):
            d = start + datetime.timedelta(days=i)
            dates.append(d.strftime("%Y-%m-%d"))
        return dates
    except:
        return []


def get_state_summary(daily_logs):
    """从最近daily_log计算状态摘要"""
    if not daily_logs:
        return {}
    
    summary = {
        "avg_fatigue": 0,
        "avg_energy": 0,
        "avg_sleep_hours": 0,
        "consecutive_high_fatigue": 0,
        "recent_weight": None,
        "training_days": 0,
        "total_days": len(daily_logs),
    }
    
    total_fatigue = 0
    total_energy = 0
    total_sleep = 0
    high_fatigue_count = 0
    
    for log in daily_logs[:7]:  # 最近7天
        fields = log.get("fields", {})
        
        fs = fields.get("fatigue_score", 0)
        if fs:
            total_fatigue += fs
            if fs >= 7:
                high_fatigue_count += 1
        
        es = fields.get("energy_score", 0)
        if es:
            total_energy += es
        
        sh = fields.get("sleep_hours", 0)
        if sh:
            total_sleep += sh
        
        if fields.get("had_training"):
            summary["training_days"] += 1
        
        if summary["recent_weight"] is None:
            ww = fields.get("weight_kg")
            if ww:
                summary["recent_weight"] = ww
    
    n = min(summary["total_days"], 7)
    if n > 0:
        summary["avg_fatigue"] = total_fatigue / n
        summary["avg_energy"] = total_energy / n if total_energy else 0
        summary["avg_sleep_hours"] = total_sleep / n if total_sleep else 0
    
    summary["consecutive_high_fatigue"] = high_fatigue_count
    
    return summary


# ============ 主函数 ============
def main():
    if len(sys.argv) < 2:
        print("Usage: python bitable_ops.py <action> [args]")
        print("Actions:")
        print("  read <table> [limit]              - Read records from table")
        print("  create <table> <fields>            - Create a new record")
        print("  recent <table> [days]             - Get recent records")
        print("  parse <text>                      - Parse user input")
        print("  weekly_plan                       - Get active weekly plan")
        print("  profile                           - Get user profile")
        print("  rules                             - Get enabled rules")
        print("  summary                           - Get state summary from recent logs")
        sys.exit(1)
    
    action = sys.argv[1]
    token = get_token()
    if not token:
        print("[ERROR] Failed to get token")
        sys.exit(1)
    
    if action == "read":
        table = sys.argv[2] if len(sys.argv) > 2 else "daily_log"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        records, err = read_records(token, table, limit=limit)
        if err:
            print(f"[ERROR] {err}")
        else:
            print(json.dumps(records, ensure_ascii=False, indent=2))
    
    elif action == "recent":
        table = sys.argv[2] if len(sys.argv) > 2 else "daily_log"
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        records, err = get_recent_records(token, table, days=days)
        if err:
            print(f"[ERROR] {err}")
        else:
            print(json.dumps(records, ensure_ascii=False, indent=2))
    
    elif action == "parse":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        info = parse_user_input(text)
        print(json.dumps(info, ensure_ascii=False, indent=2))
    
    elif action == "weekly_plan":
        plan = get_active_weekly_plan(token)
        if plan:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print("[INFO] No active weekly plan found")
    
    elif action == "profile":
        profile = get_profile(token)
        if profile:
            print(json.dumps(profile, ensure_ascii=False, indent=2))
        else:
            print("[INFO] No profile found")
    
    elif action == "rules":
        rules = get_enabled_rules(token)
        print(f"[INFO] Found {len(rules)} enabled rules")
        for r in rules:
            fields = r.get("fields", {})
            print(f"  - {fields.get('rule_id')}: {fields.get('rule_name')}")
    
    elif action == "summary":
        logs = get_recent_daily_logs(token, days=7)
        summary = get_state_summary(logs)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    elif action == "week_dates":
        week_start = sys.argv[2] if len(sys.argv) > 2 else "2026-03-23"
        dates = get_week_dates(week_start)
        print("Week dates:")
        for i, d in enumerate(dates):
            print(f"  {get_weekday_name(i)}: {d}")
    
    else:
        print(f"[ERROR] Unknown action: {action}")

if __name__ == "__main__":
    main()
