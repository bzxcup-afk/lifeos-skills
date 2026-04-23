"""
scripts/check_medicine_reminders.py
药品提醒检查脚本 - 支持按时间槽触发并发送飞书消息
"""

import json
import os
import requests
from datetime import datetime
from typing import List, Dict, Any

# 飞书应用凭证
FEISHU_APP_ID = os.getenv("LIFEOS_FEISHU_APP_ID", "cli_a92ed6e39938dbd2")
FEISHU_APP_SECRET = os.getenv("LIFEOS_FEISHU_APP_SECRET", "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq")
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

# 时间槽 -> 触发时间（与干预计划时间对齐）
TIME_SLOT_TRIGGERS = {
    '起床后': 7,
    '早餐前': 7,
    '早餐后': 8,
    '午餐前': 11,
    '午餐后': 14,   # 与干预计划 14:00 对齐
    '晚餐前': 17,
    '晚餐后': 18,
    '睡前': 21      # 与干预计划 21:00 对齐
}

# ==================== 飞书 API ====================

def get_feishu_token() -> str:
    """获取飞书 tenant_access_token"""
    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }, timeout=30)
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取token失败: {data.get('msg')}")
    return data["tenant_access_token"]

def send_feishu_message(token: str, receive_id: str, channel_type: str, msg_type: str, content: str) -> dict:
    """发送飞书消息到群/私聊"""
    # channel_id 为 open_id（ou_ 开头）时用 user_id 类型；群 chat_id 用 chat_id 类型
    if receive_id.startswith("ou_"):
        receive_id_type = "open_id"
    else:
        receive_id_type = "chat_id"
    url = f"{FEISHU_API_BASE}/im/v1/messages?receive_id_type={receive_id_type}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "receive_id": receive_id,
        "msg_type": msg_type,
        "content": content
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    result = resp.json()
    if result.get("code") != 0:
        print(f"[feishu] 发送失败: receive_id={receive_id}, type={receive_id_type}, error={result.get('msg')}", flush=True)
    else:
        print(f"[feishu] 发送成功 -> {receive_id} ({receive_id_type})", flush=True)
    return result

def send_text_message(token: str, receive_id: str, channel_type: str, text: str) -> dict:
    """发送文本消息"""
    return send_feishu_message(token, receive_id, channel_type, "text", json.dumps({"text": text}))

def send_reminders_via_feishu(reminders: List[Dict[str, Any]]) -> int:
    """发送提醒列表到飞书，返回成功数量"""
    if not reminders:
        return 0
    
    try:
        token = get_feishu_token()
        success_count = 0
        for r in reminders:
            result = send_text_message(token, r["channel_id"], r["channel_type"], r["message"])
            if result.get("code") == 0:
                success_count += 1
        return success_count
    except Exception as e:
        print(f"[feishu] 发送失败: {e}", flush=True)
        return 0

# ==================== 时间槽检查 ====================

def get_current_time_slot() -> str | None:
    """获取当前时间对应的服药时间槽"""
    now = datetime.now()
    hour = now.hour
    
    # 按整点触发时间匹配
    for slot, trigger_hour in TIME_SLOT_TRIGGERS.items():
        if hour == trigger_hour:
            return slot
    return None

def get_slot_by_trigger_hour(trigger_hour: int) -> str | None:
    """根据触发小时获取时间槽"""
    for slot, hour in TIME_SLOT_TRIGGERS.items():
        if hour == trigger_hour:
            return slot
    return None

# ==================== 干预计划提醒 ====================

def get_intervention_reminders_by_hour(hour: int) -> List[Dict[str, Any]]:
    """检查干预计划中指定小时对应的提醒"""
    data_dir = get_data_dir()
    intervention_file = os.path.join(data_dir, 'intervention_plans.json')
    
    interventions = load_json(intervention_file, [])
    
    # 筛选活跃的、匹配小时的干预计划
    hour_str = f"{hour:02d}:00"
    relevant = [
        i for i in interventions
        if i.get('active') and i.get('time') == hour_str
    ]
    
    if not relevant:
        return []
    
    print(f"[intervention] 时间 {hour_str} 找到 {len(relevant)} 个活跃干预计划")
    
    reminders = []
    # 按渠道分组，每组只发一条消息
    channel_groups: Dict[str, List] = {}
    for item in relevant:
        key = f"{item.get('channel_id')}:{item.get('channel_type')}"
        if key not in channel_groups:
            channel_groups[key] = []
        channel_groups[key].append(item)
    
    for key, group in channel_groups.items():
        channel_id, channel_type = key.split(':')
        mention_target = group[0].get('mention_target', '')
        
        # 合并该组所有消息内容
        messages = [g.get('message', '') for g in group if g.get('message')]
        combined_message = '\n'.join(messages)
        
        # 群聊需要 @，私聊不需要
        if channel_type == 'group':
            if mention_target.startswith('<at'):
                final_msg = f"{mention_target}\n{combined_message}"
            else:
                final_msg = f"@{mention_target}\n{combined_message}"
        else:
            final_msg = combined_message
        
        reminders.append({
            'channel_id': channel_id,
            'channel_type': channel_type,
            'mention_target': mention_target,
            'message': final_msg
        })
        print(f"[intervention] 生成提醒: {channel_id} -> {combined_message[:50]}...")
    
    return reminders

def load_json(filepath: str, default: Any) -> Any:
    """安全读取JSON文件"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[medicine] 读取文件失败 {filepath}: {e}")
    return default

def get_data_dir() -> str:
    """获取 medicine 模块的数据目录"""
    return os.path.join(os.path.dirname(__file__), '..', 'medicine')

def check_reminders() -> List[Dict[str, Any]]:
    """检查并生成提醒"""
    current_slot = get_current_time_slot()
    
    if not current_slot:
        print(f"[medicine] 当前时间不在任何时间槽内")
        return []
    
    print(f"[medicine] 当前时间槽: {current_slot}")
    
    data_dir = get_data_dir()
    plans_file = os.path.join(data_dir, 'medicine_plans.json')
    records_file = os.path.join(data_dir, 'medicine_records.json')
    
    plans = load_json(plans_file, [])
    records = load_json(records_file, [])
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 筛选当前时间槽的活跃计划
    slot_plans = [
        p for p in plans 
        if p.get('active') and p.get('time_slot') == current_slot
    ]
    
    if not slot_plans:
        print(f"[medicine] 时间槽 {current_slot} 没有待提醒的计划")
        return []
    
    print(f"[medicine] 找到 {len(slot_plans)} 个计划")
    
    # 按渠道分组
    channel_groups: Dict[str, List] = {}
    for plan in slot_plans:
        key = f"{plan['channel_id']}:{plan['channel_type']}"
        if key not in channel_groups:
            channel_groups[key] = []
        channel_groups[key].append(plan)
    
    reminders = []
    
    for key, group_plans in channel_groups.items():
        channel_id, channel_type = key.split(':')
        
        # 确保今天的记录存在
        for plan in group_plans:
            # 检查是否已有今日记录
            has_record = any(
                r.get('plan_id') == plan['id'] and 
                r.get('date') == today and 
                r.get('time_slot') == current_slot
                for r in records
            )
            
            if not has_record:
                # 创建新记录
                new_record = {
                    'id': f"rec_{datetime.now().strftime('%Y%m%d%H%M%S')}_{plan['id']}",
                    'plan_id': plan['id'],
                    'user_id': plan['user_id'],
                    'drug_name': plan['drug_name'],
                    'date': today,
                    'time_slot': current_slot,
                    'status': 'pending'
                }
                records.append(new_record)
                print(f"[medicine] 创建记录: {new_record['id']}")
        
        # 检查是否有未完成的记录
        pending_records = [
            r for r in records 
            if r.get('date') == today and 
               r.get('time_slot') == current_slot and 
               r.get('status') == 'pending' and
               any(p['id'] == r['plan_id'] for p in group_plans)
        ]
        
        if not pending_records:
            continue
        
        # 生成提醒
        drugs = list({p['drug_name'] for p in group_plans})
        mention_target = group_plans[0].get('mention_target', '')
        
        # 构建提醒消息
        drugs_text = '\n'.join([f"- {d}" for d in drugs])
        
        if channel_type == 'group':
            # mention_target 可能是旧格式(纯文本名字)或新格式(<at user_id="ou_xxx">name</at>)
            # 新格式已包含 proper Feishu @mention，不需要额外加 @
            if mention_target.startswith('<at'):
                message = f"{mention_target}\n现在是{current_slot}服药时间\n今天需要服用：\n{drugs_text}"
            else:
                # 旧格式：纯文本名字，需要加 @ 前缀（兼容处理）
                message = f"@{mention_target}\n现在是{current_slot}服药时间\n今天需要服用：\n{drugs_text}"
        else:
            message = f"现在是{current_slot}服药时间\n今天需要服用：\n{drugs_text}"
        
        reminders.append({
            'channel_id': channel_id,
            'channel_type': channel_type,
            'mention_target': mention_target,
            'time_slot': current_slot,
            'drugs': drugs,
            'message': message
        })
        
        print(f"[medicine] 生成提醒: {channel_id} -> {drugs}")
    
    # 保存更新后的记录
    try:
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[medicine] 保存记录失败: {e}")
    
    return reminders

def mark_as_taken(user_id: str, time_slot: str) -> int:
    """标记指定用户和时间槽的药物为已服用"""
    data_dir = get_data_dir()
    records_file = os.path.join(data_dir, 'medicine_records.json')
    
    records = load_json(records_file, [])
    today = datetime.now().strftime('%Y-%m-%d')
    
    count = 0
    for record in records:
        if (record.get('user_id') == user_id and 
            record.get('time_slot') == time_slot and 
            record.get('date') == today and 
            record.get('status') == 'pending'):
            record['status'] = 'taken'
            record['taken_at'] = datetime.now().isoformat()
            count += 1
    
    if count > 0:
        try:
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            print(f"[medicine] 标记 {count} 条记录为已服用")
        except Exception as e:
            print(f"[medicine] 保存记录失败: {e}")
    
    return count

def check_by_time_slot(time_slot: str) -> List[Dict[str, Any]]:
    """检查指定时间槽的提醒"""
    print(f"[medicine] 检查时间槽: {time_slot}")
    
    data_dir = get_data_dir()
    plans_file = os.path.join(data_dir, 'medicine_plans.json')
    records_file = os.path.join(data_dir, 'medicine_records.json')
    
    plans = load_json(plans_file, [])
    records = load_json(records_file, [])
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 筛选该时间槽的活跃计划
    slot_plans = [
        p for p in plans 
        if p.get('active') and p.get('time_slot') == time_slot
    ]
    
    if not slot_plans:
        print(f"[medicine] 时间槽 {time_slot} 没有待提醒的计划")
        return []
    
    print(f"[medicine] 找到 {len(slot_plans)} 个计划")
    
    # 按渠道分组
    channel_groups: Dict[str, List] = {}
    for plan in slot_plans:
        key = f"{plan['channel_id']}:{plan['channel_type']}"
        if key not in channel_groups:
            channel_groups[key] = []
        channel_groups[key].append(plan)
    
    reminders = []
    
    for key, group_plans in channel_groups.items():
        channel_id, channel_type = key.split(':')
        
        # 确保今天的记录存在
        for plan in group_plans:
            has_record = any(
                r.get('plan_id') == plan['id'] and 
                r.get('date') == today and 
                r.get('time_slot') == time_slot
                for r in records
            )
            
            if not has_record:
                new_record = {
                    'id': f"rec_{datetime.now().strftime('%Y%m%d%H%M%S')}_{plan['id']}",
                    'plan_id': plan['id'],
                    'user_id': plan['user_id'],
                    'drug_name': plan['drug_name'],
                    'date': today,
                    'time_slot': time_slot,
                    'status': 'pending'
                }
                records.append(new_record)
                print(f"[medicine] 创建记录: {new_record['id']}")
        
        # 检查未完成的记录
        pending_records = [
            r for r in records 
            if r.get('date') == today and 
               r.get('time_slot') == time_slot and 
               r.get('status') == 'pending' and
               any(p['id'] == r['plan_id'] for p in group_plans)
        ]
        
        if not pending_records:
            continue
        
        drugs = list({p['drug_name'] for p in group_plans})
        mention_target = group_plans[0].get('mention_target', '')
        
        drugs_text = '\n'.join([f"- {d}" for d in drugs])
        
        if channel_type == 'group':
            # mention_target 可能是旧格式(纯文本名字)或新格式(<at user_id="ou_xxx">name</at>)
            # 新格式已包含 proper Feishu @mention，不需要额外加 @
            if mention_target.startswith('<at'):
                message = f"{mention_target}\n现在是{time_slot}服药时间\n今天需要服用：\n{drugs_text}"
            else:
                # 旧格式：纯文本名字，需要加 @ 前缀（兼容处理）
                message = f"@{mention_target}\n现在是{time_slot}服药时间\n今天需要服用：\n{drugs_text}"
        else:
            message = f"现在是{time_slot}服药时间\n今天需要服用：\n{drugs_text}"
        
        reminders.append({
            'channel_id': channel_id,
            'channel_type': channel_type,
            'mention_target': mention_target,
            'time_slot': time_slot,
            'drugs': drugs,
            'message': message
        })
        
        print(f"[medicine] 生成提醒: {channel_id} -> {drugs}")
    
    # 保存记录
    try:
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[medicine] 保存记录失败: {e}")
    
    return reminders

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'taken':
            # 标记已服用
            if len(sys.argv) > 3:
                user_id = sys.argv[2]
                time_slot = sys.argv[3]
                count = mark_as_taken(user_id, time_slot)
                print(f"已标记 {count} 条记录为已服用")
            else:
                print("用法: python check_medicine_reminders.py taken <user_id> <time_slot>")
            return
        
        elif sys.argv[1] == 'trigger':
            # 按时间槽触发并发送飞书消息（药品 + 干预）
            if len(sys.argv) > 2:
                time_slot = sys.argv[2]
            else:
                # 自动检测当前时间槽
                current_slot = get_current_time_slot()
                if not current_slot:
                    print("当前不在任何时间槽触发点")
                    return
                time_slot = current_slot
            
            # 1. 检查药品提醒
            medicine_reminders = check_by_time_slot(time_slot)
            
            # 2. 检查干预提醒（根据时间槽对应的小时）
            trigger_hour = TIME_SLOT_TRIGGERS.get(time_slot)
            intervention_reminders = []
            if trigger_hour is not None:
                intervention_reminders = get_intervention_reminders_by_hour(trigger_hour)
            
            # 合并所有提醒
            all_reminders = medicine_reminders + intervention_reminders
            
            if all_reminders:
                sent = send_reminders_via_feishu(all_reminders)
                print(f"飞书发送完成: {sent}/{len(all_reminders)} 条")
                if medicine_reminders:
                    print(f"  - 药品提醒: {len(medicine_reminders)} 条")
                if intervention_reminders:
                    print(f"  - 干预提醒: {len(intervention_reminders)} 条")
            else:
                print("无待发送提醒")
            return
        elif sys.argv[1] == 'list':
            # 列出所有时间槽触发时间
            print("=== 时间槽触发时间 ===")
            for slot, hour in TIME_SLOT_TRIGGERS.items():
                print(f"  {slot}: {hour}:00")
            return
        else:
            print("用法:")
            print("  python check_medicine_reminders.py trigger [时间槽]  # 触发提醒")
            print("  python check_medicine_reminders.py taken <user_id> <time_slot>  # 标记已服用")
            print("  python check_medicine_reminders.py list  # 列出触发时间")
            return
    else:
        # 默认：检查当前时间槽（药品 + 干预）
        current_slot = get_current_time_slot()
        if not current_slot:
            print("当前不在任何时间槽触发点")
            return
        
        # 1. 检查药品提醒
        medicine_reminders = check_by_time_slot(current_slot)
        
        # 2. 检查干预提醒
        trigger_hour = TIME_SLOT_TRIGGERS.get(current_slot)
        intervention_reminders = []
        if trigger_hour is not None:
            intervention_reminders = get_intervention_reminders_by_hour(trigger_hour)
        
        all_reminders = medicine_reminders + intervention_reminders
    
    if all_reminders:
        print(f"\n=== 需要发送 {len(all_reminders)} 条提醒 ===")
        print(json.dumps(all_reminders, ensure_ascii=False, indent=2))
    else:
        print("无待发送提醒")

if __name__ == '__main__':
    main()
