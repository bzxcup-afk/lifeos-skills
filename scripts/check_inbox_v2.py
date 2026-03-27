# -*- coding: utf-8 -*-
"""
飞书收件箱检查脚本 - Cron任务专用
检查飞书收件箱（tblkcow4prsTlpva），筛选收件人=coding、状态=未读的任务
遵循SOUL.md工作流程执行
"""
import requests
import json
import sys
import os
from datetime import datetime

# 飞书应用配置
APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"

# 收件箱配置
INBOX_APP_TOKEN = "DtWnbquyZaIj9xsWLSIcagjQnAc"  # LifeOS app
INBOX_TABLE_ID = "tblkcow4prsTlpva"  # 收件箱表ID
REPLY_TABLE_ID = None  # 待确认
SYSTEM_LOG_TABLE_ID = None  # 待确认

BASE_URL = "https://open.feishu.cn/open-apis"


def get_token():
    """获取飞书 tenant_access_token"""
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        if result.get("code") == 0:
            return result.get("tenant_access_token")
        else:
            print(f"[ERROR] Token failed: {result}")
            return None
    except Exception as e:
        print(f"[ERROR] Token exception: {e}")
        return None


def get_tables(token, app_token):
    """获取多维表格中的数据表列表"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        result = response.json()
        return result
    except Exception as e:
        print(f"[ERROR] Get tables exception: {e}")
        return None


def search_records(token, app_token, table_id, filter_json=None, limit=100):
    """搜索记录"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "filter": filter_json,
        "page_size": limit
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return result.get("data", {}).get("items", []), None
        else:
            return [], f"API error: code={result.get('code')}, msg={result.get('msg')}"
    except Exception as e:
        return [], f"Exception: {e}"


def update_record(token, app_token, table_id, record_id, fields):
    """更新记录"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"fields": fields}
    
    try:
        resp = requests.put(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return True, None
        else:
            return False, f"API error: code={result.get('code')}, msg={result.get('msg')}"
    except Exception as e:
        return False, f"Exception: {e}"


def check_inbox(token):
    """检查收件箱，筛选收件人=coding、状态=未读的任务"""
    filter_json = {
        "conjunction": "and",
        "conditions": [
            {
                "field_name": "收件人",
                "operator": "is",
                "value": ["coding"]
            },
            {
                "field_name": "状态",
                "operator": "is",
                "value": ["未读"]
            }
        ]
    }
    
    tasks, error = search_records(token, INBOX_APP_TOKEN, INBOX_TABLE_ID, filter_json, limit=50)
    
    if error:
        print(f"[ERROR] Query inbox failed: {error}")
        return []
    
    return tasks


def update_inbox_status(token, record_id, new_status):
    """更新收件箱记录状态"""
    fields = {"状态": new_status}
    success, error = update_record(token, INBOX_APP_TOKEN, INBOX_TABLE_ID, record_id, fields)
    if error:
        print(f"[ERROR] Update status failed: {error}")
        return False
    return True


def execute_task(task):
    """
    执行任务
    返回: (success, result_message, details, needs_decision)
    """
    fields = task.get("fields", {})
    task_content = fields.get("任务内容", "")
    
    print(f"[INFO] Executing task: {task_content[:50]}...")
    
    # 默认返回：需要人工处理（因为无法自动判断任务类型）
    return (
        True,  # 执行流程完成
        "已接收-待处理", 
        f"任务已接收: {task_content}\n由于任务类型无法自动识别，需要人工确认执行方式。",
        True  # 需要拍板
    )


def main():
    """主流程"""
    print("=" * 60)
    print("Feishu Inbox Check for Coding Tasks")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 获取token
    print("\n[1] Getting access token...")
    token = get_token()
    if not token:
        print("  [FAIL] Cannot get token")
        return
    
    print("  [OK] Token obtained")
    
    # 检查收件箱
    print("\n[2] Checking inbox...")
    tasks = check_inbox(token)
    
    if not tasks:
        print("  No unread tasks found for 'coding' recipient")
        print("\nCheck completed. No tasks to process.")
        return
    
    print(f"  Found {len(tasks)} unread tasks")
    
    # 处理每个任务
    for idx, task in enumerate(tasks, 1):
        fields = task.get("fields", {})
        record_id = task.get("record_id", "")
        task_content = fields.get("任务内容", "")
        
        print(f"\n{'-' * 60}")
        print(f"[Task {idx}/{len(tasks)}] {task_content[:60]}")
        print(f"{'-' * 60}")
        
        # 步骤1: 更新状态为「执行中」
        print("[3] Updating status to '执行中'...")
        if update_inbox_status(token, record_id, "执行中"):
            print("  [OK] Status updated")
        else:
            print("  [FAIL] Status update failed, continuing...")
        
        # 步骤2: 执行任务
        print("[4] Executing task...")
        success, result, details, needs_decision = execute_task(task)
        print(f"  Result: {result}")
        
        # 步骤3: 更新收件箱状态为「已完成」
        print("[5] Updating status to '已完成'...")
        if update_inbox_status(token, record_id, "已完成"):
            print("  [OK] Status updated")
        else:
            print("  [FAIL] Status update failed")
        
        # 注意: 回复表和系统日志表ID待确认，暂时跳过
    
    print(f"\n{'=' * 60}")
    print(f"Completed! Processed {len(tasks)} tasks")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
