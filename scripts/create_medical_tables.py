#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建医疗报告归档相关的4个缺失表

1. raw_reports - 原始报告存储（OCR识别后的原始数据）
2. reports_master - 报告主表（医疗报告的汇总信息）
3. indicators_detail - 指标明细（各项检查指标的详细数据）
4. health_master - 健康主档案（个人的健康汇总档案）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import execute, query_one

# 1. raw_reports - 原始报告存储
RAW_REPORTS_TABLE = """
CREATE TABLE IF NOT EXISTS raw_reports (
    raw_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    -- 报告来源信息
    report_source TEXT,                    -- 报告来源（医院/体检中心等）
    report_type TEXT,                      -- 报告类型（体检/门诊/住院等）
    report_date TEXT,                      -- 报告日期
    -- OCR原始数据
    ocr_raw_text TEXT,                     -- OCR识别的原始文本
    ocr_confidence REAL,                   -- OCR置信度
    ocr_engine TEXT,                       -- OCR引擎（如：paddle/teseract等）
    -- 图片信息
    image_count INTEGER,                   -- 图片数量
    image_paths TEXT,                      -- 图片路径（JSON数组）
    -- 处理状态
    processing_status TEXT DEFAULT 'pending', -- 处理状态（pending/processing/completed/failed）
    processing_notes TEXT,                   -- 处理备注
    -- 关联信息
    linked_report_id TEXT,                 -- 关联到reports_master的report_id
    -- 时间戳
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id)
);
"""

# 2. reports_master - 报告主表
REPORTS_MASTER_TABLE = """
CREATE TABLE IF NOT EXISTS reports_master (
    report_id TEXT PRIMARY KEY,            -- 报告唯一ID（如：REP-20240326-001）
    profile_id TEXT NOT NULL,
    -- 报告基本信息
    report_source TEXT,                    -- 报告来源（医院名称）
    report_type TEXT,                      -- 报告类型（体检/门诊/住院/检验等）
    report_subtype TEXT,                   -- 报告子类型（血常规/尿常规/生化等）
    report_date TEXT,                      -- 报告日期
    -- 医院信息
    hospital_name TEXT,                    -- 医院名称
    hospital_department TEXT,              -- 科室
    hospital_doctor TEXT,                  -- 医生姓名
    -- 报告摘要
    report_summary TEXT,                   -- 报告摘要
    key_findings TEXT,                     -- 主要发现（JSON数组）
    abnormal_items TEXT,                   -- 异常项目（JSON数组）
    overall_assessment TEXT,               -- 总体评估
    -- 状态
    review_status TEXT DEFAULT 'pending',  -- 审核状态（pending/reviewed/confirmed）
    archive_status TEXT DEFAULT 'active',  -- 归档状态（active/archived/deleted）
    -- 关联
    raw_report_id INTEGER,                 -- 关联到raw_reports
    -- 时间戳
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id),
    FOREIGN KEY (raw_report_id) REFERENCES raw_reports(raw_id)
);
"""

# 3. indicators_detail - 指标明细
INDICATORS_DETAIL_TABLE = """
CREATE TABLE IF NOT EXISTS indicators_detail (
    indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    -- 指标基本信息
    indicator_name TEXT,                   -- 指标名称（如：总胆固醇）
    indicator_name_en TEXT,                -- 指标英文名（如：Total Cholesterol）
    indicator_category TEXT,               -- 指标分类（如：血脂/血糖/肝功等）
    -- 数值信息
    value_raw TEXT,                        -- 原始值（字符串）
    value_numeric REAL,                    -- 数值（转为数字）
    unit TEXT,                             -- 单位（如：mmol/L）
    -- 参考范围
    reference_range_text TEXT,               -- 参考范围文本（如：3.1-5.7）
    reference_range_min REAL,                -- 参考范围最小值
    reference_range_max REAL,                -- 参考范围最大值
    -- 判断结果
    status TEXT,                           -- 状态（normal/abnormal/critical/borderline）
    direction TEXT,                        -- 方向（high/low/normal）
    severity INTEGER,                      -- 严重程度（0-10）
    -- 医学解释
    clinical_significance TEXT,            -- 临床意义
    suggestions TEXT,                      -- 建议
    -- 关联信息
    related_indicators TEXT,               -- 相关指标（JSON数组）
    -- 时间戳
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES reports_master(report_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id)
);
"""

# 4. health_master - 健康主档案
HEALTH_MASTER_TABLE = """
CREATE TABLE IF NOT EXISTS health_master (
    health_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL UNIQUE,       -- 每个用户只有一条健康主档案
    -- 最新体检信息
    latest_physical_date TEXT,             -- 最新体检日期
    latest_physical_report_id TEXT,        -- 最新体检报告ID
    -- 关键指标汇总（最新值）
    latest_blood_pressure TEXT,              -- 最新血压（如：120/80）
    latest_blood_sugar REAL,               -- 最新血糖
    latest_hba1c REAL,                     -- 最新糖化血红蛋白
    latest_cholesterol_total REAL,         -- 最新总胆固醇
    latest_ldl REAL,                       -- 最新低密度脂蛋白
    latest_hdl REAL,                       -- 最新高密度脂蛋白
    latest_triglycerides REAL,             -- 最新甘油三酯
    -- 异常指标跟踪
    abnormal_indicators TEXT,                -- 异常指标列表（JSON）
    chronic_conditions TEXT,                 -- 慢性病列表（JSON）
    -- 健康评估
    overall_health_score INTEGER,          -- 总体健康评分（0-100）
    health_risk_level TEXT,                -- 健康风险等级（low/medium/high）
    last_evaluation_date TEXT,             -- 最后评估日期
    -- 随访与提醒
    follow_up_items TEXT,                  -- 随访事项（JSON）
    next_checkup_date TEXT,                -- 下次体检日期
    -- 统计信息
    total_reports INTEGER DEFAULT 0,       -- 总报告数
    total_indicators INTEGER DEFAULT 0,    -- 总指标数
    -- 时间戳
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id)
);
"""

# 执行创建所有表
SQL_SCRIPTS = [
    ("raw_reports", RAW_REPORTS_TABLE),
    ("reports_master", REPORTS_MASTER_TABLE),
    ("indicators_detail", INDICATORS_DETAIL_TABLE),
    ("health_master", HEALTH_MASTER_TABLE),
]

def main():
    print("=" * 80)
    print("创建医疗报告归档相关的4个表")
    print("=" * 80)
    print()
    
    created = []
    failed = []
    
    for table_name, sql in SQL_SCRIPTS:
        print(f"创建表: {table_name} ...", end=" ")
        try:
            execute(sql)
            print("✓ 成功")
            created.append(table_name)
        except Exception as e:
            print(f"✗ 失败: {e}")
            failed.append((table_name, str(e)))
    
    print()
    print("=" * 80)
    print("结果汇总")
    print("=" * 80)
    print(f"成功创建: {len(created)} 个表")
    for t in created:
        print(f"  ✓ {t}")
    
    if failed:
        print(f"\n创建失败: {len(failed)} 个表")
        for t, e in failed:
            print(f"  ✗ {t}: {e}")
    
    print("=" * 80)

if __name__ == '__main__':
    main()
