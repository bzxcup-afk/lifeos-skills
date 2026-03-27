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
    return resp.json()

def create_table(token, app_token, name):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"table": {"name": name}}
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    return resp.json()

token = get_token()
print(f"Token: {'OK' if token else 'FAIL'}")

# 先尝试列出芳芳的表
print("\n尝试访问芳芳的 Bitable...")
result = list_tables(token, FANGFANG_APP_TOKEN)
print(f"结果: code={result.get('code')}, msg={result.get('msg')}")

# 尝试创建一个测试表
print("\n尝试创建测试表...")
result = create_table(token, FANGFANG_APP_TOKEN, "测试表")
print(f"结果: code={result.get('code')}, msg={result.get('msg')}")
if result.get('code') != 0:
    print(f"详细错误: {result}")
