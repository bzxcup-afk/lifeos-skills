import sys
import os
sys.path.insert(0, '.')

# 导入健康评估模块
from health_evaluation import run_evaluation
import json

# 运行评估
result = run_evaluation('002')

# 保存结果
with open(r'C:\Users\Jin\.openclaw\workspace-coding\fangfang_health_eval.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print('评估完成，已保存到 fangfang_health_eval.json')
print('总分:', result.get('total_score'))
