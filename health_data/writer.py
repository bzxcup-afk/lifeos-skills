# -*- coding: utf-8 -*-
"""写入器 - 批量写入健康数据到数据库"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db import get_connection


class Writer:
    """写入器"""
    
    @classmethod
    def write_batch(cls, profile_id: str, user_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量写入记录
        
        Args:
            profile_id: 用户 profile_id (如 "001")
            user_id: 用户 sender_id (飞书 open_id)
            records: 待写入的记录列表
            
        Returns:
            {
                "success": bool,
                "written_count": int,
                "failed_count": int,
                "batch_id": str,
                "errors": [...]
            }
        """
        if not records:
            return {
                "success": True,
                "written_count": 0,
                "failed_count": 0,
                "batch_id": None,
                "errors": []
            }
        
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        written_count = 0
        errors = []
        
        sql = """
            INSERT INTO health_data_logs (
                id, user_id, profile_id,
                metric_type, value, unit,
                date, measured_at, granularity,
                source_app, source_mode,
                raw_text, extra_json,
                confidence, image_hash, import_batch_id,
                is_valid, validation_notes,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with get_connection() as conn:
                for r in records:
                    record_id = f"hdl_{uuid.uuid4().hex[:12]}"
                    
                    params = (
                        record_id,
                        user_id,
                        profile_id,
                        r.get("metric_type"),
                        r.get("value"),
                        r.get("unit"),
                        r.get("date"),
                        r.get("measured_at") or r.get("date"),
                        r.get("granularity", "instant"),
                        r.get("source_app", "xiaomi_health"),
                        "screenshot_parse",
                        r.get("raw_text", ""),
                        r.get("extra_json") or json.dumps(r.get("extra", {})) if r.get("extra") else None,
                        r.get("confidence", 0.9),
                        r.get("image_hash"),
                        batch_id,
                        1 if r.get("is_valid", True) else 0,
                        r.get("validation_notes", ""),
                        now
                    )
                    
                    try:
                        conn.execute(sql, params)
                        written_count += 1
                    except Exception as e:
                        errors.append({
                            "record": r,
                            "error": str(e)
                        })
        except Exception as e:
            return {
                "success": False,
                "written_count": written_count,
                "failed_count": len(records) - written_count,
                "batch_id": batch_id,
                "errors": errors + [{"error": str(e)}]
            }
        
        return {
            "success": len(errors) == 0,
            "written_count": written_count,
            "failed_count": len(records) - written_count,
            "batch_id": batch_id,
            "errors": errors
        }
