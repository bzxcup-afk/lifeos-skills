# LifeOS 本地版快速使用说明

## 目录结构

```
skills/lifeos-main/
├── config/
│   ├── config.json          # 主配置（数据库路径、用户列表）
│   └── bitable_config.json  # 身份识别映射（仅保留 identity_mapping）
├── data/
│   └── lifeos.db            # SQLite 主数据库
├── scripts/
│   ├── db.py                    # 数据库连接和 CRUD
│   ├── init_db.py               # 数据库初始化
│   ├── health_service.py        # 健康数据服务
│   ├── medication_service.py    # 用药服务
│   ├── assessment_service.py    # 评估服务
│   ├── health_evaluation.py     # 健康评估入口
│   ├── lifeos_service.py        # 对话层统一入口（推荐）
│   └── feishu_export.py         # 飞书导出（预留）
└── SKILL.md                     # 技能定义文档
```

## 快速开始

### 1. 初始化数据库

```bash
cd scripts
python init_db.py
```

### 2. 命令行测试

```bash
# 运行健康评估
python health_evaluation.py run 001 30

# 运行并保存评估
python health_evaluation.py save 001 30

# 列出历史评估
python health_evaluation.py list 001
```

### 3. Python 代码中使用

```python
from lifeos_service import get_service

# 获取服务实例（profile_id: 001=金, 002=芳芳, 003=老妈, 004=老爹）
svc = get_service('001')

# 记录睡眠
result = svc.record_sleep(hours=7.5, quality=8)
print(result['message'])  # 已记录 2026-03-26 睡眠 7.5 小时

# 记录疲劳度
result = svc.record_fatigue(score=5, notes='有点累')

# 记录训练
result = svc.record_training(brief='跑步3公里', had_training=True)

# 获取今日概览
today = svc.get_today_summary()
```

## 数据表结构

### 核心表

| 表名 | 说明 |
|------|------|
| `profiles` | 用户资料（001/002/003/004） |
| `daily_logs` | 每日记录（睡眠、疲劳、训练等） |
| `events` | 事件记录（聚餐、出差、生病等） |
| `medical_records` | 医疗记录（症状、诊断等） |
| `medications` | 用药/补剂清单 |
| `medication_logs` | 服药记录 |
| `weekly_plans` | 周计划 |
| `weekly_plan_details` | 周计划详情（7天明细） |
| `health_evaluations` | 健康评估记录 |
| `health_knowledge` | 健康知识库 |
| `rules` | 规则表 |

### 多用户区分

所有表都有 `profile_id` 字段区分用户：
- `001` = 金
- `002` = 芳芳
- `003` = 老妈
- `004` = 老爹

## 配置说明

### config/config.json

```json
{
  "database": {
    "path": "data/lifeos.db",      // 数据库路径（相对路径）
    "backup_dir": "data/backups/"
  },
  "profiles": {
    "001": { "name": "金", "default": true },
    "002": { "name": "芳芳" },
    "003": { "name": "老妈" },
    "004": { "name": "老爹" }
  },
  "feishu_export": {
    "enabled": false                 // 飞书导出功能开关
  }
}
```

### config/bitable_config.json

保留 `identity_mapping` 用于身份识别，但不再用于飞书表 ID 路由。

## 与飞书的关系

**当前状态：**
- 数据主存储：本地 SQLite (`data/lifeos.db`)
- 飞书：仅用于身份识别 + 未来导出接口

**未来扩展：**
- 实现 `feishu_export.py` 中的导出功能
- 按需将本地数据同步到飞书

## 常用操作

### 查看数据库内容

```bash
# 使用 SQLite 命令行
cd data
sqlite3 lifeos.db

# 常用查询
.tables                          # 查看所有表
SELECT * FROM profiles;         # 查看用户
SELECT * FROM daily_logs LIMIT 5;  # 查看最新5条记录
.quit                            # 退出
```

### 备份数据库

```bash
# 复制数据库文件
cp data/lifeos.db data/backups/lifeos_$(date +%Y%m%d).db
```

### 重置数据库

```bash
# 删除并重新初始化
rm data/lifeos.db
python scripts/init_db.py
```

---

如有问题，查看 `SKILL.md` 或检查 `scripts/` 目录下的具体实现。
