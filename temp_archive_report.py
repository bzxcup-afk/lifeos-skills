import sys
sys.path.insert(0, r'C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main\scripts')

from bitable_ops import get_token, create_record
import json

# 写入医疗记录
token = get_token()
if token:
    fields = {
        "record_type": "血检",
        "institution": "秭归县两河口镇卫生院",
        "department": "外科",
        "complaint_or_reason": "血常规检查 - 临床诊断：股骨颈骨折，84岁高龄患者",
        "key_metrics_json": json.dumps({
            "WBC": "10.37↑ (参考4-10 10^9/L)",
            "NEUT": "9.15↑ (参考2-7 10^9/L)",
            "LYM": "0.76↓ (参考0.8-4 10^9/L)",
            "RBC": "2.63↓ (参考3.5-5 10^12/L)",
            "HGB": "96↓ (参考110-150 g/L)"
        }, ensure_ascii=False),
        "tags": ["血常规", "骨折", "贫血", "感染指标"],
        "summary_for_system": "84岁患者血常规：白细胞和中性粒细胞偏高提示感染/炎症；红细胞、血红蛋白偏低提示贫血；结合股骨颈骨折，需关注术后感染风险和贫血纠正。",
        "record_date": "2023-08-30",
        "severity_level": "中",
        "follow_up_needed": True
    }
    record_id, error = create_record(token, "medical_records", fields)
    if record_id:
        print(f"SUCCESS: 记录已创建，ID: {record_id}")
    else:
        print(f"ERROR: {error}")
else:
    print("ERROR: 无法获取token")
