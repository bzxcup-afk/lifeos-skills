#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import time

APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"

JIN_APP_TOKEN = "DtWnbquyZaIj9xsWLSIcagjQnAc"
FANGFANG_APP_TOKEN = "Y2pxbRjm8avmLUsnH8jc2K5rnHL"

FANGFANG_RULES_TABLE = "tblFQXpFCcM2njxZ"
JIN_RULES_TABLE = "tbl2Sbdeq3jXx4Lf"

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
    return resp.json()

def convert_to_number(val):
    """将字符串数字转换为真正的数字类型"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return val  # 已经是数字
    if isinstance(val, str):
        val = val.strip()
        if '.' in val:
            try:
                return float(val)
            except:
                return None
        else:
            try:
                return int(val)
            except:
                return None
    return val

def main():
    print("="*60)
    print("复制 rules 到芳芳的 Bitable (修复版)")
    print("="*60)
    
    token = get_token()
    print(f"Token: {'OK' if token else 'FAIL'}\n")
    
    # 获取芳芳规则表字段
    fangfang_fields = get_fields(token, FANGFANG_APP_TOKEN, FANGFANG_RULES_TABLE)
    fangfang_field_names = [f.get("field_name") for f in fangfang_fields]
    print(f"芳芳规则表字段: {fangfang_field_names}\n")
    
    # 获取金的规则
    jin_rules = get_records(token, JIN_APP_TOKEN, JIN_RULES_TABLE)
    print(f"读取到 {len(jin_rules)} 条规则\n")
    
    # 复制
    success = 0
    fail = 0
    
    for rule in jin_rules:
        fields = rule.get("fields", {})
        
        # 构建复制字段
        copy_fields = {}
        for fname in fangfang_field_names:
            if fname in fields and fname not in ["rule_id", "created_at", "updated_at"]:
                val = fields[fname]
                
                # 数字字段转换
                if fname in ["priority", "confidence", "success_rate"]:
                    converted = convert_to_number(val)
                    if converted is not None:
                        copy_fields[fname] = converted
                    else:
                        copy_fields[fname] = val
                else:
                    copy_fields[fname] = val
        
        # 修改 rule_id
        if "rule_id" in copy_fields:
            copy_fields["rule_id"] = str(copy_fields["rule_id"]) + "_c"
        
        # debug: 打印数字字段的值和类型
        for fname in ["priority", "confidence"]:
            if fname in copy_fields:
                val = copy_fields[fname]
                print(f"  DEBUG: {fname} = {val} (type={type(val).__name__})")
        
        result = create_record(token, FANGFANG_APP_TOKEN, FANGFANG_RULES_TABLE, copy_fields)
        if result.get("code") == 0:
            success += 1
            print(f"  [OK] {copy_fields.get('rule_name', 'unknown')}")
        else:
            fail += 1
            print(f"  [FAIL] {copy_fields.get('rule_name', 'unknown')}: {result.get('msg')}")
        
        time.sleep(0.2)
    
    print()
    print("="*60)
    print(f"完成！成功: {success}, 失败: {fail}")
    print("="*60)

if __name__ == "__main__":
    main()
