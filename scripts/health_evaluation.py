#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""健康评估模块 - 本地SQLite版"""

import os
import sys
import json
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from health_service import get_service
from db import insert


def run_evaluation(profile_id, days_back=30):
    """运行健康评估"""
    svc = get_service(profile_id)
    
    profile = svc.get_profile()
    if not profile:
        return {"error": "Profile not found"}
    
    logs = svc.get_recent_logs(days=days_back)
    
    scores = calculate_scores(logs, profile, days_back)
    
    result = {
        "eval_id": str(uuid.uuid4())[:8],
        "profile_id": profile_id,
        "eval_date": datetime.now().strftime("%Y-%m-%d"),
        
        "data_source_desc": f"基于最近{len(logs)}天daily_logs",
        "data_time_range": f"{days_back}天",
        "data_coverage": calculate_coverage(logs, days_back),
        "confidence_score": calculate_confidence(logs, days_back),
        
        "cardio_score": scores["cardio"],
        "strength_score": scores["strength"],
        "metabolism_score": scores["metabolism"],
        "recovery_score": scores["recovery"],
        "execution_score": scores["execution"],
        "total_score": scores["total"],
        
        "risk_signals": json.dumps(scores["risks"], ensure_ascii=False),
        "overall_status": scores["status"],
        "main_issues": "\n".join(scores["issues"]),
        "recommended_actions": "\n".join(scores["actions"]),
        "brief_report": generate_brief_report(scores, profile),
        
        "chart_data_json": json.dumps({
            "radar": {
                "labels": ["心血管", "肌肉力量", "代谢体重", "恢复睡眠", "执行度"],
                "values": [
                    scores["cardio"], scores["strength"], scores["metabolism"],
                    scores["recovery"], scores["execution"]
                ]
            }
        }, ensure_ascii=False),
        
        "explanation_json": json.dumps(scores["explanations"], ensure_ascii=False),
        
        "eval_age": calculate_age(profile.get("birth_date")),
        "eval_gender": profile.get("gender"),
        "eval_training_base": profile.get("training_base"),
        "eval_health_goal": profile.get("health_goal"),
        "missing_fields": json.dumps(scores["missing"], ensure_ascii=False)
    }
    
    return result


def calculate_scores(logs, profile, days_back):
    """计算五维评分"""
    scores = {
        "cardio": 70, "strength": 70, "metabolism": 70,
        "recovery": 70, "execution": 70, "total": 70,
        "status": "一般", "risks": [], "issues": [],
        "actions": [], "explanations": {}, "missing": []
    }
    
    if not logs:
        scores["missing"].append("无历史daily_logs数据")
        return scores
    
    n = len(logs)
    sleep_hours = [l.get("sleep_hours") or 0 for l in logs if l.get("sleep_hours")]
    fatigue_scores = [l.get("fatigue_score") or 0 for l in logs if l.get("fatigue_score")]
    
    avg_sleep = sum(sleep_hours) / len(sleep_hours) if sleep_hours else 0
    avg_fatigue = sum(fatigue_scores) / len(fatigue_scores) if fatigue_scores else 5
    
    training_count = sum(1 for l in logs if l.get("had_training"))
    training_rate = training_count / n if n > 0 else 0
    
    # 恢复睡眠评分
    if avg_sleep >= 7.5:
        scores["recovery"] = 85 + min((avg_sleep - 7.5) * 5, 10)
    elif avg_sleep >= 6:
        scores["recovery"] = 70 + (avg_sleep - 6) * 10
    else:
        scores["recovery"] = max(40, 60 - (6 - avg_sleep) * 10)
        scores["risks"].append({"type": "睡眠不足", "level": "中", "detail": f"平均睡眠{avg_sleep:.1f}小时"})
        scores["issues"].append("睡眠不足，建议保证7-8小时睡眠")
        scores["actions"].append("调整作息，固定就寝时间")
    
    if avg_fatigue > 7:
        scores["recovery"] = max(40, scores["recovery"] - 15)
        scores["risks"].append({"type": "持续高疲劳", "level": "高", "detail": f"平均疲劳度{avg_fatigue:.1f}"})
        scores["issues"].append("疲劳度过高，需要增加恢复时间")
        scores["actions"].append("减少训练量，增加主动恢复")
    
    scores["explanations"]["recovery"] = f"基于平均睡眠{avg_sleep:.1f}小时，平均疲劳度{avg_fatigue:.1f}"
    
    # 执行度评分
    if training_rate >= 0.8:
        scores["execution"] = 90
    elif training_rate >= 0.6:
        scores["execution"] = 75 + (training_rate - 0.6) * 75
    elif training_rate >= 0.4:
        scores["execution"] = 60 + (training_rate - 0.4) * 75
    else:
        scores["execution"] = max(40, training_rate * 150)
        if training_rate < 0.3:
            scores["issues"].append("训练频率偏低，建议制定规律计划")
            scores["actions"].append("设定每周固定训练日")
    
    scores["explanations"]["execution"] = f"近{n}天训练{training_count}次，执行率{training_rate:.1%}"
    
    # 肌肉力量、代谢、心血管（简化估算）
    base_strength = 60
    if training_rate > 0.5:
        base_strength += min((training_rate - 0.5) * 40, 25)
    if avg_fatigue < 5:
        base_strength += 10
    elif avg_fatigue > 7:
        base_strength -= 15
    scores["strength"] = max(40, min(95, base_strength))
    scores["explanations"]["strength"] = "基于训练频率和恢复状态估算"
    
    base_meta = 70
    if avg_sleep >= 7:
        base_meta += 10
    if training_rate >= 0.4:
        base_meta += 10
    scores["metabolism"] = max(50, min(90, base_meta))
    scores["explanations"]["metabolism"] = "基于睡眠和训练估算"
    
    base_cardio = 70
    age = calculate_age(profile.get("birth_date"))
    if age and age > 50:
        base_cardio -= 5
    scores["cardio"] = max(50, min(90, base_cardio))
    scores["explanations"]["cardio"] = "基于基础资料估算"
    
    # 总分
    scores["total"] = round(
        scores["cardio"] * 0.30 +
        scores["strength"] * 0.25 +
        scores["metabolism"] * 0.20 +
        scores["recovery"] * 0.15 +
        scores["execution"] * 0.10
    )
    
    # 总体状态
    if scores["total"] >= 85:
        scores["status"] = "优秀"
    elif scores["total"] >= 75:
        scores["status"] = "良好"
    elif scores["total"] >= 60:
        scores["status"] = "一般"
    elif scores["total"] >= 45:
        scores["status"] = "需改善"
    else:
        scores["status"] = "较差"
    
    return scores


def calculate_coverage(logs, days_back):
    if not logs:
        return "无数据"
    n = len(logs)
    if n >= days_back * 0.9:
        return f"完整({n}/{days_back}天)"
    elif n >= days_back * 0.6:
        return f"部分({n}/{days_back}天)"
    else:
        return f"不足({n}/{days_back}天)"


def calculate_confidence(logs, days_back):
    if not logs:
        return 0
    n = len(logs)
    base = min(100, int(n / days_back * 100))
    quality = sum(1 for l in logs if l.get('sleep_hours') and l.get('fatigue_score'))
    if quality >= len(logs) * 0.8:
        base = min(100, base + 10)
    return min(100, base)


def calculate_age(birth_date_str):
    if not birth_date_str:
        return None
    try:
        birth = datetime.strptime(birth_date_str, "%Y-%m-%d")
        today = datetime.now()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except:
        return None


def generate_brief_report(scores, profile):
    name = profile.get('name', '用户')
    lines = [
        f"【{name}的健康评估报告】",
        "",
        f"评估日期: {datetime.now().strftime('%Y年%m月%d日')}",
        f"总体状态: {scores['status']} (总分: {scores['total']})",
        "",
        "【五维评分】",
        f"  心血管健康: {scores['cardio']} 分",
        f"  肌肉力量:   {scores['strength']} 分",
        f"  代谢体重:   {scores['metabolism']} 分",
        f"  恢复睡眠:   {scores['recovery']} 分",
        f"  执行度:     {scores['execution']} 分",
        "",
    ]
    
    if scores['risks']:
        lines.extend(["【风险提示】"])
        for risk in scores['risks']:
            lines.append(f"  ⚠️ {risk['type']}: {risk['detail']}")
        lines.append("")
    
    if scores['issues']:
        lines.extend(["【主要问题】"])
        for issue in scores['issues']:
            lines.append(f"  • {issue}")
        lines.append("")
    
    if scores['actions']:
        lines.extend(["【建议行动】"])
        for action in scores['actions']:
            lines.append(f"  → {action}")
        lines.append("")
    
    lines.append("— 本评估基于本地历史数据生成 —")
    
    return "\n".join(lines)


def save_evaluation(result):
    """保存评估结果"""
    json_fields = ['risk_signals', 'chart_data_json', 'explanation_json', 'missing_fields']
    data = dict(result)
    for field in json_fields:
        if field in data and not isinstance(data[field], str):
            data[field] = json.dumps(data[field], ensure_ascii=False)
    
    insert("health_evaluations", data)
    return result['eval_id']


# 命令行入口
if __name__ == "__main__":
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python health_evaluation.py <command> [args]")
        print("Commands:")
        print("  run <profile_id> [days]    - 运行评估")
        print("  save <profile_id> [days]   - 运行并保存")
        print("  list <profile_id>          - 列出历史评估")
        sys.exit(1)
    
    cmd = sys.argv[1]
    profile_id = sys.argv[2] if len(sys.argv) > 2 else "001"
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    if cmd == "run":
        from health_service import get_service
        svc = get_service(profile_id)
        profile = svc.get_profile()
        logs = svc.get_recent_logs(days=days)
        scores = calculate_scores(logs, profile or {"name": profile_id}, days)
        print(generate_brief_report(scores, profile or {"name": profile_id}))
    
    elif cmd == "save":
        result = run_evaluation(profile_id, days)
        eval_id = save_evaluation(result)
        print(f"✓ 评估已保存，ID: {eval_id}")
        print(generate_brief_report(result, {"name": profile_id}))
    
    elif cmd == "list":
        from db import query_many
        rows = query_many(
            "SELECT eval_id, eval_date, total_score, overall_status FROM health_evaluations WHERE profile_id = ? ORDER BY created_at DESC",
            (profile_id,)
        )
        print(f"【{profile_id}的历史评估】")
        for r in rows:
            print(f"  {r['eval_date']} | 总分:{r['total_score']} | 状态:{r['overall_status']} | ID:{r['eval_id']}")
    
    else:
        print(f"Unknown command: {cmd}")
