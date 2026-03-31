# LifeOS 多维表格 - 表结构参考

## 表概览

| # | 表名 | Key | Table ID | 主要用途 |
|---|------|-----|---------|---------|
| 1 | 个人资料 | profile | tbl2rpgHhR9rm6m0 | 用户基本信息和健康基线 |
| 2 | 每日记录 | daily_log | tbl9i2SehAhTZKrg | 每日健康状态追踪 |
| 3 | 事件记录 | event_log | tblEyhr3CKUxqSgc | 影响健康的事件记录 |
| 4 | 医疗记录 | medical_records | tblIvTWyBUopNeyt | 医疗检查和诊断记录 |
| 5 | 健康知识 | health_knowledge | tblNyrMIcXTZK3Jz | 健康相关知识库 |
| 6 | 规则 | rules | tbl2Sbdeq3jXx4Lf | 行动规则 |
| 7 | 周计划 | weekly_plan | tblkHBrurIm6f0j0 | 每周计划 |
| 8 | 周计划详情 | weekly_plan_detail | tblGHnXFij97QF9d | 每日拆解后的周计划明细 |
| 9 | 药品补剂列表 | medication_supplement_list | tblDX3SHgxlFTsPI | 药品和补剂管理 |

---

## 1. 个人资料 (profile)

### 用途
存储用户的基本信息、健康基线和长期目标。

### 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| profile_id | 文本 | 主键 |
| name | 文本 | 姓名 |
| gender | 单选 | 男/女/其他 |
| birth_date | 日期 | 出生日期（计算年龄用） |
| height_cm | 数字 | 身高(cm) |
| baseline_weight_kg | 数字 | 基线体重(kg) |
| body_fat_estimate | 数字 | 体脂估算(%) |
| resting_heart_rate | 数字 | 静息心率 |
| blood_type | 单选 | 血型 |
| allergies | 多行文本 | 过敏信息 |
| chronic_conditions | 多行文本 | 慢性病 |
| past_major_issues | 多行文本 | 既往重大问题 |
| family_history | 多行文本 | 家族病史 |
| long_term_goal | 单选 | 长期目标（减脂/增肌/维持/恢复/抗衰/养生） |
| current_phase | 单选 | 当前阶段（减脂期/增肌期/维持期/恢复期/抗衰期/养生期） |
| life_principles | 多行文本 | 生活原则 |
| health_constraints | 多行文本 | 健康限制 |

---

## 2. 每日记录 (daily_log)

### 用途
追踪每日健康状态、训练、饮食等。

### 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| daily_id | 文本 | 主键 |
| profile_id | 文本 | 关联 profile |
| date | 日期 | 记录日期 |
| sleep_hours | 数字 | 睡眠时长(h) |
| sleep_quality | 单选 | 很差/差/一般/好/很好 |
| energy_score | 数字 | 精力评分(1-10) |
| fatigue_score | 数字 | 疲劳评分(1-10) |
| mood_score | 数字 | 心情评分(1-10) |
| stress_score | 数字 | 压力评分(1-10) |
| weight_kg | 数字 | 当日体重(kg) |
| body_status_notes | 多行文本 | 身体状态备注 |
| had_training | 复选框 | 是否训练 |
| training_brief | 多行文本 | 训练简述 |
| diet_status | 单选 | 良好/一般/失控/聚餐/未记录 |
| supplement_status | 单选 | 完成/部分完成/未完成/未安排 |
| abnormal_event_flag | 复选框 | 是否有异常事件 |
| abnormal_event_summary | 多行文本 | 异常事件摘要 |
| today_summary | 多行文本 | 今日总结 |
| state_tags | 多选 | 状态标签 |
| plan_status | 单选 | 按计划/部分调整/偏离/无计划 |
| next_day_risk | 单选 | 低/中/高 |
| system_comment | 多行文本 | 系统评论 |

### 状态标签 (state_tags) 选项

- 恢复不足
- 高疲劳
- 状态稳定
- 压力偏高
- 执行良好
- 执行中断
- 饮食波动
- 身体不适
- 需要恢复
- 节奏被打断

---

## 3. 事件记录 (event_log)

### 用途
记录影响健康节奏的各类事件。

### 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| event_id | 文本 | 主键 |
| profile_id | 文本 | 关联 profile |
| event_datetime | 日期时间 | 事件时间 |
| related_date | 日期 | 相关日期 |
| event_type | 单选 | 事件类型 |
| event_title | 文本 | 事件标题 |
| description | 多行文本 | 事件描述 |
| impact_scope | 多选 | 影响范围 |
| severity | 单选 | 严重程度 |
| expected_duration | 单选 | 预期持续时间 |
| recovery_needed | 复选框 | 是否需要恢复 |
| linked_daily_log | 文本 | 关联 daily_log |
| extracted_tags | 多选 | 提取标签 |
| system_interpretation | 多行文本 | 系统解读 |

### 事件类型 (event_type) 选项

- 出差
- 加班
- 熬夜
- 聚餐
- 生病
- 旅行
- 情绪
- 其他

### 影响范围 (impact_scope) 选项

- 睡眠
- 训练
- 饮食
- 情绪
- 恢复

### 提取标签 (extracted_tags) 选项

- 计划扰动
- 高压
- 饮食风险
- 恢复风险

---

## 4. 医疗记录 (medical_records)

### 用途
存储医疗检查、诊断、用药等记录。

### 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| record_id | 文本 | 主键 |
| profile_id | 文本 | 关联 profile |
| record_date | 日期 | 记录日期 |
| record_type | 单选 | 记录类型 |
| institution | 文本 | 医疗机构 |
| department | 文本 | 科室 |
| complaint_or_reason | 多行文本 | 主诉/原因 |
| key_metrics_json | 多行文本 | 关键指标(JSON格式) |
| abnormal_items | 多行文本 | 异常项目 |
| diagnosis | 多行文本 | 诊断 |
| doctor_advice | 多行文本 | 医生建议 |
| medications | 多行文本 | 用药 |
| severity_level | 单选 | 严重程度（低/中/高） |
| follow_up_needed | 复选框 | 是否需要随访 |
| next_review_date | 日期 | 下次复查日期 |
| source_file_link | 文本 | 原始文件链接 |
| tags | 多选 | 标签 |
| summary_for_system | 多行文本 | 系统摘要 |

### 记录类型 (record_type) 选项

- 体检
- 血检
- 门诊
- 影像
- 用药
- 其他

### 标签 (tags) 选项

- 血脂
- 血糖
- 睡眠
- 消化
- 心血管

---

## 5. 健康知识 (health_knowledge)

### 用途
存储个体化健康知识、原则和经验。

### 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| knowledge_id | 文本 | 主键 |
| title | 文本 | 标题 |
| knowledge_type | 单选 | 知识类型（通用/个体/原则/医疗） |
| category | 单选 | 分类 |
| source_type | 单选 | 来源类型 |
| source_ref | 文本 | 来源引用 |
| content | 多行文本 | 内容 |
| applicable_conditions | 多行文本 | 适用条件 |
| not_applicable_conditions | 多行文本 | 不适用条件 |
| evidence_strength | 单选 | 证据强度（弱/中/强） |
| confidence | 数字 | 置信度 |
| status | 单选 | 状态（候选/已确认/停用） |
| first_observed_at | 日期 | 首次观察日期 |
| last_verified_at | 日期 | 最后验证日期 |
| related_rules | 文本 | 关联规则 |
| tags | 多选 | 标签 |
| created_at | 日期时间 | 创建时间 |
| updated_at | 日期时间 | 更新时间 |

---

## 6. 规则 (rules)

### 用途
存储健康管理规则，用于决策支持。

### 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| rule_id | 文本 | 主键（如 R002, R003） |
| rule_name | 文本 | 规则名称 |
| rule_type | 单选 | 规则类型（硬规则/软规则/演化规则） |
| target_scope | 单选 | 目标范围 |
| trigger_conditions | 多行文本 | 触发条件 |
| action | 多行文本 | 执行动作 |
| priority | 数字 | 优先级（10最高） |
| exception_conditions | 多行文本 | 例外条件 |
| source_type | 单选 | 来源类型（用户/知识/医疗/系统） |
| source_ref | 文本 | 来源引用 |
| confidence | 数字 | 置信度 |
| success_rate | 数字 | 成功率 |
| enabled | 复选框 | 是否启用 |
| review_status | 单选 | 审核状态（候选/已确认/停用） |
| created_at | 日期时间 | 创建时间 |
| last_triggered_at | 日期时间 | 最后触发时间 |
| active_phase | 单选 | 活跃阶段 |
| notes | 多行文本 | 备注 |
| created_by | 单选 | 创建者（用户/系统） |
| updated_at | 日期时间 | 更新时间 |

### 优先级说明

- **10**：最高优先级（保护性硬规则，如医疗限制、身体不适保护）
- **7-9**：一般执行规则
- **1-6**：辅助规则

---

## 7. 周计划 (weekly_plan)

### 用途
存储每周计划，以周计划为核心驱动日常生活。

### 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| weekly_plan_id | 文本 | 主键 |
| profile_id | 文本 | 关联 profile |
| week_start | 日期 | 周开始日期 |
| week_end | 日期 | 周结束日期 |
| plan_status | 单选 | 状态（草稿/生效中/已完成/已调整） |
| phase | 单选 | 阶段（减脂期/增肌期/维持期/恢复期/抗衰期/养生期） |
| weekly_goal | 多行文本 | 本周主要目标（一句话） |
| focus_areas | 多选 | 本周重点领域 |
| training_target | 多行文本 | 本周训练安排 |
| diet_target | 多行文本 | 本周饮食策略 |
| supplement_target | 多行文本 | 本周补剂/药品执行原则 |
| medical_notes | 多行文本 | 本周医疗注意事项 |
| key_risks | 多行文本 | 本周风险点 |
| adjustment_strategy | 多行文本 | 若状态变差/有事件的调整方式 |
| success_criteria | 多行文本 | 这周怎样算完成不错 |
| triggered_rules | 文本 | 本周触发的规则 |
| source_summary | 多行文本 | 本周计划依据 |
| execution_score | 数字 | 执行评分 |
| review_summary | 多行文本 | 复盘摘要 |
| next_week_notes | 多行文本 | 下周备注 |
| created_at | 日期 | 创建时间 |
| updated_at | 修改时间 | 更新时间 |

### 重点领域 (focus_areas) 选项

- 训练
- 饮食
- 睡眠
- 恢复
- 补剂
- 医疗

### 周计划生成依据 (source_summary) 应包含

- 年龄与个人资料影响
- 最近7-14天状态趋势
- 当前阶段与近期目标
- 本周已知事件
- 触发的规则

---

## 8. 周计划详情 (weekly_plan_detail)

### 用途
存储详细版周计划拆解到每天的执行明细。

### 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| weekly_plan_id | 文本 | 关联 weekly_plan |
| profile_id | 文本 | 关联 profile |
| plan_date | 日期 | 计划日期 |
| weekday | 单选/文本 | 周几 |
| daily_theme | 文本 | 今日主题 |
| training_detail | 多行文本 | 训练安排 |
| diet_detail | 多行文本 | 饮食策略 |
| supplement_medication_detail | 多行文本 | 补剂/药品安排 |
| recovery_detail | 多行文本 | 恢复安排 |
| fallback_plan | 多行文本 | 备用方案 |
| priority_level | 单选 | 优先级 |
| notes | 多行文本 | 补充说明 |

---

## 9. 药品补剂列表 (medication_supplement_list)

### 用途
管理用户的药品和补剂计划。

### 字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| item_id | 文本 | 主键 |
| profile_id | 文本 | 关联 profile |
| name | 文本 | 名称 |
| item_type | 单选 | 类型（补剂/药品） |
| dosage | 文本 | 用量 |
| frequency | 单选 | 频率（每天/每周/按需） |
| timing | 多选 | 服用时间 |
| with_food | 单选 | 与食物关系（随餐/空腹/均可） |
| start_date | 日期 | 开始日期 |
| end_date | 日期 | 结束日期 |
| purpose | 多行文本 | 用途 |
| precautions | 多行文本 | 注意事项 |
| source_type | 单选 | 来源（医生建议/用户设定/系统建议） |
| status | 单选 | 状态（启用/暂停/已结束） |
| notes | 多行文本 | 备注 |

### 服用时间 (timing) 选项

- 早餐前
- 早餐后
- 午餐前
- 午餐后
- 晚餐前
- 晚餐后
- 睡前

---

## API 调用示例

### 读取 profile
```python
records, _ = bitable_ops.read_records(token, 'profile', limit=1)
```

### 读取最近7天 daily_log
```python
records, _ = bitable_ops.get_recent_records(token, 'daily_log', days=7)
```

### 创建 weekly_plan
```python
fields = {
    'week_start': '2026-03-23',
    'week_end': '2026-03-29',
    'plan_status': '生效中',
    'phase': '减脂期',
    'weekly_goal': '稳定训练节奏，控制饮食波动',
    'focus_areas': ['训练', '饮食', '恢复'],
    ...
}
record_id, _ = bitable_ops.create_record(token, 'weekly_plan', fields)
```

### 查询生效的周计划
```python
# 通过 filter 筛选 plan_status = '生效中'
records, _ = bitable_ops.read_records(token, 'weekly_plan', 
    filterformula="plan_status='生效中'")
```

---

*最后更新：2026-03-20 v2.0.0*
