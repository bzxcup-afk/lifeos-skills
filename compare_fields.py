#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"

JIN_APP_TOKEN = "DtWnbquyZaIj9xsWLSIcagjQnAc"
FANGFANG_APP_TOKEN = "Y2pxbRjm8avmLUsnH8jc2K5rnHL"

BASE_URL = "https://open.feishu.cn/open-apis"

# 表 ID
JIN_RULES_TABLE = "tbl2Sbdeq3jXx4Lf"
FANGFANG_RULES_TABLE = "tblFQXpFCcM2njxZ"

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

def get_records(token, app_token, table_id):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("items", [])
    return []

def main():
    token = get_token()
    if not token:
        print("[ERROR] Token failed")
        return
    
    print("="*60)
    print("对比金的 rules 和芳芳 rules 的字段类型")
    print("="*60)
    
    # 获取金的字段
    jin_fields = get_fields(token, JIN_APP_TOKEN, JIN_RULES_TABLE)
    print("\n金的 rules 字段:")
    for f in jin_fields:
        print(f"  {f.get('field_name')}: type={f.get('type')}, property={f.get('property')}")
    
    # 获取芳芳的字段
    fangfang_fields = get_fields(token, FANGFANG_APP_TOKEN, FANGFANG_RULES_TABLE)
    print("\n芳芳的 rules 字段:")
    for f in fangfang_fields:
        print(f"  {f.get('field_name')}: type={f.get('type')}, property={f.get('property')}")
    
    # 对比差异
    print("\n差异分析:")
    jin_field_names = {f.get('field_name'): f for f in jin_fields}
    fangfang_field_names = {f.get('field_name'): f for f in fangfang_fields}
    
    for name, jin_f in jin_field_names.items():
        if name in fangfang_field_names:
            ff = fangfang_field_names[name]
            if jin_f.get('type') != ff.get('type'):
                print(f"  类型不同: {name} - 金={jin_f.get('type')}, 芳芳={ff.get('type')}")
        else:
            print(f"  芳芳缺少字段: {name}")
    
    # 查看金的规则记录中的数字字段值
    print("\n金的 rules 记录中的数字字段值:")
    jin_records = get_records(token, JIN_APP_TOKEN, JIN_RULES_TABLE)
    for r in jin_records[:3]:
        fields = r.get('fields', {})
        priority = fields.get('priority')
        confidence = fields.get('confidence')
        success_rate = fields.get('success_rate')
        print(f"  {fields.get('rule_name')}: priority={priority}(type={type(priority)}), confidence={confidence}(type={type(confidence)})")
    
    print("="*60)

if __name__ == "__main__":
    main()
