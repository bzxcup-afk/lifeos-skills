#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探测飞书收件箱应用中的表结构
"""

import requests
import os

BASE_URL = "https://open.feishu.cn/open-apis"
INBOX_APP_TOKEN = "DtWnbquyZaIj9xsWLSIcagjQnAc"

DEFAULT_APP_ID = "cli_a92ed6e39938dbd2"
DEFAULT_APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"

APP_ID = os.getenv("LIFEOS_FEISHU_APP_ID", DEFAULT_APP_ID)
APP_SECRET = os.getenv("LIFEOS_FEISHU_APP_SECRET", DEFAULT_APP_SECRET)


def get_token():
    """获取飞书访问令牌"""
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            return result.get("tenant_access_token")
        else:
            print(f"[ERROR] Token获取失败: {result}")
            return None
    except Exception as e:
        print(f"[ERROR] Token请求异常: {e}")
        return None


def list_tables(token, app_token):
    """列出应用中的所有表"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            tables = result.get("data", {}).get("items", [])
            return tables, None
        else:
            return [], f"API错误: {result}"
    except Exception as e:
        return [], f"请求异常: {e}"


def list_fields(token, app_token, table_id):
    """列出表中的所有字段"""
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            fields = result.get("data", {}).get("items", [])
            return fields, None
        else:
            return [], f"API错误: {result}"
    except Exception as e:
        return [], f"请求异常: {e}"


def main():
    print("=" * 60)
    print("飞书收件箱应用 - 表结构探测")
    print("=" * 60)
    
    token = get_token()
    if not token:
        print("[ERROR] 无法获取访问令牌")
        return
    
    print("\n[1] 获取应用中的所有表...")
    tables, error = list_tables(token, INBOX_APP_TOKEN)
    
    if error:
        print(f"[ERROR] {error}")
        return
    
    if not tables:
        print("  未发现任何表")
        return
    
    print(f"  发现 {len(tables)} 个表:\n")
    
    for table in tables:
        table_id = table.get("table_id", "")
        table_name = table.get("name", "")
        
        print(f"  【表名】{table_name}")
        print(f"  【表ID】{table_id}")
        print()
        
        # 获取字段信息
        print(f"  [字段列表]")
        fields, field_error = list_fields(token, INBOX_APP_TOKEN, table_id)
        
        if field_error:
            print(f"    [ERROR] {field_error}")
        else:
            for field in fields:
                field_name = field.get("field_name", "")
                field_type = field.get("field_type", "")
                print(f"    - {field_name} ({field_type})")
        
        print("\n" + "-" * 50 + "\n")


if __name__ == "__main__":
    main()
