import sys
import os
sys.path.insert(0, '.')
from db import insert, query_one

# 昨天的日期
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# 写入 daily_log
log_data = {
    'profile_id': '002',
    'date': yesterday,
    'sleep_hours': 7.0,
    'had_training': 1,
    'training_brief': '平板支撑',
    'state_tags': '训练日',
    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

result = insert('daily_logs', log_data)
print('insert result:', result)

# 验证
log = query_one('SELECT * FROM daily_logs WHERE profile_id = ? AND date = ?', ['002', yesterday])
if log:
    print('date:', log['date'])
    print('sleep_hours:', log['sleep_hours'])
    print('had_training:', log['had_training'])
    print('training_brief:', log['training_brief'])
