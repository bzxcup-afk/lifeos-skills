#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用药管理服务（预留框架）"""

from datetime import datetime
from db import query_one, query_many, insert, update


class MedicationService:
    """用药管理服务"""
    
    def __init__(self, profile_id=None):
        self.profile_id = profile_id
    
    def list_medications(self, active_only=True):
        """列出用药清单"""
        if not self.profile_id:
            return []
        
        sql = "SELECT * FROM medications WHERE profile_id = ?"
        params = [self.profile_id]
        
        if active_only:
            sql += " AND is_active = 1"
        
        return query_many(sql, tuple(params))
    
    def add_medication(self, drug_name, dosage=None, time_slot=None):
        """添加用药"""
        if not self.profile_id:
            return None
        
        data = {
            'profile_id': self.profile_id,
            'drug_name': drug_name,
            'dosage': dosage,
            'time_slot': time_slot,
            'is_active': 1
        }
        
        return insert("medications", data)
    
    def check_reminders(self, date=None, time_slot=None):
        """检查待提醒用药"""
        if not self.profile_id:
            return []
        
        date = date or datetime.now().strftime("%Y-%m-%d")
        
        # 获取所有active的用药
        meds = self.list_medications(active_only=True)
        
        reminders = []
        for med in meds:
            # 检查今天是否已记录
            log = query_one(
                """SELECT * FROM medication_logs 
                   WHERE med_id = ? AND date = ? AND time_slot = ?""",
                (med['med_id'], date, med['time_slot'] or 'default')
            )
            
            if not log or log['status'] != 'taken':
                if time_slot is None or med.get('time_slot') == time_slot:
                    reminders.append({
                        'med_id': med['med_id'],
                        'drug_name': med['drug_name'],
                        'dosage': med['dosage'],
                        'time_slot': med['time_slot']
                    })
        
        return reminders
    
    def record_taken(self, med_id, date=None, time_slot=None):
        """记录已服药"""
        if not self.profile_id:
            return False
        
        date = date or datetime.now().strftime("%Y-%m-%d")
        
        # 查找或创建记录
        log = query_one(
            "SELECT * FROM medication_logs WHERE med_id = ? AND date = ? AND time_slot = ?",
            (med_id, date, time_slot or 'default')
        )
        
        if log:
            update("medication_logs", {
                'status': 'taken',
                'taken_at': datetime.now().isoformat()
            }, "log_id = ?", (log['log_id'],))
        else:
            insert("medication_logs", {
                'med_id': med_id,
                'profile_id': self.profile_id,
                'date': date,
                'time_slot': time_slot or 'default',
                'status': 'taken',
                'taken_at': datetime.now().isoformat()
            })
        
        return True


def get_service(profile_id=None):
    return MedicationService(profile_id)
