#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库基础模块"""

import sqlite3
import json
import os
from pathlib import Path
from contextlib import contextmanager

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = SKILL_ROOT / "config" / "config.json"


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"database": {"path": "data/lifeos.db"}}


def get_db_path():
    config = load_config()
    db_path = config["database"]["path"]
    if os.path.isabs(db_path):
        return db_path
    return str(SKILL_ROOT / db_path)


@contextmanager
def get_connection():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(sql, params=()):
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid


def query_one(sql, params=()):
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def query_many(sql, params=(), limit=None):
    with get_connection() as conn:
        if limit:
            sql = f"{sql} LIMIT {limit}"
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def insert(table, data):
    columns = list(data.keys())
    placeholders = ", ".join(["?" for _ in columns])
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    return execute(sql, tuple(data.values()))


def update(table, data, where_clause, where_params):
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    return execute(sql, tuple(data.values()) + tuple(where_params))


def delete(table, where_clause, where_params):
    sql = f"DELETE FROM {table} WHERE {where_clause}"
    return execute(sql, where_params)
