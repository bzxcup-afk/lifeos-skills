#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库初始化脚本"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_connection, get_db_path, execute, query_one

SCHEMA = """
-- 用户资料
CREATE TABLE IF NOT EXISTS profiles (
    profile_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    gender TEXT,
    birth_date TEXT,
    height_cm REAL,
    weight_kg REAL,
    -- 新增：体征相关
    blood_type TEXT,                    -- 血型
    resting_heart_rate INTEGER,         -- 静息心率
    waist_cm REAL,                      -- 腰围
    hip_cm REAL,                        -- 臀围
    -- 新增：目标与阶段
    body_goal TEXT,                     -- 身体目标
    current_stage TEXT,                 -- 当前阶段
    -- 新增：健康相关
    health_concerns TEXT,               -- 健康关注
    family_history TEXT,                -- 家族病史
    lifestyle_habits TEXT,              -- 生活习惯
    diet_preferences TEXT,              -- 饮食偏好
    -- 原有字段
    training_base TEXT,
    health_goal TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 每日记录
CREATE TABLE IF NOT EXISTS daily_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    date TEXT NOT NULL,
    sleep_hours REAL,
    sleep_quality INTEGER,
    fatigue_score INTEGER,
    energy_score INTEGER,
    weight_kg REAL,
    had_training BOOLEAN,
    training_brief TEXT,
    diet_status TEXT,
    body_status_notes TEXT,
    today_summary TEXT,
    state_tags TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(profile_id, date),
    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id)
);

-- 事件记录
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    event_date TEXT,
    event_type TEXT,
    event_description TEXT,
    impact_level TEXT,
    related_metrics TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id)
);

-- 医疗记录
CREATE TABLE IF NOT EXISTS medical_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    record_date TEXT,
    record_type TEXT,
    complaint_or_reason TEXT,
    diagnosis TEXT,
    key_metrics_json TEXT,
    treatment_summary TEXT,
    tags TEXT,
    summary_for_system TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id)
);

-- 用药清单
CREATE TABLE IF NOT EXISTS medications (
    med_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    drug_name TEXT NOT NULL,
    dosage TEXT,
    time_slot TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id)
);

-- 服药记录
CREATE TABLE IF NOT EXISTS medication_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    med_id INTEGER NOT NULL,
    profile_id TEXT NOT NULL,
    date TEXT NOT NULL,
    time_slot TEXT,
    status TEXT DEFAULT 'pending',
    taken_at TEXT,
    FOREIGN KEY(med_id) REFERENCES medications(med_id),
    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id)
);

-- 周计划
CREATE TABLE IF NOT EXISTS weekly_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    week_start TEXT NOT NULL,
    week_end TEXT,
    plan_status TEXT DEFAULT 'draft',
    weekly_goal TEXT,
    key_focus TEXT,
    risk_notes TEXT,
    adjustment_principles TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id)
);

-- 周计划详情
CREATE TABLE IF NOT EXISTS weekly_plan_details (
    detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    profile_id TEXT NOT NULL,
    plan_date TEXT NOT NULL,
    weekday TEXT,
    daily_theme TEXT,
    training_detail TEXT,
    diet_detail TEXT,
    supplement_medication_detail TEXT,
    recovery_detail TEXT,
    fallback_plan TEXT,
    priority_level TEXT,
    notes TEXT,
    FOREIGN KEY(plan_id) REFERENCES weekly_plans(plan_id),
    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id)
);

-- 健康评估记录
CREATE TABLE IF NOT EXISTS health_evaluations (
    eval_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    eval_date TEXT,
    data_source_desc TEXT,
    data_time_range TEXT,
    data_coverage TEXT,
    confidence_score INTEGER,
    cardio_score INTEGER,
    strength_score INTEGER,
    metabolism_score INTEGER,
    recovery_score INTEGER,
    execution_score INTEGER,
    total_score INTEGER,
    risk_signals TEXT,
    overall_status TEXT,
    main_issues TEXT,
    recommended_actions TEXT,
    brief_report TEXT,
    chart_data_json TEXT,
    explanation_json TEXT,
    eval_age INTEGER,
    eval_gender TEXT,
    eval_training_base TEXT,
    eval_health_goal TEXT,
    missing_fields TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id)
);

-- 健康知识库
CREATE TABLE IF NOT EXISTS health_knowledge (
    knowledge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    content TEXT,
    category TEXT,
    tags TEXT,
    source TEXT,
    confidence INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 规则表
CREATE TABLE IF NOT EXISTS rules (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT,
    trigger_conditions TEXT,
    action TEXT,
    priority INTEGER,
    enabled BOOLEAN DEFAULT 1,
    review_status TEXT,
    confidence REAL,
    tags TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 个人偏好表
CREATE TABLE IF NOT EXISTS user_preferences (
    pref_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL UNIQUE,
    sports_likes TEXT,                  -- 喜欢的运动
    sports_dislikes TEXT,               -- 不喜欢的运动
    food_likes TEXT,                    -- 喜欢的食物
    food_dislikes TEXT,                 -- 不喜欢的食物
    cuisine_likes TEXT,                 -- 喜欢的菜系
    nutrition_preferences TEXT,         -- 营养方案偏好
    execution_preferences TEXT,          -- 执行偏好
    notes TEXT,                         -- 备注/变更历史
    source TEXT,                        -- 来源: dialogue_extract/guided_answer/manual
    confidence TEXT,                    -- 置信度: high/medium/low
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES profiles(profile_id)
);
"""

def init():
    print(f"Initializing database...")
    print(f"Path: {get_db_path()}")
    
    try:
        with get_connection() as conn:
            conn.executescript(SCHEMA)
        print("[OK] Schema created")
        
        # 初始化用户
        default_users = [("001", "金"), ("002", "芳芳"), ("003", "老妈"), ("004", "老爹")]
        for profile_id, name in default_users:
            existing = query_one("SELECT 1 FROM profiles WHERE profile_id = ?", (profile_id,))
            if not existing:
                execute("INSERT INTO profiles (profile_id, name) VALUES (?, ?)", (profile_id, name))
        
        print("[OK] Default profiles initialized")
        print("\nDone!")
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    success = init()
    sys.exit(0 if success else 1)
