# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'scripts')
from bitable_ops import get_current_app_token, read_records

token = get_current_app_token()
table_key = 'tblkcow4prsTlpva'
filter_formula = 'AND(收件人="coding", 状态="未读")'
result = read_records(token, table_key, filterformula=filter_formula, limit=20)
print(result)
