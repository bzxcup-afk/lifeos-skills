#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出所有可访问的Bitable表"""

import sys
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(script_dir)
sys.path.insert(0, skill_root)

from scripts.bitable_ops import get_token, get_current_app_token, BASE_URL
import requests

def list_all_tables():
    """列出所有可访问的表"""
    # 列出金的LifeOS中的所有表
    app_token = 'DtWnbquyZaIj9xsWLSIcagjQnAc'
    token = get_token()
    
    if not token:
        print('[ERROR] Failed to get token')
        return
    
    url = f'{BASE_URL}/bitable/v1/apps/{app_token}/tables'
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        result = resp.json()
        
        print(f'Tables in {app_token}:')
        if result.get('code') == 0:
            for t in result.get('data', {}).get('items', []):
                print(f'  {t.get("table_id")} - {t.get("name")}')
        else:
            print(f'Error: {result.get("msg")}')
    except Exception as e:
        print(f'[ERROR] {e}')

if __name__ == '__main__':
    list_all_tables()
