# -*- coding: utf-8 -*-
"""Find app_token for the inbox table"""
import requests
import json
import os

BASE_URL = "https://open.feishu.cn/open-apis"
APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"
TARGET_TABLE = "tblkcow4prsTlpva"

# Get token
resp = requests.post(f"{BASE_URL}/auth/v3/tenant_access_token/internal", 
                     json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=30)
token = resp.json().get("tenant_access_token")
print(f"Token: {token[:30]}...")

# Known app_tokens to try
app_tokens = [
    "DtWnbquyZaIj9xsWLSIcagjQnAc",  # lifeos_jin
    "ILxkbi8gwaQBK4srjcSczYWZncb",  # lifeos_laolao
    "LDk3b3PGtaGbDVsjOV1cavxun2g",  # lifeos_laoma
    "Y2pxbRjm8avmLUsnH8jc2K5rnHL",  # lifeos_fangfang
]

headers = {"Authorization": f"Bearer {token}"}

for app_token in app_tokens:
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{TARGET_TABLE}/records"
    params = {"page_size": 1}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        result = resp.json()
        code = result.get("code")
        if code == 0:
            print(f"SUCCESS! app_token: {app_token}")
            print(f"Response: {json.dumps(result, ensure_ascii=False)[:500]}")
            break
        else:
            print(f"app_token {app_token}: code={code}, msg={result.get('msg', '')[:100]}")
    except Exception as e:
        print(f"app_token {app_token}: error={e}")
else:
    print("Table not found in any known app_token")
