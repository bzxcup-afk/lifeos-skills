# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
from db import execute

# Delete老爹的药物记录
execute("DELETE FROM medications WHERE profile_id = '004' AND drug_name IN ('硝苯地平控释片', '阿司匹林')")
print("Cleared")
