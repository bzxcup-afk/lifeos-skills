#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import time
import json

APP_ID = "cli_a92ed6e39938dbd2"
APP_SECRET = "4bZFShVypTIKI25FmNHSLgRUL7BuRhrq"

# 两个 Bitable 的 app_token
BITABLES = {
    "jin": {
        "name": "金 - LifeOS",
        "app_token": "DtWnbquyZaIj9xsWLSIcagjQnAc"
    },
    "fangfang": {
        "name": "芳芳 - LifeOS",
        "app_token": "Y2pxbRjm8avmLUsnH8jc2K5rnHL"
    }
}

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

def list_fields(token, app_token, table_id):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("items", [])
    return []

def create_table(token, app_token, name, description=""):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"table": {"name": name, "description": description}}
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("table_id")
    elif result.get("code") == 4007:
        # Table exists, find it
        tables = list_tables(token, app_token)
        for t in tables:
            if t.get("name") == name:
                return t.get("table_id")
    return None

def create_field(token, app_token, table_id, field_name, field_type, property=None):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"field_name": field_name, "type": field_type}
    if property:
        data["property"] = property
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return True
    return False

def create_record(token, app_token, table_id, fields):
    url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"fields": fields}
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return True
    return False

def main():
    print("="*60)
    print("复制 LifeOS 表结构到芳芳的 Bitable")
    print("="*60)
    
    token = get_token()
    if not token:
        print("[ERROR] Token failed")
        return
    
    print(f"[OK] Token OK\n")
    
    # 1. 获取金 Bitable 的表结构
    print("[Step 1] 获取金的 LifeOS 表结构")
    jin_tables = list_tables(token, BITABLES["jin"]["app_token"])
    print(f"  金的表数量: {len(jin_tables)}")
    
    jin_table_ids = {}
    for t in jin_tables:
        name = t.get("name")
        table_id = t.get("table_id")
        jin_table_ids[name] = table_id
        print(f"  - {name}: {table_id}")
    
    print()
    
    # 2. 在芳芳 Bitable 中创建相同表结构
    print("[Step 2] 在芳芳的 Bitable 创建相同表结构")
    
    new_table_ids = {}  # name -> new_table_id
    
    for t in jin_tables:
        name = t.get("name")
        new_table_id = create_table(token, BITABLES["fangfang"]["app_token"], name)
        if new_table_id:
            print(f"  [OK] 创建表: {name} -> {new_table_id}")
            new_table_ids[name] = new_table_id
            time.sleep(0.3)
            
            # 获取原表字段并复制
            old_fields = list_fields(token, BITABLES["jin"]["app_token"], t.get("table_id"))
            
            for field in old_fields:
                fname = field.get("field_name")
                ftype = field.get("type")
                fprop = field.get("property")
                
                if create_field(token, BITABLES["fangfang"]["app_token"], new_table_id, fname, ftype, fprop):
                    print(f"      [OK] 字段: {fname}")
                else:
                    print(f"      [SKIP] 字段: {fname} (可能已存在)")
                
                time.sleep(0.1)
        else:
            print(f"  [FAIL] 创建表: {name}")
    
    print()
    
    # 3. 复制 rules 表内容
    print("[Step 3] 复制 rules 表内容到芳芳的 Bitable")
    
    if "rules" in jin_table_ids and "rules" in new_table_ids:
        jin_rules = list_fields(token, BITABLES["jin"]["app_token"], jin_table_ids["rules"])
        
        # 读取金 rules 表的记录
        url = f"{BASE_URL}/bitable/v1/apps/{BITABLES['jin']['app_token']}/tables/{jin_table_ids['rules']}/records"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers, timeout=30)
        result = resp.json()
        
        if result.get("code") == 0:
            records = result.get("data", {}).get("items", [])
            print(f"  找到 {len(records)} 条规则记录")
            
            # 获取芳芳 rules 表的字段列表
            fangfang_rules_fields = list_fields(token, BITABLES["fangfang"]["app_token"], new_table_ids["rules"])
            
            for record in records:
                fields = record.get("fields", {})
                # 只复制基础字段
                copy_fields = {}
                for f in fangfang_rules_fields:
                    fname = f.get("field_name")
                    if fname in fields and fname not in ["rule_id", "created_at", "updated_at"]:
                        copy_fields[fname] = fields[fname]
                
                if copy_fields:
                    # 设置 rule_id 加后缀
                    if "rule_id" in copy_fields:
                        copy_fields["rule_id"] = copy_fields["rule_id"] + "_fang"
                    
                    if create_record(token, BITABLES["fangfang"]["app_token"], new_table_ids["rules"], copy_fields):
                        print(f"  [OK] 复制规则: {copy_fields.get('rule_name', 'unknown')}")
                    else:
                        print(f"  [FAIL] 复制规则: {copy_fields.get('rule_name', 'unknown')}")
                
                time.sleep(0.2)
    
    print()
    print("="*60)
    print("复制完成！")
    print("="*60)
    print(f"\n芳芳的 Bitable 表结构:")
    for name, tid in new_table_ids.items():
        print(f"  - {name}: {tid}")

if __name__ == "__main__":
    main()
