# -*- coding: utf-8 -*-
"""总结生成器 - 使用 LLM 生成自由格式总结"""

from typing import Dict, Any, List


class SummaryGenerator:
    """总结生成器"""
    
    # 指标中文名映射
    METRIC_CN_NAMES = {
        "steps": "步数",
        "active_calories": "卡路里",
        "moderate_vigorous_minutes": "中高强度分钟",
        "activity_sessions": "活动次数",
        "sleep_duration_minutes": "睡眠时长",
        "heart_rate": "心率",
        "weight_kg": "体重",
        "blood_glucose": "血糖",
        "blood_pressure_systolic": "收缩压",
        "blood_pressure_diastolic": "舒张压",
    }
    
    # 单位中文名
    UNIT_CN_NAMES = {
        "steps": "步",
        "kcal": "千卡",
        "min": "分钟",
        "times": "次",
        "bpm": "次/分",
        "kg": "kg",
        "mmol/L": "mmol/L",
        "mmHg": "mmHg",
    }
    
    @classmethod
    def format_records_for_llm(cls, records: List[Dict[str, Any]], stats: Dict[str, Any] = None) -> str:
        """
        将记录格式化为 LLM 输入
        
        Args:
            records: 记录列表
            stats: 统计数据（可选）
            
        Returns:
            格式化的文本描述
        """
        if not records:
            return "暂无数据"
        
        # 按指标类型分组
        by_metric = {}
        for r in records:
            mt = r.get("metric_type", "")
            if mt not in by_metric:
                by_metric[mt] = []
            by_metric[mt].append(r)
        
        lines = []
        for metric_type, recs in by_metric.items():
            cn_name = cls.METRIC_CN_NAMES.get(metric_type, metric_type)
            unit = recs[0].get("unit", "")
            cn_unit = cls.UNIT_CN_NAMES.get(unit, unit)
            
            # 最近一条
            latest = recs[0]
            latest_val = latest.get("value")
            latest_date = latest.get("date", "")
            
            if metric_type == "sleep_duration_minutes":
                # 睡眠转小时分
                total_min = float(latest_val) if latest_val else 0
                hours = int(total_min // 60)
                mins = int(total_min % 60)
                val_str = f"{hours}小时{mins}分" if hours else f"{mins}分钟"
            else:
                val_str = f"{latest_val} {cn_unit}" if latest_val else "无数据"
            
            line = f"- {cn_name}：{val_str}（{latest_date}）"
            lines.append(line)
        
        result = "\n".join(lines)
        
        # 添加统计信息
        if stats:
            result += f"\n\n统计：共 {stats.get('count', 0)} 条记录"
            if stats.get("change") is not None:
                change = stats.get("change", 0)
                direction = "↑" if change > 0 else "↓" if change < 0 else "→"
                result += f"，变化 {direction} {abs(change)}"
        
        return result
    
    @classmethod
    def build_summary_prompt(cls, query_type: str, query_params: Dict[str, Any], 
                             records: List[Dict[str, Any]], stats: Dict[str, Any] = None) -> str:
        """
        构建总结 prompt
        
        Args:
            query_type: 查询类型 ("single_metric", "recent_summary")
            query_params: 查询参数
            records: 查询到的记录
            stats: 统计数据
            
        Returns:
            LLM prompt
        """
        data_text = cls.format_records_for_llm(records, stats)
        
        if query_type == "single_metric":
            metric_cn = cls.METRIC_CN_NAMES.get(query_params.get("metric_type", ""), "未知")
            days = query_params.get("days", 7)
            prompt = f"""请根据以下{metric_cn}数据，用自然语言总结：

{data_text}

要求：
1. 直接总结，不要固定模板
2. 突出变化趋势和异常
3. 如有数据，保持客观
4. 简洁明了
"""
        else:  # recent_summary
            prompt = f"""请根据以下最近健康数据，用自然语言总结：

{data_text}

要求：
1. 直接总结，不要固定模板
2. 涵盖各个方面（运动、睡眠、代谢等）
3. 突出重点和异常
4. 简洁有条理
"""
        
        return prompt
