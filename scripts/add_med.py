# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import insert

profile_id = '004'

result1 = insert('medications', {
    'profile_id': profile_id,
    'drug_name': '硝苯地平控释片',
    'is_active': 1
})
print(f'Nifedipine: {"OK" if result1 else "FAIL"}')

result2 = insert('medications', {
    'profile_id': profile_id,
    'drug_name': '阿司匹林',
    'is_active': 1
})
print(f'Aspirin: {"OK" if result2 else "FAIL"}')
