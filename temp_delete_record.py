import sys
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts')

import requests
from bitable_ops import get_token, get_table_ids, resolve_table_key, get_current_app_token, BASE_URL

# 删除记录
token = get_token()
if token:
    record_id = "recveK9iwFBXx5"
    table_key = resolve_table_key("medical_records")
    table_id = get_table_ids().get(table_key)
    
    if table_id:
        app_token = get_current_app_token()
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            resp = requests.delete(url, headers=headers, timeout=30)
            result = resp.json()
            if result.get("code") == 0:
                print(f"SUCCESS: 记录 {record_id} 已删除")
            else:
                print(f"ERROR: {result.get('code')} - {result.get('msg')}")
        except Exception as e:
            print(f"ERROR: {str(e)}")
    else:
        print("ERROR: 找不到表ID")
else:
    print("ERROR: 无法获取token")
