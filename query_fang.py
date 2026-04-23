import sqlite3

conn = sqlite3.connect(r'C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\data\lifeos.db')
cursor = conn.cursor()

profile_id = '002'

# 查询芳芳的每日记录
print("=== 芳芳的每日记录 (daily_logs) ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_logs'")
if cursor.fetchone():
    cursor.execute("PRAGMA table_info(daily_logs)")
    print("daily_logs表结构:")
    for col in cursor.fetchall():
        print(f"  {col}")
    cursor.execute("SELECT * FROM daily_logs WHERE profile_id = ? ORDER BY date DESC LIMIT 10", (profile_id,))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("暂无每日记录")

# 查询芳芳的运动记录
print("\n=== 芳芳的运动记录 (exercise) ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%exercise%'")
tables = cursor.fetchall()
print(f"运动相关表: {tables}")
for table in tables if tables else []:
    table_name = table[0]
    cursor.execute(f"SELECT * FROM {table_name} WHERE profile_id = ? ORDER BY date DESC LIMIT 5", (profile_id,))
    rows = cursor.fetchall()
    if rows:
        print(f"{table_name}:")
        for row in rows:
            print(row)
    else:
        print(f"{table_name}: 暂无记录")

# 查询芳芳的健康评估
print("\n=== 芳芳的健康评估 ===")
cursor.execute("SELECT * FROM health_evaluations WHERE profile_id = ? ORDER BY created_at DESC LIMIT 5", (profile_id,))
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print("暂无健康评估记录")

conn.close()
