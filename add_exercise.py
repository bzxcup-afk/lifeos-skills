import sqlite3
from datetime import datetime

conn = sqlite3.connect(r'C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\data\lifeos.db')
cursor = conn.cursor()

profile_id = '002'
today = datetime.now().strftime('%Y-%m-%d')

# 检查今天是否已有记录
cursor.execute("SELECT log_id FROM daily_logs WHERE profile_id = ? AND date = ?", (profile_id, today))
existing = cursor.fetchone()

if existing:
    # 更新现有记录
    log_id = existing[0]
    cursor.execute("""
        UPDATE daily_logs 
        SET had_training = 1, training_brief = ?
        WHERE log_id = ?
    """, ('平板支撑 x 2组', log_id))
    print(f"更新了今天的记录: log_id={log_id}")
else:
    # 插入新记录
    cursor.execute("""
        INSERT INTO daily_logs (profile_id, date, had_training, training_brief)
        VALUES (?, ?, 1, ?)
    """, (profile_id, today, '平板支撑 x 2组'))
    print(f"创建了新记录: log_id={cursor.lastrowid}")

conn.commit()
conn.close()
print("记录成功！")
