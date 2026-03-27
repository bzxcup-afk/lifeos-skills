#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeOS Bitable 字段同步脚本 v2.1
同步医疗报告归档 v1.1.0 新增表和字段
"""

import requests
import json
import os
from pathlib import Path

# ============ 配置 ============
BASE_URL = "https://open.feishu.cn/open-apis"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent.parent

# 飞书 Bitable 字段类型映射（字符串名 -> API数字ID）
FIELD_TYPE_MAP = {
    "text": 1,
    "number": 2,
    "single_select": 3,
    "multi_select": 4,
    "datetime": 5,
    "checkbox": 7,
    "textarea": 2,  # 富文本映射为多行文本
    "select": 3,     # select 映射为单选
}

# 从环境变量或配置文件获取
APP_ID = os.getenv("LIFEOS_FEISHU_APP_ID", "cli_a92ed6e39938dbd2")
APP_SECRET = os.getenv("LIFEOS_FEISHU_APP_SECRET", "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq")

# 需要同步的Bitable配置
BITABLE_CONFIGS = {
    "lifeos_jin": {
        "name": "金 - LifeOS",
        "app_token": "DtWnbquyZaIj9xsWLSIcagjQnAc",
    },
    "lifeos_fangfang": {
        "name": "芳芳 - LifeOS",
        "app_token": "Y2pxbRjm8avmLUsnH8jc2K5rnHL",
    },
    "lifeos_laoma": {
        "name": "老妈 - LifeOS",
        "app_token": "LDk3b3PGtaGbDVsjOV1cavxun2g",
    },
    "lifeos_laolao": {
        "name": "老爹 - LifeOS",
        "app_token": "ILxkbi8gwaQBK4srjcSczYWZncb",
    },
}

# 新增表字段定义
NEW_TABLES_FIELDS = {
    "raw_reports": [
        ("report_id", "text", "报告唯一ID"),
        ("report_type", "text", "报告类型"),
        ("hospital", "text", "医院名称"),
        ("department", "text", "科室"),
        ("exam_date", "datetime", "检查日期"),
        ("report_date", "datetime", "报告日期"),
        ("patient_name", "text", "患者姓名"),
        ("patient_gender", "select", "患者性别"),
        ("patient_age", "number", "患者年龄"),
        ("doctor", "text", "申请医生"),
        ("raw_data", "text", "原始JSON数据"),
        # v1.1.0 新增风险相关字段
        ("table_risk_level", "select", "表格风险等级"),
        ("has_structure_risk", "checkbox", "是否存在结构风险"),
        ("high_risk_item_count", "number", "高风险项目数量"),
        ("medium_risk_item_count", "number", "中风险项目数量"),
        ("risk_summary", "text", "风险摘要"),
        ("requires_review", "checkbox", "是否需要人工核实"),
        ("archive_status", "select", "归档状态"),
    ],
    "reports_master": [
        ("report_name", "text", "报告名称"),
        ("report_type", "text", "报告类型"),
        ("hospital", "text", "医院"),
        ("exam_date", "datetime", "检查日期"),
        ("abnormal_count", "number", "异常项数量"),
        ("key_abnormal_items", "text", "关键异常项"),
        ("doctor_summary", "text", "医生结论"),
        ("archive_status", "select", "归档状态"),
    ],
    "indicators_detail": [
        ("indicator_name", "text", "指标名称"),
        ("standard_name", "text", "标准名称"),
        ("category", "text", "类别"),
        ("value", "number", "数值"),
        ("text_value", "text", "文本值"),
        ("unit", "text", "单位"),
        ("reference_range", "text", "参考范围"),
        ("abnormal_flag", "select", "异常标记"),
        ("confidence", "number", "识别置信度"),
        # v1.1.0 新增字段
        ("risk_flags", "text", "风险标记(JSON)"),
        ("review_priority", "select", "复核优先级"),
        ("is_verified", "checkbox", "是否已确认"),
        ("is_used_for_profile", "checkbox", "是否用于主档案"),
    ],
    "health_master": [
        ("latest_sbp", "number", "最新收缩压"),
        ("latest_dbp", "number", "最新舒张压"),
        ("bp_record_date", "datetime", "血压记录日期"),
        ("latest_fpg", "number", "最新空腹血糖"),
        ("latest_hba1c", "number", "最新糖化血红蛋白"),
        ("glucose_record_date", "datetime", "血糖记录日期"),
        ("latest_ldl_c", "number", "最新LDL-C"),
        ("latest_hdl_c", "number", "最新HDL-C"),
        ("latest_tg", "number", "最新甘油三酯"),
        ("lipid_record_date", "datetime", "血脂记录日期"),
        ("latest_alt", "number", "最新ALT"),
        ("latest_ast", "number", "最新AST"),
        ("latest_creatinine", "number", "最新肌酐"),
        ("latest_uric_acid", "number", "最新尿酸"),
        ("liver_kidney_record_date", "datetime", "肝肾记录日期"),
        ("last_updated", "datetime", "最后更新时间"),
    ],
}


def get_access_token():
    """获取飞书访问令牌"""
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return result["tenant_access_token"]
        else:
            print(f"获取token失败: {result}")
            return None
    except Exception as e:
        print(f"请求token异常: {e}")
        return None


def list_tables(app_token, token):
    """列出Bitable中所有表"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return result["data"]["items"]
        else:
            print(f"列取表失败: {result}")
            return []
    except Exception as e:
        print(f"请求表列表异常: {e}")
        return []


def create_table(app_token, token, table_name, description=""):
    """创建新表"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "table": {
            "name": table_name,
            "description": description
        }
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return result["data"]["table_id"]
        else:
            return None
    except Exception as e:
        return None


def create_field(app_token, table_id, token, field_name, field_type, description="", options=None):
    """创建字段"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 转换字段类型为API数字ID
    api_field_type = FIELD_TYPE_MAP.get(field_type, 1)  # 默认为text(1)
    
    field_data = {
        "field_name": field_name,
        "type": api_field_type
    }
    
    # 处理特殊类型属性
    if field_type in ("select", "single_select") and options:
        field_data["property"] = {
            "options": [{"name": opt} for opt in options]
        }
    elif field_type == "multi_select" and options:
        field_data["property"] = {
            "options": [{"name": opt} for opt in options]
        }
    elif field_type == "checkbox":
        # checkbox 不需要 property 字段
        pass
    elif field_type == "number":
        field_data["property"] = {"formatter": "0"}
    elif field_type == "datetime":
        # datetime 不需要 property
        pass
    
    try:
        resp = requests.post(url, headers=headers, json=field_data, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return True, None
        else:
            return False, result.get("msg", str(result))
    except Exception as e:
        return False, str(e)


def sync_single_bitable(app_token, bitable_name, token):
    """同步单个Bitable"""
    print(f"\n{'='*60}")
    print(f"同步: {bitable_name}")
    print(f"{'='*60}")
    
    # 获取现有表
    existing_tables = list_tables(app_token, token)
    existing_table_names = {t["name"]: t["table_id"] for t in existing_tables}
    
    print(f"\n现有表: {list(existing_table_names.keys())}")
    
    # 需要创建的表
    tables_to_create = {
        "原始报告": "raw_reports",
        "报告主表": "reports_master",
        "指标明细": "indicators_detail",
        "健康主档案": "health_master",
    }
    
    created_tables = {}
    
    # 创建表
    for table_name, table_key in tables_to_create.items():
        if table_name in existing_table_names:
            print(f"\n  [已存在] {table_name}")
            created_tables[table_key] = existing_table_names[table_name]
        else:
            print(f"\n  [创建] {table_name}...")
            table_id = create_table(app_token, token, table_name, tables_to_create[table_name])
            if table_id:
                print(f"    成功: {table_id}")
                created_tables[table_key] = table_id
            else:
                print(f"    失败")
    
    # 创建字段
    print(f"\n{'='*60}")
    print("创建字段")
    print(f"{'='*60}")
    
    for table_key, table_id in created_tables.items():
        if table_key not in NEW_TABLES_FIELDS:
            continue
        
        print(f"\n  表: {table_key}")
        fields = NEW_TABLES_FIELDS[table_key]
        
        for field_name, field_type, field_desc in fields:
            # 检查是否有选项
            options = None
            if field_type == "select" and field_name in ["patient_gender", "table_risk_level", "archive_status", "abnormal_flag", "review_priority"]:
                if field_name == "patient_gender":
                    options = ["男", "女"]
                elif field_name == "table_risk_level":
                    options = ["low", "medium", "high"]
                elif field_name == "archive_status":
                    options = ["pending", "archived", "rejected", "manual_review"]
                elif field_name == "abnormal_flag":
                    options = ["正常", "偏高", "偏低", "阳性", "阴性"]
                elif field_name == "review_priority":
                    options = ["low", "medium", "high"]
            
            success, error = create_field(app_token, table_id, token, field_name, field_type, field_desc, options)
            
            if success:
                print(f"    + {field_name} ({field_type})")
            else:
                # 字段可能已存在
                error_str = str(error).lower()
                if "field_name already exist" in error_str or "exists" in error_str or "FieldNameDuplicated" in str(error):
                    print(f"    = {field_name} (已存在)")
                else:
                    print(f"    ! {field_name} (错误: {error})")
    
    print(f"\n{'='*60}")
    print(f"{bitable_name} 同步完成")
    print(f"{'='*60}")
    
    return created_tables


def main():
    print("=" * 60)
    print("LifeOS Bitable 字段同步脚本 v2.1")
    print("同步医疗报告归档 v1.1.0 新增表和字段")
    print("=" * 60)
    
    # 获取访问令牌
    print("\n【1/3】获取飞书访问令牌...")
    token = get_access_token()
    if not token:
        print("[失败] 获取令牌失败，退出")
        return
    print("[成功] 获取令牌成功")
    
    # 同步每个Bitable
    print("\n【2/3】同步各家庭成员Bitable...")
    results = {}
    for bitable_key, config in BITABLE_CONFIGS.items():
        result = sync_single_bitable(config["app_token"], config["name"], token)
        results[bitable_key] = result
    
    # 总结
    print("\n【3/3】同步结果汇总")
    print("=" * 60)
    for bitable_key, result in results.items():
        print(f"\n{BITABLE_CONFIGS[bitable_key]['name']}:")
        for table_key, table_id in result.items():
            print(f"  • {table_key}: {table_id}")
    
    print("\n" + "=" * 60)
    print("同步完成！请检查飞书Bitable确认表和字段已创建")
    print("=" * 60)


if __name__ == "__main__":
    main()
