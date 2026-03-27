#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书收件箱中的未读任务
"""

import requests
import json
import os
import sys

BASE_URL = "https://open.feishu.cn/open-apis"

# 应用凭证
APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"

# 收件箱表ID - 从cron任务提供
INBOX_TABLE_ID = "tblkcow4prsTlpva"
APP_TOKEN = "DtWnbquyZaIj9xsWLSIcagjQnAc"

def get_token():
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result["tenant_access_token"]
    return None

def list_tables(token):
    """列出所有表"""
    url = f"{BASE_URL}/bitable/v1/apps/{APP_TOKEN}/tables"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        result = resp.json()
        print(f"List tables response: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        print(f"Error listing tables: {e}")
        return None

def read_inbox_records(token, filterformula=None, limit=100):
    """读取收件箱表记录"""
    url = f"{BASE_URL}/bitable/v1/apps/{APP_TOKEN}/tables/{INBOX_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": limit}
    
    if filterformula:
        params["filter"] = filterformula
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        result = resp.json()
        print(f"Read records response: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if result.get("code") == 0:
            return result.get("data", {}).get("items") or [], None
        return None, f"Error {result.get('code')}: {result.get('msg')}"
    except Exception as e:
        return None, str(e)

def update_record(token, record_id, fields):
    """更新记录"""
    url = f"{BASE_URL}/bitable/v1/apps/{APP_TOKEN}/tables/{INBOX_TABLE_ID}/records/{record_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"fields": fields}
    
    try:
        resp = requests.put(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        print(f"Update record response: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if result.get("code") == 0:
            return True, None
        return False, f"Error {result.get('code')}: {result.get('msg')}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("检查飞书收件箱 - 未读任务")
    print("=" * 60)
    print(f"APP_TOKEN: {APP_TOKEN}")
    print(f"INBOX_TABLE_ID: {INBOX_TABLE_ID}")
    print()
    
    token = get_token()
    if not token:
        print("[ERROR] Failed to get token")
        sys.exit(1)
    
    print("[OK] Token获取成功")
    print()
    
    # 先列出所有表，看看能否访问
    print("=" * 60)
    print("步骤1: 列出所有表")
    print("=" * 60)
    list_result = list_tables(token)
    print()
    
    # 尝试读取收件箱记录
    print("=" * 60)
    print("步骤2: 读取收件箱记录（无筛选）")
    print("=" * 60)
    records, err = read_inbox_records(token, limit=10)
    if err:
        print(f"[ERROR] 读取收件箱失败: {err}")
    elif not records:
        print("[INFO] 收件箱中没有记录")
    else:
        print(f"[INFO] 发现 {len(records)} 条记录")
        for record in records:
            fields = record.get("fields", {})
            record_id = record.get("record_id")
            print(f"\n记录ID: {record_id}")
            for k, v in fields.items():
                print(f"  {k}: {v}")
    print()
    
    # 尝试筛选
    print("=" * 60)
    print("步骤3: 读取未读任务（收件人=coding, 状态=未读）")
    print("=" * 60)
    filter_formula = 'AND(CurrentValue.[收件人]="coding", CurrentValue.[状态]="未读")'
    records, err = read_inbox_records(token, filterformula=filter_formula, limit=50)
    if err:
        print(f"[ERROR] 读取未读任务失败: {err}")
    elif not records:
        print("[INFO] 没有符合条件的未读任务")
    else:
        print(f"[INFO] 发现 {len(records)} 条未读任务")
    print()
    
    print("=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
