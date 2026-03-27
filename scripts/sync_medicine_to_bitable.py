#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 medicine_plans.json 到 medication_supplement_list Bitable 表
"""

import json
import os
import sys
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitable_ops import get_token, create_record, update_record, read_records, get_current_app_token


def load_medicine_plans(file_path):
    """加载 medicine_plans.json 文件"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print("文件为空")
                return []
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return []
    except Exception as e:
        print(f"读取文件错误: {e}")
        return []


def map_time_slot_to_timing(time_slot):
    """将 time_slot 映射到 timing 字段"""
    mapping = {
        "起床后": "早餐前",
        "早餐前": "早餐前",
        "早餐后": "早餐后",
        "午餐前": "午餐前",
        "午餐后": "午餐后",
        "晚餐前": "晚餐前",
        "晚餐后": "晚餐后",
        "睡前": "睡前"
    }
    return mapping.get(time_slot, time_slot)


def create_medication_record(drug_info, profile_id="001"):
    """
    创建 medication_supplement_list 记录字段
    
    从 JSON 中的字段映射到 Bitable 字段
    """
    # 从 drug_info 中提取基本信息
    drug_name = drug_info.get("drug_name", "")
    time_slot = drug_info.get("time_slot", "")
    active = drug_info.get("active", True)
    
    # 判断是药品还是补剂（简单规则：常见补剂名称）
    supplement_keywords = ["鱼油", "维生素", "VK", "VC", "VD", "VA", "VB", "镁", "锌", "钙", 
                          "辅酶", "Q10", "益生菌", "益生元", "胶原蛋白", "叶黄素", "氨糖",
                          "AKG", "alpha", "酮戊二酸", "NMN", "NAD", "硫辛酸", "肌酸", "BCAA"]
    
    is_supplement = any(keyword.lower() in drug_name.lower() for keyword in supplement_keywords)
    item_type = "补剂" if is_supplement else "药品"
    
    # 映射时间槽到 timing
    timing = map_time_slot_to_timing(time_slot)
    
    # 构建 dosage（用量）字段 - 从 drug_name 中尝试提取剂量信息
    dosage = ""
    # 常见剂量模式：数字+单位，如 10mg, 500mg, 1000IU 等
    import re
    dose_match = re.search(r'(\d+\s*(mg|g|μg|mcg|IU|ml|毫升|片|粒|粒|颗|支|瓶))', drug_name, re.IGNORECASE)
    if dose_match:
        dosage = dose_match.group(1)
    
    # 构建 fields 字典
    fields = {
        "item_id": drug_info.get("id", ""),
        "profile_id": profile_id,
        "name": drug_name,
        "item_type": item_type,
        "dosage": dosage,
        "frequency": "每天",
        "timing": [timing],  # 多选字段需要传入数组
        "with_food": "随餐" if is_supplement else "均可",
        "purpose": f"由用户设定，服用时间：{time_slot}",
        "source_type": "用户设定",
        "status": "启用" if active else "暂停",
        "notes": f"来源：{drug_info.get('channel_type', 'unknown')} 渠道"
    }
    
    return fields


def sync_to_bitable(plans, profile_id="001", app_token=None):
    """
    同步药品计划到 Bitable
    
    策略：
    1. 先读取 Bitable 中现有的记录
    2. 对每个计划，检查是否已存在（根据 name + timing 判断）
    3. 如果不存在，创建新记录
    4. 如果存在但内容有变化，更新记录
    """
    token = get_token()
    if not token:
        print("获取 Token 失败")
        return False
    
    table_key = "medication_supplement_list"
    
    # 读取现有记录
    existing_records, _ = read_records(token, app_token, table_key, limit=100)
    if existing_records is None:
        existing_records = []
    
    # 构建已存在记录的索引（name + timing）
    existing_index = {}
    for rec in existing_records:
        fields = rec.get('fields', {})
        name = fields.get('name', '')
        timing = fields.get('timing', '')
        key = f"{name}_{timing}"
        existing_index[key] = rec['record_id']
    
    # 同步每个计划
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for plan in plans:
        fields = create_medication_record(plan, profile_id)
        key = f"{fields['name']}_{fields['timing']}"
        
        # 检查是否已存在
        if key in existing_index:
            # 更新现有记录
            record_id = existing_index[key]
            success, result = update_record(token, table_key, record_id, fields)
            if success:
                updated_count += 1
                print(f"更新记录: {fields['name']} ({fields['timing']})")
            else:
                print(f"更新失败: {fields['name']} - {result}")
        else:
            # 创建新记录
            success, result = create_record(token, table_key, fields)
            if success:
                created_count += 1
                print(f"创建记录: {fields['name']} ({fields['timing']})")
            else:
                print(f"创建失败: {fields['name']} - {result}")
    
    print(f"\n同步完成: 创建 {created_count} 条, 更新 {updated_count} 条, 跳过 {skipped_count} 条")
    return True


def main():
    """主函数"""
    # 确定 medicine_plans.json 的路径
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plans_file = os.path.join(script_dir, 'medicine', 'medicine_plans.json')
    
    print(f"加载药品计划文件: {plans_file}")
    
    # 加载计划
    plans = load_medicine_plans(plans_file)
    if not plans:
        print("没有药品计划需要同步")
        return
    
    print(f"找到 {len(plans)} 条药品计划")
    
    # 同步到 Bitable
    sync_to_bitable(plans, profile_id="001")


if __name__ == '__main__':
    main()
