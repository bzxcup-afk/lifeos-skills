# -*- coding: utf-8 -*-
import json
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"
BASE_URL = "https://open.feishu.cn/open-apis"
APP_TOKEN = "UwMYbYWtzaqvbEsx5yTctzhWnqb"
INBOX_TABLE_ID = "tblkcow4prsTlpva"

def get_app_token():
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    resp.raise_for_status()
    return resp.json()["tenant_access_token"]

def list_records(token, table_id, filter_obj=None):
    url = f"{BASE_URL}/bitable/v1/apps/{APP_TOKEN}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": 100}
    if filter_obj:
        params["filter"] = json.dumps(filter_obj)
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    return resp.json()

token = get_app_token()
print(f"Token: {token[:20]}...")

# Build filter as dict (not formula string)
# Feishu API expects filter as JSON string
filter_obj = {
    "conjunction": "and",
    "conditions": [
        {"field_name": "收件人", "operator": "is", "value": ["coding"]},
        {"field_name": "状态", "operator": "is", "value": ["未读"]}
    ]
}

print(f"\n=== Filter: {json.dumps(filter_obj, ensure_ascii=False)} ===")
result = list_records(token, INBOX_TABLE_ID, filter_obj)
print(f"Code: {result.get('code')}, Msg: {result.get('msg')}")
if result.get("code") == 0:
    items = result.get("data", {}).get("items", [])
    print(f"Found {len(items)} records")
    for item in items:
        fields = item.get("fields", {})
        print(f"  [{item.get('record_id')}] {json.dumps(fields, ensure_ascii=False)}")
else:
    print(f"Full result: {json.dumps(result, ensure_ascii=False)}")

# Also check the existing coding tasks to understand current state
print(f"\n=== All coding tasks (any status) ===")
all_filter = {
    "conjunction": "and", 
    "conditions": [
        {"field_name": "收件人", "operator": "is", "value": ["coding"]}
    ]
}
result2 = list_records(token, INBOX_TABLE_ID, all_filter)
if result2.get("code") == 0:
    items = result2.get("data", {}).get("items", [])
    print(f"Found {len(items)} records for coding")
    for item in items:
        fields = item.get("fields", {})
        print(f"  [{item.get('record_id')}] 状态={fields.get('状态')} 指令={fields.get('指令', '')[:80]}")
