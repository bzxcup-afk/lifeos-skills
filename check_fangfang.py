#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import time

APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"

FANGFANG_APP_TOKEN = "Y2pxbRjm8avmLUsnH8jc2K5rnHL"
BASE_URL = "https://open.feishu.cn/open-apis"

def get_token():
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=30)
    return resp.json().get("tenant_access_token")

def list_tables(token, app_token):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("items", [])
    return []

token = get_token()
print(f"Token: {'OK' if token else 'FAIL'}")

print("\n芳芳 Bitable 中已有的表:")
tables = list_tables(token, FANGFANG_APP_TOKEN)
for t in tables:
    print(f"  - {t.get('name')}: {t.get('table_id')}")
print(f"\n共 {len(tables)} 个表")
