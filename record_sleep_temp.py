# -*- coding: utf-8 -*-
from scripts.db import get_db
from datetime import datetime

db = get_db()
today = '2026-04-12'
profile_id = '001'

# Check if record exists for today
existing = db.query('SELECT id FROM daily_log WHERE profile_id = ? AND date = ?', (profile_id, today))
if existing:
    # Update existing record
    db.execute('UPDATE daily_log SET sleep_hours = 7, sleep_quality = 8, updated_at = ? WHERE profile_id = ? AND date = ?',
               (datetime.now().isoformat(), profile_id, today))
    print('updated')
else:
    # Insert new record
    db.execute('INSERT INTO daily_log (profile_id, date, sleep_hours, sleep_quality, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
               (profile_id, today, 7, 8, datetime.now().isoformat(), datetime.now().isoformat()))
    print('inserted')
