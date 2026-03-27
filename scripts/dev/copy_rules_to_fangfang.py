#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import time

APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"

JIN_APP_TOKEN = "DtWnbquyZaIj9xsWLSIcagjQnAc"
FANGFANG_APP_TOKEN = "Y2pxbRjm8avmLUsnH8jc2K5rnHL"

# 芳芳的表 ID
FANGFANG_TABLES = {
    "profile": "tbl6sw7TZ4XyMruk",
    "规则": "tblFQXpFCcM2njxZ",
}

BASE_URL = "https://open.feishu.cn/open-apis"

def get_token():
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=30)
    return resp.json().get("tenant_access_token")

def get_records(token, app_token, table_id):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("items", [])
    return []

def create_record(token, app_token, table_id, fields):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"fields": fields}
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    result = resp.json()
    return result

def main():
    print("="*60)
    print("复制数据到芳芳的 Bitable")
    print("="*60)
    
    token = get_token()
    print(f"Token: {'OK' if token else 'FAIL'}\n")
    
    # 1. 创建芳芳的 profile
    print("[Step 1] 创建芳芳的 profile")
    profile_fields = {
        "profile_id": "002",
        "name": "芳芳",
        "remark": "群聊中的家庭成员，金的妻子"
    }
    result = create_record(token, FANGFANG_APP_TOKEN, FANGFANG_TABLES["profile"], profile_fields)
    if result.get("code") == 0:
        print(f"  [OK] Profile 创建成功")
    else:
        print(f"  [FAIL] Profile: {result.get('msg')}")
    
    print()
    
    # 2. 复制 rules
    print("[Step 2] 复制 rules 内容")
    
    # 读取金的 rules
    jin_rules = get_records(token, JIN_APP_TOKEN, "tbl2Sbdeq3jXx4Lf")
    print(f"  读取金的规则: {len(jin_rules)} 条")
    
    # 获取芳芳 rules 表的字段
    fangfang_rules_fields = get_records(token, FANGFANG_APP_TOKEN, FANGFANG_TABLES["规则"])
    fangfang_field_names = [f.get("field_name") for f in fangfang_rules_fields]
    print(f"  芳芳规则表字段: {fangfang_field_names}")
    
    # 复制每条规则
    success = 0
    for rule in jin_rules:
        fields = rule.get("fields", {})
        
        # 构建复制字段
        copy_fields = {}
        for fname in fangfang_field_names:
            if fname in fields and fname not in ["rule_id", "created_at", "updated_at"]:
                copy_fields[fname] = fields[fname]
        
        # 修改 rule_id
        if "rule_id" in copy_fields:
            copy_fields["rule_id"] = str(copy_fields["rule_id"]) + "_jin_copy"
        
        result = create_record(token, FANGFANG_APP_TOKEN, FANGFANG_TABLES["规则"], copy_fields)
        if result.get("code") == 0:
            success += 1
            print(f"  [OK] {copy_fields.get('rule_name', 'unknown')}")
        else:
            print(f"  [FAIL] {copy_fields.get('rule_name', 'unknown')}: {result.get('msg')}")
        
        time.sleep(0.2)
    
    print()
    print("="*60)
    print(f"完成！复制了 {success}/{len(jin_rules)} 条规则")
    print("="*60)

if __name__ == "__main__":
    main()
