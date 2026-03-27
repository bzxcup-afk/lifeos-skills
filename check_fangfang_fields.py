#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"
FANGFANG_APP_TOKEN = "Y2pxbRjm8avmLUsnH8jc2K5rnHL"
BASE_URL = "https://open.feishu.cn/open-apis"

def get_token():
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=30)
    return resp.json().get("tenant_access_token")

def get_fields(token, app_token, table_id):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("items", [])
    return []

def get_records(token, app_token, table_id, limit=5):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": limit}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("items", [])
    return []

# 芳芳的表
FANGFANG_TABLES = {
    "profile": "tbl6sw7TZ4XyMruk",  # 家庭成员表
    "规则": "tblFQXpFCcM2njxZ",
}

token = get_token()
print(f"Token: {'OK' if token else 'FAIL'}\n")

# 查看家庭成员表字段
print("="*60)
print("芳芳的'家庭成员表'字段:")
print("="*60)
fields = get_fields(token, FANGFANG_APP_TOKEN, FANGFANG_TABLES["profile"])
for f in fields:
    print(f"  - {f.get('field_name')} (type={f.get('type')})")

print("\n前3条记录:")
records = get_records(token, FANGFANG_APP_TOKEN, FANGFANG_TABLES["profile"], limit=3)
for r in records:
    print(f"  {r.get('fields')}")

# 查看规则表字段
print("\n" + "="*60)
print("芳芳的'规则'表字段:")
print("="*60)
fields = get_fields(token, FANGFANG_APP_TOKEN, FANGFANG_TABLES["规则"])
for f in fields:
    print(f"  - {f.get('field_name')} (type={f.get('type')})")

print("\n前3条记录:")
records = get_records(token, FANGFANG_APP_TOKEN, FANGFANG_TABLES["规则"], limit=3)
for r in records:
    print(f"  {json.dumps(r.get('fields'), ensure_ascii=False)}")
