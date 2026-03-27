#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"
FANGFANG_APP_TOKEN = "Y2pxbRjm8avmLUsnH8jc2K5rnHL"
BASE_URL = "https://open.feishu.cn/open-apis"

def get_token():
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=30)
    return resp.json().get("tenant_access_token")

def create_record(token, app_token, table_id, fields):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"fields": fields}
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    return resp.json()

token = get_token()
print(f"Token: {'OK' if token else 'FAIL'}")

# 芳芳 profile 表 ID
PROFILE_TABLE = "tbl6sw7TZ4XyMruk"

print("\n尝试创建芳芳的 profile...")
result = create_record(token, FANGFANG_APP_TOKEN, PROFILE_TABLE, {
    "name": "芳芳"
})
print(f"Result: code={result.get('code')}, msg={result.get('msg')}")
if result.get('code') != 0:
    print(f"详细: {result}")
