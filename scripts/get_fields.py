# -*- coding: utf-8 -*-
import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"
BASE_URL = "https://open.feishu.cn/open-apis"
APP_TOKEN = "UwMYbYWtzaqvbEsx5yTctzhWnqb"
INBOX_TABLE_ID = "tblkcow4prsTlpva"

resp = requests.post(f"{BASE_URL}/auth/v3/tenant_access_token/internal", json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
token = resp.json()["tenant_access_token"]

url = f"{BASE_URL}/bitable/v1/apps/{APP_TOKEN}/tables/{INBOX_TABLE_ID}/fields"
resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
data = resp.json()
print("Fields result code:", data.get("code"))
for item in data.get("data", {}).get("items", []):
    print(f"field_id={item['field_id']}, field_name={repr(item['field_name'])}, type={item['type']}, ui_type={item['ui_type']}")
