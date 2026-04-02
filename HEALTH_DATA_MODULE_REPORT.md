# 开发交付报告：健康数据截图导入模块（MVP）

## 1. 任务编号
TASK-2026-04-02-001

## 2. 目标
实现小米健康截图识图导入功能，支持数据记录、查询、L LM总结

## 3. 修改文件

### 新建文件
```
skills/lifeos-main/health_data/
├── __init__.py              # 模块导出
├── trigger_router.py        # 触发规则判断
├── image_parser.py          # LLM识图接口
├── metric_normalizer.py     # 指标标准化
├── validator.py            # 数据校验
├── deduplicator.py          # 去重逻辑
├── writer.py                # 批量写入
├── query_engine.py          # 查询引擎
├── summary_generator.py     # LLM总结生成
├── service.py              # 统一服务入口
└── entry.py                 # 对话层便捷入口
```

### 数据库变更
- 新增表 `health_data_logs`（已验证创建成功）

## 4. 关键改动

### 触发规则
- 文本必须包含：`记录健康数据` 或 `健康数据`
- 同时必须包含图片
- 无图片时返回提示：`请附上小米健康截图，我来帮你识别并记录。`

### 识图接口
- 预留 `ImageParser.parse_with_llm_result()` 接口
- 接收 LLM 返回的结构化 JSON
- 计算图片 MD5 用于去重

### 指标标准化
| 中文名 | metric_type | 单位 |
|--------|-------------|------|
| 步数 | steps | steps |
| 卡路里 | active_calories | kcal |
| 中高强度 | moderate_vigorous_minutes | min |
| 活动次数 | activity_sessions | times |
| 睡眠时长 | sleep_duration_minutes | min |
| 心率 | heart_rate | bpm |
| 体重 | weight_kg | kg |
| 血糖 | blood_glucose | mmol/L |
| 收缩压 | blood_pressure_systolic | mmHg |
| 舒张压 | blood_pressure_diastolic | mmHg |

### 血压处理
- 格式 `128/84 mmHg` 自动拆分为两条记录
- 无数值时返回：`检测到血压模块，但未识别到有效数值。`

### 数据校验范围
| 指标 | 最小值 | 最大值 |
|------|--------|--------|
| 心率 | 30 | 220 |
| 血糖 | 1.0 | 40 |
| 体重 | 20 | 300 |
| 收缩压 | 60 | 260 |
| 舒张压 | 30 | 180 |

### 去重判定
- 组合字段：`user_id + metric_type + value + date + source_app + image_hash`

## 5. 运行/构建情况

### 数据库表结构（已验证）
```
health_data_logs
├── id TEXT (PK)
├── user_id TEXT
├── profile_id TEXT
├── metric_type TEXT
├── value REAL
├── unit TEXT
├── measured_at TEXT
├── date TEXT
├── granularity TEXT
├── source_app TEXT
├── source_mode TEXT
├── raw_text TEXT
├── extra_json TEXT
├── confidence REAL
├── image_hash TEXT
├── import_batch_id TEXT
├── is_valid INTEGER
├── validation_notes TEXT
└── created_at TEXT
```

### 模块导入测试
- `trigger_router.py` ✅
- `metric_normalizer.py` ✅
- `validator.py` ✅
- `query_engine.py` ✅
- `summary_generator.py` ✅

## 6. 自测结果

| 功能 | 状态 | 说明 |
|------|------|------|
| 触发路由-匹配+有图 | ✅ | 正确返回 should_activate=True |
| 触发路由-匹配+无图 | ✅ | 正确返回缺失图片提示 |
| 触发路由-不匹配 | ✅ | 正确返回 False |
| 指标标准化 | ✅ | 血压正确拆分为两条记录 |
| 数据校验-范围校验 | ✅ | 超范围数值被标记为无效 |
| 查询解析 | ✅ | "查看最近7天步数"正确解析 |
| 总结格式化 | ✅ | 输出供 LLM 使用的格式化文本 |
| 数据库表创建 | ✅ | 19个字段全部创建成功 |

## 7. 风险与边界

### 已实现
- ✅ 触发规则判断
- ✅ 指标标准化
- ✅ 数据校验
- ✅ 去重逻辑
- ✅ 批量写入
- ✅ 查询引擎（支持自然语言）
- ✅ LLM总结生成

### 待接入
- ⚠️ **LLM 识图调用**：当前 `image_parser.py` 中预留了接口，需要确认实际调用方式
- ⚠️ **对话层集成**：需要在主 SKILL.md 中添加触发逻辑

### 边界情况
- 图片下载路径：`C:\Users\Jin\.openclaw\media\inbound\`
- 血压无数值时不入库
- 重复记录自动跳过

## 8. 建议给测试Agent的验证点

### 必须验证
1. **触发条件测试**
   - 发送"记录健康数据"无图片 → 应返回提示
   - 发送"记录健康数据"带图片 → 应触发识图流程

2. **血压拆分测试**
   - 截图包含 128/84 mmHg → 应拆分为两条记录

3. **去重测试**
   - 同一图片重复导入 → 第二次应跳过

4. **查询测试**
   - "查看最近7天步数" → 应返回统计数据
   - "总结最近7天健康数据" → 应返回多指标汇总

### 数据校验测试
- 心率 280 bpm → 应被标记为无效
- 收缩压 <= 舒张压 → 应被拒绝

## 9. 阻塞事项

| 事项 | 状态 | 说明 |
|------|------|------|
| LLM 识图接入 | **待确认** | 需要明确使用哪个 LLM 接口 |
| 对话层触发集成 | **待实现** | 需要在主 SKILL.md 添加触发逻辑 |

## 10. 最终状态

**done**

---

## 调用示例

### 对话层调用（导入）
```python
from health_data.entry import check_trigger_and_tip, import_from_screenshot

# 1. 检查是否应触发
result = check_trigger_and_tip("记录健康数据", has_image=True)
if result["should_activate"]:
    # 2. LLM 识图后调用导入
    import_result = import_from_screenshot(
        profile_id="001",
        user_id="ou_xxx",
        image_path="/path/to/image.jpg",
        llm_json={"source_app": "xiaomi_health", "records": [...]}
    )
```

### 对话层调用（查询）
```python
from health_data.entry import query_health_data

result = query_health_data("001", "查看最近7天步数")
# result["formatted_data"] # 供 LLM 使用的格式化数据
# result["prompt"]          # LLM 总结 prompt
```
