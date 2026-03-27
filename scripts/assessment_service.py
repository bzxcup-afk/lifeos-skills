#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""评估服务 - 预留框架"""

from datetime import datetime
from db import query_one, query_many, insert, update


class AssessmentService:
    """健康评估服务（预留）"""
    
    def __init__(self, profile_id=None):
        self.profile_id = profile_id
    
    def get_latest_assessment(self):
        """获取最新评估"""
        if not self.profile_id:
            return None
        return query_one(
            "SELECT * FROM health_evaluations WHERE profile_id = ? ORDER BY created_at DESC LIMIT 1",
            (self.profile_id,)
        )
    
    def list_assessments(self, limit=10):
        """列出历史评估"""
        if not self.profile_id:
            return []
        return query_many(
            "SELECT * FROM health_evaluations WHERE profile_id = ? ORDER BY created_at DESC LIMIT ?",
            (self.profile_id, limit)
        )


def get_service(profile_id=None):
    return AssessmentService(profile_id)
