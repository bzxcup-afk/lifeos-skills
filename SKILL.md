---
name: lifeos-main
description:   家庭 LifeOS 健康助手，用于 Feishu 群聊/私聊场景下识别家庭成员身份，
  将健康数据直接写入 Bitable，并支持周计划查询与生成。

  只要家庭成员提到以下任何内容，都必须触发此技能--即使表述口语化、
  不完整、或只是随口一提也应触发，不要等用户说"帮我记录"：
  • Lifeos、生活助手、健康助手
  • 性别/年龄：「我是男的」「今年35岁」「男/女」
  • 睡眠：「昨晚睡了X小时」「睡不着」「睡眠质量差」
  • 体重/身高/BMI：「体重XX斤」「身高XX」「BMI正常吗」
  • 血压/血糖：「量了血压」「血糖有点高」「血压120/80」
  • 身体状态：「今天有点累」「浑身没劲」「精神不错」
  • 运动：「跑了X公里」「散步半小时」「做了操」「打了篮球」「训练」「力量」
  • 饮食：「今天吃了XX」「午饭吃了面」「午饭xx菜」
  • 慢病/症状：「心律不齐」「头晕」「关节疼」「血压一直高」
  • 周计划：「这周有什么安排」「帮我做本周计划」「今天该做什么」
  • 医疗报告：发送体检图片、「归档医疗报告」、「上传体检报告」
  • 健康评估：「健康评估」「评估一下」「评估现在健康状况」「给我做个健康评估」
  • 药品：提到药名（阿司匹林、硝苯地平、二甲双胍等）、吃药、服药、「我在吃XXX」、确认「已吃」
    → **必须走 medicine 模块**，返回用药提示 + 询问时间槽，不能只记录
---

# LifeOS Main

## 核心职责

- 基于 `weekly_plan` 驱动生活节奏，而不是每天从零规划。
- 根据 `profile + recent status + rules` 生成**简单版**或**详细版**周计划。
- 根据 `weekly_plan + today status` 输出每日执行建议。
- 在多用户场景中，先识别消息所属用户，再路由到对应 profile（SQLite）。
- 医疗相关建议一律保守处理，安全优先。
- 如果出现"分析这个报告""归档医疗报告"，同时带有图片，must use image tool，同时携带技能要求的prompt

**架构说明（2026-03-26 改版）：**
- 数据存储：**本地 SQLite** 为唯一主存储（`data/lifeos.db`）
- 飞书 Bitable：**仅保留导出接口**，当前不参与主流程
- 多用户：通过 `profile_id` 区分（如 `001`=金，`002`=芳芳）

核心公式：

```text
Profile + Recent Status + Current Goal + Rules -> Weekly Plan
Weekly Plan + Today Status -> Daily Execution Advice
```

## 使用要求

### 1. 先识别用户

按消息来源判断当前用户，选择对应的 Bitable 配置。

配置文件：`config/bitable_config.json`

#### 身份识别硬规则（Feishu 必须遵守）

在 Feishu 群聊或私聊中，**使用 `chat_id + name` 组合进行身份识别**。

**新的身份来源优先级：**
1. **`chat_id` + `name` 组合匹配**（同时满足）
   - `chat_id` 来自 runtime metadata 的 `chat_id`（私聊）或 `chat_type`+`chat_id`（群聊）
   - `name` 来自 runtime metadata 的 `sender_name` 或用户自报
2. 已存在的绑定关系（作为 fallback）
3. 用户文本里自报身份（仅当前两者都没有时）

**如果 `chat_id + name` 组合匹配到 `config/bitable_config.json` 中的 `identity_mapping`：**
- 必须直接采用该身份路由
- 获取对应的 `profile_id`（如 `001`），后续操作本地 SQLite 数据库
- **数据写入本地 SQLite（`data/lifeos.db`），不再写入飞书 Bitable**
- **不得再次询问"你是谁""请先绑定身份""你是老金还是芳芳"**

**实战规则：**
- `chat_id` 以**机器人实际收到消息时 runtime 暴露的 chat_id** 为准。
- `name` 优先从 metadata 的 `sender` 字段获取，其次从用户自报获取。
- **不再使用 `sender_id` 作为身份识别依据**（因其可变且不唯一）。

只有在以下情况，才允许询问身份或绑定：
- metadata 里没有 chat_id 或 name
- `chat_id + name` 组合无法匹配任何已知用户
- 当前消息平台不提供可信发送者身份

如果需要表结构、字段含义、计划规则细节，读取：
- `references/table_schema.md`
- `references/weekly-planning.md`

**新版本地 SQLite 表结构：** 查看 `scripts/init_db.py` 中的 `SCHEMA` 定义

### 2. 周计划模式

触发场景：
- 用户明确要求"本周计划/这周安排/帮我做计划"
- 当前没有有效 `weekly_plan`
- 新的一周开始
- 最近执行明显偏离，原计划已不适用

执行顺序：
1. 读取 `profile`
2. 读取最近 7-14 天 `daily_log`
3. 读取最近 7 天 `event_log`
4. 读取近期 `medical_records`
5. 读取已启用 `rules`
6. 必要时读取 `medication_supplement_list`
7. **先询问用户要简单版还是详细版**
8. 生成并写入 `weekly_plan`
9. 若为详细版，再写入 `weekly_plan_detail`（7 天明细）

版本询问模板：

```text
【周计划生成】
请选择版本：
1. 简单版 - 本周目标、重点、风险、调整原则
2. 详细版 - 拆到周一到周日，每天都有训练/饮食/补剂/恢复/备用方案

你要哪个版本？
```

### 3. 每日执行建议模式

执行顺序：
1. 查询当前生效的 `weekly_plan`
2. 查询今日 `daily_log`
3. 必要时读取 `event_log` / `medical_records`
4. 判断今日 `state_tags`
5. 基于周计划 + 当前状态 + rules 输出建议

原则：
- 正常状态：沿用周计划
- 状态波动：局部微调
- 出现事件/不适：保护性调整
- 不轻易重建整周计划

### 4. 直接记录模式

当用户提供明确、可写入的信息时，直接记录，不反复确认。

对于 Feishu 群聊中的已识别家庭成员，像下面这类表达应优先视为"可直接记录"：
- 我昨天睡了 7 小时
- 我今天有点累
- 我今天跑了 3 公里
- 我今天午饭吃了……
- 我量了血压 120/80

只要chat_id和昵称 已匹配到已知成员，就优先写表，再给简短回复；不要退回到身份确认问答。

例外：
- 信息明显缺失
- 含义模糊
- 涉及医疗风险，需要确认关键事实

#### 群聊实测已验证的话术

下列表达已经实测适合优先按"直接记录"处理：
- 我昨天睡了7个小时 -> 写入 `daily_log.sleep_hours`
- 我今天有点累 -> 更新 `daily_log.body_status_notes`，并可补 `state_tags=需要恢复`
- 我今天跑了3公里 -> 更新 `daily_log.training_brief` / `had_training`
- 我今天中午吃了面和炸鸡 -> 更新 `daily_log.today_summary` / `diet_status`
- 我今天量了血压，68 118 -> 解析为 `118/68`

#### 偏好自动提取话术（重要！）

**必须自动提取并写入 `user_preferences` 表：**

| 用户表达 | 写入字段 | 示例值 |
|---------|---------|--------|
| "我喜欢XX" | sports_likes | "散步, 游泳, 打篮球" |
| "我不喜欢XX" | sports_dislikes | "跑步" |
| "我喜欢粤菜/川菜..." | cuisine_likes | "粤菜, 清淡" |
| "我倾向地中海饮食" | nutrition_preferences | "地中海饮食" |
| "我不抽烟/不喝酒" | lifestyle_constraints | "不抽烟, 不喝酒" |
| "早起锻炼/晚间锻炼" | execution_preferences | "晚间锻炼" |

**执行流程：**
```python
# 每条消息都应执行偏好检测
from preference_service import extract_preferences_from_text, get_preference_service

result = extract_preferences_from_text(user_message)
if result['matched']:
    svc = get_preference_service(profile_id)
    for field, value in result['preferences'].items():
        svc.update_single_field(field, value, source='dialogue_extract', confidence='high')
    # 回复简短确认："好的，已记住你喜欢XX"
```

**禁止：**
- 临时性表达不要当作偏好写入（如"今天想吃火锅"）
- 不要对同一偏好反复确认

#### 新版数据记录方式（本地 SQLite）

**2026-03-26 改版后，数据写入本地 SQLite 而非飞书 Bitable：**

```python
# 方式1：使用 chat_adapter.py（推荐，自动处理身份识别）
from chat_adapter import ChatAdapter

adapter = ChatAdapter()
result = adapter.record_sleep(
    chat_id='ou_xxx',      # 从 runtime metadata 获取
    sender_name='金',     # 从 runtime metadata 获取
    hours=7.5,
    quality=8
)
# result['reply_message']: "已记录 2026-03-26 睡眠 7.5 小时，质量 8/10"
```

```python
# 方式2：使用 lifeos_service.py（直接指定 profile_id）
from lifeos_service import get_service

svc = get_service('001')  # 001=金, 002=芳芳, 003=老妈, 004=老爹
svc.record_sleep(hours=7.5, quality=8)
svc.record_fatigue(score=4, notes='有点累')
svc.record_training(brief='跑步3公里', had_training=True)
```

**身份识别流程：**
```
chat_id + name → identity_mapping → profile_id (001/002/003/004) → 本地 SQLite
```

**注意事项：**
- 新版不再调用 `bitable_ops.py`，改用 `chat_adapter.py` 或 `lifeos_service.py`
- 数据存储在 `data/lifeos.db`，不再写入飞书
- 飞书 Bitable 仅保留身份识别功能（`identity_mapping`）


## 药品记录规则（重要）

当用户提到药名时，**必须**执行以下流程，不能只记录：

```
用户：「我在吃硝苯地平、阿司匹林」
↓
智子：
1. 识别药名（硝苯地平 → 降压药，阿司匹林 → 抗血小板）
2. 返回用药提示（禁忌、服用时间、副作用）
3. 询问时间槽（早餐后/睡前等）
4. 用户回复时间槽
↓
写入 medicine_plans.json → 完成
```

**禁止：** 只记录「已记录用药信息」就结束，不引导设置提醒。

### 5. 基本资料自动更新

当用户主动告知性别、年龄等信息时，自动解析并写入 profile 表。

**触发表达示例：**
- "我是男的"
- "男，今年35岁"
- "我是女性"
- "今年40岁"
- "我今年38岁"

**更新规则：**
| 输入 | 更新字段 | 说明 |
|------|---------|------|
| "男/男/男性" | gender = "男" | 单选字段 |
| "女/女性" | gender = "女" | 单选字段 |
| "今年X岁" | birth_date | 自动估算出生日期 |

**流程：**
1. 解析用户输入中的性别/年龄
2. 调用 `update_profile_from_text(token, text)` 更新 profile 表
3. 简短回复确认

**注意：**
- 若 profile 中已有该字段且值相同，不重复更新
- 年龄自动转换为出生日期（估算为当年6月15日）
- 性别和年龄分开处理，可以只提供其中一个

---

## 个人偏好模块 V1.0

### 模块位置
`scripts/preference_service.py`

### 用途
记录用户长期生活偏好，为周计划、饮食建议、运动建议提供参考。

### 表结构
**表名：`user_preferences`**

| 字段 | 类型 | 说明 |
|------|------|------|
| profile_id | TEXT | 主键，关联 profiles |
| sports_likes | TEXT | 喜欢的运动 |
| sports_dislikes | TEXT | 不喜欢的运动 |
| food_likes | TEXT | 喜欢的食物 |
| food_dislikes | TEXT | 不喜欢的食物 |
| cuisine_likes | TEXT | 喜欢的菜系 |
| nutrition_preferences | TEXT | 营养方案偏好 |
| lifestyle_constraints | TEXT | 生活约束(不抽烟/不喝酒/早睡等) |
| execution_preferences | TEXT | 执行偏好 |
| notes | TEXT | 备注/变更历史 |
| source | TEXT | 来源 (dialogue_extract/guided_answer/manual) |
| confidence | TEXT | 置信度 (high/medium/low) |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### 提取规则

**触发条件：** 用户明确表达长期偏好时自动提取

**应该提取的表达：**
- "我喜欢散步，不喜欢跑步"
- "我比较喜欢粤菜"
- "我现在倾向地中海饮食"
- "家里老人适合清淡一点"

**不应提取的临时表达：**
- "今天想吃火锅"
- "今晚吃清淡点"

**提取逻辑：**
```python
from preference_service import extract_preferences_from_text, get_preference_service

# 从文本提取偏好
result = extract_preferences_from_text("我喜欢散步，不喜欢跑步")
# result = {'matched': True, 'preferences': {'sports_likes': '散步', 'sports_dislikes': '跑步'}}

# 如果匹配到偏好，自动写入
if result['matched']:
    svc = get_preference_service(profile_id)
    for field, value in result['preferences'].items():
        svc.update_single_field(field, value, source='dialogue_extract', confidence='high')
```

### 引导提问

**触发场景：** 仅在以下场景进行单轮补问
1. 用户请求生成饮食计划，但偏好信息不足
2. 用户请求生成运动计划，但偏好信息不足
3. 用户首次建立偏好档案时

**提问模板：**
```python
from preference_service import get_guidance_question, get_preference_service

# 检查偏好完整性
svc = get_preference_service(profile_id)
if not svc.is_preference_complete_for('sports'):
    question = get_guidance_question('sports')
    # question: "你平时更喜欢什么运动方式？比如散步、游泳、力量训练、瑜伽等"
```

### 调用规则

在以下功能生成前，自动读取偏好并注入上下文：

```python
from preference_service import build_preference_context

# 构建偏好上下文
ctx = build_preference_context(profile_id)
# ctx = """【用户偏好信息】
# - 喜欢的运动: 散步, 游泳
# - 喜欢的菜系: 粤菜, 清淡
# """
```

**接入点：**
- 周计划生成
- 饮食建议
- 运动建议
- 健康生活方式建议

---

## 6. 医疗与风险边界

必须遵守：
- 不编造历史数据
- 不忽略年龄、慢性病、健康限制
- 不根据当天一句话就重建整周计划
- 详细版不能写成理想化、不可执行的计划
- 若年龄偏大、疲劳高或存在医疗风险，计划必须保守

#### 血压记录规则（实测）

- 当前 `daily_log` 没有专用血压字段。
- 用户说"我今天量了血压，68 118"这类话时，应解析成 `118/68`。
- 血压记录当前应优先写入 `medical_records`，而不是强塞进 `daily_log`：
  - `record_type`: `其他`
  - `complaint_or_reason`: `用户自测血压`
  - `key_metrics_json`: 保存收缩压/舒张压/原始输入
  - `tags`: `心血管`
  - `summary_for_system`: 生成人类可读摘要
- 如需在日常回顾中看到血压，可额外在 `daily_log.system_comment` 中补一句摘要，但医疗留档仍以 `medical_records` 为主。

#### 症状/慢性病描述记录规则（实测）

当用户提到以下类型的内容时，**必须写入 `medical_records`**，不得仅做对话回复：

- 心律不齐、心慌、心跳异常
- 血压偏高/偏低、血压不稳
- 血糖异常（空腹、餐后）
- 关节疼痛、腰酸背痛、腿脚不便
- 头晕、头痛、失眠
- 慢性病描述（"我有糖尿病""血压一直高"）
- 身体异常事件的描述（"今天摔了一跤""生气了胸闷"）

写入格式：
- `record_type`: `症状描述` 或 `慢性病跟踪`
- `complaint_or_reason`: 用户原话或精简描述
- `key_metrics_json`: 若有具体数值则保存（如"生气时血压偏高"）
- `tags`: 根据症状归类（如`心血管``血糖``骨骼``神经系统`）
- `summary_for_system`: 生成一句人类可读摘要

**禁止：** 仅给健康建议就结束，不写记录。记录比建议更重要--建议可能出错，但记录不会丢失。

## 脚本

正式脚本（本地 SQLite 版）：
- `scripts/db.py`：数据库连接和基础 CRUD
- `scripts/init_db.py`：数据库初始化
- `scripts/health_service.py`：健康数据服务（daily_log 等）
- `scripts/medication_service.py`：用药管理服务
- `scripts/assessment_service.py`：评估服务
- `scripts/health_evaluation.py`：健康评估入口
- `scripts/preference_service.py`：个人偏好服务

预留脚本（暂不实现）：
- `scripts/feishu_export.py`：飞书导出接口

旧版脚本（已废弃）：
- `scripts/bitable_ops.py`：旧版飞书读写，已被 `db.py` + `health_service.py` 替代

## 配置

- 主配置：`config/config.json`（数据库路径、用户列表）
- 用户配置：`config/bitable_config.json`（飞书相关，仅 identity_mapping 保留用于身份识别）
- SQLite 路径使用相对路径，便于迁移

### 身份识别

使用 `config/bitable_config.json` 中的 `identity_mapping` 进行用户身份路由，找到对应的 `profile_id`（如 `001`、`002`）后，操作本地 SQLite 数据库。

- `scripts/bitable_ops.py` 必须兼容英文表键和中文表名，例如：
  - `daily_log` <-> `每日记录`
  - `medical_records` <-> `医疗记录`
  - `rules` <-> `规则`
  - `medication_supplement_list` <-> `药品补剂表`
- 日期字段写入前要自动规范化成飞书可接受的毫秒时间戳；不要要求调用方手工传时间戳。
- 常见日期输入如 `2026-03-21`、`2026/03/21`、`2026-03-21 10:20:30` 都应自动转换。

## 参考文件

需要字段/表结构时读取：
- `references/table_schema.md`

需要周计划规则、输出格式、节奏原则时读取：
- `references/weekly-planning.md`

## 调试经验记录

### 1. PowerShell 执行 Python 脚本的语法

**问题现象：**
```
& was not followed by a valid statement
```

**原因：** PowerShell 不支持 `&&` 语法，这是 Bash 的语法

**正确写法：**
```powershell
# 错误 ❌
cd "path" && python script.py

# 正确 ✅ (PowerShell)
cd "path"; python script.py

# 或者分段执行
cd "path"
python script.py

# 或者用 & 调用
& "C:\path\python.exe" script.py
```

### 2. Python 字符串中的引号嵌套

**问题现象：**
```
SyntaxError: unterminated string literal
```

**原因：** 在 `-c "python code"` 中嵌套了复杂的字符串，引号冲突

**正确写法：**
- 创建独立的 `.py` 脚本文件执行
- 避免在命令行中直接写复杂的多行 Python 代码
- 简单测试可用：`python -c "import db; print(db.query_one('SELECT 1'))"`

### 3. Windows 中文编码问题

**问题现象：**
- 中文输出显示为乱码（如 `����`）
- 这不影响实际功能，只是显示问题

**解决：**
- 脚本中避免中文输出或使用英文字符
- 或在脚本开头添加：`# -*- coding: utf-8 -*-`
- Windows 控制台默认 GBK 编码，无法彻底解决，但不影响数据正确性

### 4. 数据库图片路径访问

**问题现象：**
- 用户发的图片（如 `img_v3_xxx`）是飞书图片引用
- 当前环境无法直接访问飞书图片资源

**正确流程：**
- 飞书群聊/私聊中发图片 → 机器人接收 → 下载到本地媒体目录 → 读取本地文件处理
- 图片路径：`C:\Users\Jin\.openclaw\media\inbound\`

### 5. 调试建议

- **优先使用独立脚本**：避免复杂的命令行嵌套
- **创建临时测试脚本**：如 `test_debug.py`，方便反复调试
- **数据库操作验证**：先在 Python 交互环境测试 SQL
- **图片处理**：确保图片已下载到本地后再处理

### 本轮联调结论

- 群聊 @ 机器人 + 2 号家庭成员 sender_id 路由已跑通。
- `daily_log` 目前采用"同一天合并更新"策略，而不是每句新建一条记录。
- 详细版周计划已经验证可以成功写入 `weekly_plan` 和 `weekly_plan_detail`。
- 若出现"表已写成功，但聊天回复没有完整发出来"的现象，先记录为**回复层卡顿/输出层问题**，不必立即怀疑表写入失败。

## 风格

- 简洁
- 冷静
- 实用
- 个体化
- 涉及医疗时保守

### 主动引导策略（每次回复末尾必须执行）

**原则：被动应答 + 主动拓展，不生硬追问。**

每次写表完成后，在回复末尾补一句自然的后续引导，帮助用户持续追踪健康数据。语气像家人之间的关心，不像是客服问卷。

**引导句生成规则：**

|刚记录的数据类型|推荐引导句（选一个自然的）|
|---|---|
|睡眠时长|「今天打算怎么安排活动？」|
|身体疲劳/状态|「有什么不舒服的地方吗？」|
|饮食|「今天有锻炼计划吗？」|
|跑步/运动|「跑完感觉怎么样？」|
|血压/体检|「最近睡眠质量如何？」|
|用药/补剂|「今天饮食正常吗？」|
|周计划相关|「还有什么想调整的吗？」|

**禁止：**
- 不要连续两条消息都用追问结尾
- 不要在用户刚说完一件事就追问细节，休息一下
- 不要用「请问您今天…？」「请问您昨天…」这种生硬开场白

---

## 医疗报告归档助手 V1.1（双阶段架构）

### 模块位置
`medical_report_archive/`

### 架构
- **阶段A**：视觉识别
- **阶段B**：代码写入飞书

### 触发条件
当用户发送以下内容或者类似的词语时激活：
- 发送医疗报告图片
- 发送"归档医疗报告"
- 发送"上传体检报告"
注意，如果发送内容包含图片，必须用 image tool，而不是用functions.read

### 工作流
```
用户发图片
    ↓
阶段A：用image tool视觉分析 → 输出结构化JSON（含风险评估）
    ↓
阶段B：风险解析 → 归档策略判定 → 用户核实提示 → 等待确认
    ↓
用户回复"确认/强制归档/放弃" → 执行对应归档策略
```

---

### 阶段A：视觉识别与风险审计

 用image tool，带上`medical_report_archive/stage_a_prompt.md`中的prompt 分析图片。

**阶段A输出必须包含：**

```json
{
  "report_meta": { ... },
  "items": [
    {
      "raw_name": "...",
      "standard_name": "...",
      "value": ...,
      "unit": "...",
      "reference_range": "...",
      "abnormal_flag": "...",
      "confidence": 0.95,
      "risks": [
        {"risk_type": "column_shift", "risk_level": "high", "description": "..."}
      ],
      "review_priority": "high"
    }
  ],
  "summary": "...",
  "table_structure_analysis": {
    "overall_risk_level": "low|medium|high",
    "has_possible_shift": false,
    "column_risks": [],
    "row_risks": []
  },
  "confidence_check": {
    "extraction_confidence": 92,
    "identity_match_score": 85,
    "consistency_score": 90,
    "total_archive_confidence": 89,
    "hard_conflict": false,
    "conflict_notes": "",
    "archive_recommendation": "可归档"
  },
  "raw_extract": {"ocr_text": "..."}
}
```

---

### 阶段B：归档执行（v1.1 增强版）

**核心原则：从"直接写入"升级为"风险感知 + 有条件归档 + 用户重点核实"**

#### 步骤1-6 归档流程

```
步骤1：接收视觉识别 JSON
步骤2：执行风险解析（三级风险提取）
步骤3：执行归档前置信度校验
步骤4：生成"用户核实提示"（只展示需核实内容）
步骤5：等待用户确认
步骤6：根据确认结果执行归档策略（A/B/C/D/E策略）
```

#### 风险分级规则

**1. 全局风险（表级）**
```python
if table_structure_check.overall_risk_level == "high":
    global_risk = "high"
elif table_structure_check.has_possible_shift:
    global_risk = "medium"
else:
    global_risk = table_structure_check.overall_risk_level  # low
```

**2. 项目风险（item级）**
```python
for item in items:
    if item.review_priority == "high":
        item_risk = "high"
    elif any(f in ["column_shift", "row_shift"] for f in item.risk_flags):
        item_risk = "high"
    elif any(f in ["unit_mismatch", "range_mismatch"] for f in item.risk_flags):
        item_risk = "medium"
    else:
        item_risk = "low"
```

**3. 关键项目判定**
```python
CRITICAL_ITEMS = [
    "LDL-C", "LDL_C", "低密度脂蛋白",
    "HbA1c", "HbA1C", "糖化血红蛋白",
    "ALT", "谷丙转氨酶",
    "AST", "谷草转氨酶",
    "Cr", "Creatinine", "肌酐",
    "BUN", "尿素氮",
    "UA", "尿酸",
    "血压", "收缩压", "舒张压", "SBP", "DBP"
]
```

#### 归档策略（A/B/C/D/E五级策略）

| 策略 | 触发条件 | 处理方式 |
|-----|---------|---------|
| **A - FULL_ARCHIVE** | 无识别风险 + 无硬冲突 | 正常归档：写入raw_reports → reports_master → indicators_detail → 更新health_master |
| **B - ARCHIVE_WITH_WARNING** | 存在中风险（识别过程问题） | 允许归档，但标记为"已归档-含风险"，需提示用户核实 |
| **C - SAVE_NOT_UPDATE_PROFILE** | 关键项目有**识别风险** | 只写入raw_reports + reports_master + indicators_detail（标记未确认），**不更新health_master** |
| **D - RAW_ONLY** | 全局高风险（表级问题严重） | 仅保存raw_reports，提示用户"需人工核对后再归档" |
| **E - BLOCKED** | 硬冲突存在 | 禁止自动归档，必须用户选择强制归档或放弃 |

**重要说明：**
- 指标异常本身**不会**触发策略C（如肌酐偏高是正常现象）
- 策略C只会在**识别过程有风险**时触发（如OCR错误、数值错位、表格结构混乱）
- 只要识别过程无风险，即使指标严重异常，也应走策略A（FULL_ARCHIVE）

**硬冲突检测规则（必须严格遵守）：**

以下情况必须判定为**硬冲突（hard_conflict = true）**，触发 **E级策略（BLOCKED）**：

| 冲突类型 | 判定条件 | 说明 |
|---------|---------|------|
| **年龄冲突** | 报告患者年龄与发言者profile年龄相差 > 20岁 | 如：发言者35岁，报告患者84岁 |
| **性别冲突** | 报告患者性别与发言者profile性别不一致 | 如：发言者男，报告患者女 |
| **身份不明** | 报告患者姓名模糊/缺失，且年龄与发言者不符 | 无法确认患者身份 |
| **发言者代理** | 发言者明确表示"帮别人问"/"这是别人的报告" | 需确认实际患者身份 |

**硬冲突处理流程：**
```
检测到硬冲突
    ↓
立即停止自动归档
    ↓
向用户展示冲突详情
    ↓
等待用户选择：
  1. 「强制归档」→ 要求用户明确指定目标家庭成员
  2. 「放弃归档」→ 终止流程
```

**重要原则：**
- **宁可暂停，不可错归** - 身份不明确时，禁止擅自推测归档
- **禁止推测** - 不得根据"年龄相近""可能是家人"等推测自动归档
- **用户确认优先** - 必须得到用户明确确认后才能继续

---

**策略判定伪代码：**
```python
def determine_strategy(risk_assessment, report_meta, sender_profile):
    # 首先检测硬冲突
    hard_conflict, conflict_reason = check_hard_conflict(report_meta, sender_profile)

    # E: 硬冲突
    if hard_conflict:
        risk_assessment["has_hard_conflict"] = True
        risk_assessment["conflict_notes"] = conflict_reason
        return ArchiveStrategy.BLOCKED

    # D: 全局高风险（表级问题）
    if risk_assessment["global_risk_level"] == "high":
        return ArchiveStrategy.RAW_ONLY

def check_hard_conflict(report_meta, sender_profile):
    """
    检测硬冲突
    返回: (is_conflict, conflict_reason)
    """
    # 年龄冲突（相差超过20岁）
    if report_meta.get("age") and sender_profile.get("age"):
        age_diff = abs(report_meta["age"] - sender_profile["age"])
        if age_diff > 20:
            return True, f"年龄冲突：报告患者{report_meta['age']}岁，发言者{sender_profile['age']}岁，相差{age_diff}岁"

    # 性别冲突
    if report_meta.get("gender") and sender_profile.get("gender"):
        if report_meta["gender"] != sender_profile["gender"]:
            return True, f"性别冲突：报告患者{report_meta['gender']}，发言者{sender_profile['gender']}"

    # 患者姓名缺失或模糊，且年龄明显不符
    if not report_meta.get("patient_name") or report_meta.get("patient_name") == "":
        if report_meta.get("age") and sender_profile.get("age"):
            if abs(report_meta["age"] - sender_profile["age"]) > 10:
                return True, f"身份不明：报告患者年龄{report_meta['age']}岁与发言者年龄{sender_profile['age']}岁不符，且患者姓名缺失"

    return False, ""
```

    # C: 关键项目有识别风险（非指标异常）
    # 检查是否有识别风险（而非指标本身是否异常）
    if risk_assessment["critical_items_with_risk"] and risk_assessment["high_risk_count"] > 0:
        return ArchiveStrategy.SAVE_NOT_UPDATE_PROFILE

    # B: 中风险（识别过程问题）
    if risk_assessment["medium_risk_count"] > 0 or risk_assessment["global_risk_level"] == "medium":
        return ArchiveStrategy.ARCHIVE_WITH_WARNING

    # A: 无识别风险 + 无硬冲突
    return ArchiveStrategy.FULL_ARCHIVE
```

#### 用户核实提示（重点改造：只展示需核实内容）

**输出结构：**

```
==================================================
📋 医疗报告归档核实
==================================================

【识别结果摘要】
  报告类型：{report_type}
  检查日期：{exam_date}
  医院：{hospital}
  患者：{patient_name} ({gender}, {age}岁)
  关键异常项：{abnormal_count}项
    {key_abnormal_items}

【风险提示】

1. 表格风险
   {table_risk_items}

2. 重点核实项目（高风险 items）
   {high_risk_items}

3. 可疑字段
   {suspicious_fields}

【归档建议】
   {archive_recommendation}

【可选操作】
   {available_actions}

==================================================
请回复操作编号或关键词
==================================================
```

---

### 目标表结构（v1.1 新增字段）

#### raw_reports 表（新增字段）
| 字段名 | 类型 | 说明 |
|-------|------|------|
| table_risk_level | string | 表格风险等级 (low/medium/high) |
| has_structure_risk | boolean | 是否存在结构风险 |
| high_risk_item_count | number | 高风险项目数量 |
| medium_risk_item_count | number | 中风险项目数量 |
| risk_summary | string | 风险摘要 |
| requires_review | boolean | 是否需要人工核实 |
| archive_status | string | 归档状态 (pending/archived/rejected/manual_review) |

#### indicators_detail 表（新增字段）
| 字段名 | 类型 | 说明 |
|-------|------|------|
| risk_flags | string | 风险标记（JSON数组） |
| review_priority | string | 复核优先级 (low/medium/high) |
| is_verified | boolean | 是否已确认 |
| is_used_for_profile | boolean | 是否用于主档案 |

---

### 使用示例（v1.1 完整流程）

```
用户发送体检报告图片
    ↓
阶段A：视觉识别 + 风险审计
    ↓
阶段B步骤2：风险解析（提取三级风险）
    ↓
阶段B步骤3：信度校验（计算总置信度）
    ↓
阶段B步骤4：生成用户核实提示（只展示需核实内容）
    ↓
阶段B步骤5：等待用户确认
    ↓
用户回复"确认归档" / "强制归档" / "放弃"
    ↓
阶段B步骤6：执行对应归档策略（A/B/C/D/E）
    ↓
完成归档 / 部分归档 / 放弃归档
```


---

## 健康评估模块 v1.0

### 触发条件

当用户发送以下内容时激活：
- 「健康评估」
- 「评估一下」
- 「评估现在健康状况」
- 「给我做个健康评估」
- 「健康状态怎么样」

### 评估流程

```
用户请求健康评估
    │
    ├─ 1. 读取 profile（年龄、性别、训练基础、健康目标）
    ├─ 2. 读取最近 7 天 daily_log（自动扩展至 14/30 天）
    ├─ 3. 读取最近 30 天 medical_records
    ├─ 4. 读取最近 7 天 event_log
    ├─ 5. 读取当前 medication_supplement_list
    │
    ├─ 6. 执行五维评分
    │     ├─ 心血管 (30%): 血压、心率、医疗记录、年龄
    │     ├─ 肌肉力量 (25%): 训练频次、训练基础、体重变化
    │     ├─ 代谢体重 (20%): BMI、体重、饮食状态
    │     ├─ 恢复睡眠 (15%): 睡眠时长、质量、疲劳评分
    │     └─ 执行度 (10%): 计划执行率、训练完成率
    │
    ├─ 7. 风险信号判定（绿/黄/红）
    ├─ 8. 数据置信度评估
    ├─ 9. 生成简版报告 + 图表数据
    │     ├─ 生成雷达图 PNG -> `output/health_radar.png`
    │     └─ 生成柱状图 PNG -> `output/health_bar.png`
    │
    └─ 10. 展示报告 + 图表图片
          ├─ 返回文本报告（五维评分、风险信号、建议）
          ├─ 返回雷达图图片
          └─ 询问用户是否保存到记录表
                ├─ 用户确认 -> 写入 health_evaluation 表
                └─ 用户拒绝 -> 仅展示报告
```

### 五维评分权重

| 维度 | 权重 | 数据来源 |
|------|------|---------|
| 心血管 | 30% | 血压、心率、医疗记录中的心血管问题、年龄 |
| 肌肉力量 | 25% | 训练记录、训练基础、体重变化 |
| 代谢体重 | 20% | 体重、BMI、饮食状态 |
| 恢复睡眠 | 15% | 睡眠时长、睡眠质量、疲劳评分 |
| 执行度 | 10% | 计划执行情况、训练完成度 |

### 总体状态判定

| 总分区间 | 状态 |
|---------|------|
| >= 85 | 优秀 |
| 75-84 | 良好 |
| 60-74 | 一般 |
| 45-59 | 需改善 |
| < 45 | 较差 |

### 输出内容

1. **五维评分 + 总分**
2. **风险信号**（颜色标记 + 原因说明）
3. **雷达图图片**（PNG，自动生成）
4. **柱状图图片**（PNG，自动生成）
5. **雷达图/柱状图数据**（JSON，保存到 Bitable 用）
6. **简版健康报告**（文本）
7. **数据来源说明**
8. **数据覆盖情况**
9. **评估置信度**
10. **缺失数据字段**

**图片返回方式：** 使用 `MEDIA:./skills/lifeos-main/output/health_radar.png` 格式返回

### 写入时机

- 评估完成后自动生成图表图片并展示报告
- 询问用户：「要保存这次评估记录吗？」
- 用户回复「是/保存/确认」-> 调用 `save_health_evaluation()` 写入
- 用户回复「否/不用/算了」-> 仅展示，不写入

### 健康评估记录表（health_evaluation）

需要在飞书多维表格中创建新表，表名不限（系统用 `health_evaluation` 键访问）。

**表结构：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| eval_id | 文本 | 主键 UUID |
| user_id | 文本 | 用户ID |
| 评估时间 | 日期时间 | 评估执行时间 |
| 数据来源说明 | 多行文本 | 本次评估使用了哪些数据源 |
| 数据时间范围 | 多行文本 | 数据覆盖的时间范围 |
| 数据覆盖情况 | 多行文本 | 各维度数据完整度 |
| 评估置信度 | 数字 | 0-100% |
| 心血管评分 | 数字 | 0-100 |
| 肌肉力量评分 | 数字 | 0-100 |
| 代谢体重评分 | 数字 | 0-100 |
| 恢复睡眠评分 | 数字 | 0-100 |
| 执行度评分 | 数字 | 0-100 |
| 总分 | 数字 | 0-100 |
| 风险信号 | 多行文本 | 各维度风险信号 |
| 总体状态 | 单选 | 优秀/良好/一般/需改善/较差 |
| 主要问题 | 多行文本 | 本次评估发现的主要问题 |
| 建议行动 | 多行文本 | 改进建议 |
| 简版评估报告 | 多行文本 | 人类可读简版报告 |
| 图表数据_JSON | 多行文本 | 雷达图+柱状图数据JSON |
| 解释_JSON | 多行文本 | 各维度评分解释JSON |
| 评估时年龄 | 数字 | 评估时的年龄 |
| 评估时性别 | 单选 | 男/女 |
| 评估时训练基础 | 多行文本 | profile中的训练基础 |
| 评估时健康目标 | 多行文本 | profile中的健康目标 |
| 缺失数据字段 | 多行文本 | 本次评估缺失的字段 |

### 脚本入口

- `scripts/health_evaluation.py` - 健康评估核心逻辑
- `python health_evaluation.py display` - 运行并格式化输出
- `python health_evaluation.py run` - 运行并输出 JSON
- `python health_evaluation.py run_and_save` - 运行并保存到表

### 配置

在 `config/bitable_config.json` 的 `health_evaluation_table_ids` 中配置各用户的表 ID：

```json
{
  "health_evaluation_table_ids": {
    "lifeos_jin": "tblHE001PLACEHOLDER",
    "lifeos_laolao": "tblHE002PLACEHOLDER",
    "lifeos_laoma": "tblHE003PLACEHOLDER",
    "lifeos_fangfang": "tblHE004PLACEHOLDER"
  }
}
```

> 注意：开发阶段使用占位符 table ID，需要在飞书创建真实表后替换。

---

## 药品提醒模块 v1.0

### 模块位置
`medicine/`

### 架构
- **medicine/index.ts** - 主入口，消息路由
- **medicine/parser.ts** - 药物识别
- **medicine/time_slot.ts** - 时间槽定义
- **medicine/storage.ts** - JSON 文件存储
- **medicine/context.ts** - 对话上下文
- **medicine/reminder.ts** - 提醒逻辑

### 触发条件

当用户发送以下内容时激活：
- 提到具体药名（阿托伐他汀、二甲双胍等）
- 「吃药」「服药」「我在吃XXX」
- 「已吃」「吃了」- 确认服药

### 工作流程

```
用户提到药名
    ↓
parser.ts 识别药物名称
    ↓
返回最多3条药物提示
    ↓
询问服药时间（时间槽选择）
    ↓
用户选择时间槽（如"早餐后"）
    ↓
storage.ts 创建用药计划
    ↓
回复确认（记住渠道+@用户）
```

### 时间槽

固定8个时间槽：
| 时间槽 | 大致时段 |
|--------|---------|
| 起床后 | 6:00-8:00 |
| 早餐前 | 7:00-8:00 |
| 早餐后 | 8:00-9:00 |
| 午餐前 | 11:00-12:00 |
| 午餐后 | 12:00-14:00 |
| 晚餐前 | 17:00-18:00 |
| 晚餐后 | 18:00-20:00 |
| 睡前 | 21:00-23:00 |

### 提醒调度

提醒检查通过独立的 cron 任务触发：
- `scripts/check_medicine_reminders.py` - 每分钟执行
- 检查当前时间槽
- 按渠道+时间槽聚合
- 群里必须 @用户，私聊不需要

### 数据结构

**medicine_plans.json** - 用药计划：
```json
{
  "id": "med_xxx",
  "user_id": "sender_id",
  "user_name": "用户名",
  "drug_name": "阿托伐他汀",
  "time_slot": "睡前",
  "channel_type": "group",
  "channel_id": "chat_id",
  "mention_target": "@用户名",
  "created_at": "ISO时间",
  "active": true
}
```

**medicine_records.json** - 每日服药记录：
```json
{
  "id": "rec_xxx",
  "plan_id": "med_xxx",
  "user_id": "sender_id",
  "drug_name": "阿托伐他汀",
  "date": "2026-03-25",
  "time_slot": "睡前",
  "status": "pending|taken|missed",
  "taken_at": "ISO时间"
}
```

### 集成方式

在飞书消息处理中，当消息未被其他模块处理时，调用：

```typescript
import { handleMedicineMessage } from './medicine/index';

const result = handleMedicineMessage(
  text,           // 消息文本
  chatId,         // 群/私聊ID
  senderId,       // 发送者ID
  senderName,     // 发送者昵称
  channelType,    // 'group' | 'direct'
  mentionTarget   // 群里@的目标
);

if (result.handled) {
  // 发送回复
  sendReply(result.reply);
}
```

### 提醒脚本

```bash
# 每分钟执行的提醒脚本
python scripts/check_medicine_reminders.py
```

该脚本由系统 cron/调度器触发，返回需要发送的提醒列表。
## 身份路由维护

### 硬规则

- 所有身份路由配置统一维护在 `config/bitable_config.json`
- `bitables` 是"家庭成员 -> Bitable / profile"绑定的唯一来源
- `identity_mapping` 是"runtime `chat_id + sender_name` -> 家庭成员身份"映射的唯一来源
- 不要在业务脚本里硬编码 chat_id、sender_name 或成员到 Bitable 的映射关系

### 运行时优先级

1. 先用 runtime metadata 中的 `chat_id + sender_name` 命中 `identity_mapping`
2. 如果未命中，再 fallback 到成员主绑定，如 `owner_feishu_id` 或 `owner_profile_id`
3. 只有前两者都失败时，才允许询问用户身份，或依赖用户文本中的自报身份

### 命中后的行为要求

- 一旦 `identity_mapping` 命中，必须直接路由到对应的 Bitable / profile
- 一旦 `identity_mapping` 命中，不得再追问"你是谁""请先绑定身份"等重复身份确认问题
- `sender_id` 只能作为兼容信息，不能替代 `chat_id + sender_name` 成为主路由依据

### 维护规则

- 新增家庭成员时：
  - 先在 `bitables` 中新增成员配置
  - 再在 `identity_mapping` 中新增至少一条该成员的直聊映射
  - 如果该成员会在固定群聊中使用，再补充对应群聊的真实 `chat_id` / `chat_key` 映射
- 修改成员昵称或别名时：
  - 只修改 `identity_mapping.names`
- 修改某条路由指向哪个成员、哪个 profile 时：
  - 修改 `identity_mapping.bitable_key` 和/或 `identity_mapping.profile_id`
- 修改成员主身份 ID 时：
  - 修改 `bitables.<member>.owner_feishu_id` 或相关主绑定字段
- 不要为了适配个例去改脚本逻辑；优先改 `config/bitable_config.json`

### 推荐的 `identity_mapping` 结构

```json
{
  "chat_type": "direct",
  "chat_id": "ou_xxx",
  "chat_key": "ou_xxx",
  "name": "芳芳",
  "names": ["芳芳", "方芳"],
  "bitable_key": "lifeos_fangfang",
  "profile_id": "002"
}
```

### 修改后检查清单

- 确认 runtime metadata 能正确命中目标成员
- 确认数据写入了正确的 Bitable
- 确认命中路由后，agent 不会再重复追问身份
