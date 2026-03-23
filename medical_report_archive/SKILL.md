# 医疗报告归档助手 V1.1

## 双阶段架构

```
用户发送图片
    ↓
【阶段A】agent会话（volc-coding视觉分析）
    输出结构化JSON
    ↓
【阶段B】归档workflow（代码写入飞书）
    写入4张表 → 展示确认 → 用户回复"归档"
```

## 触发条件

当用户发送以下内容时激活：
- 发送医疗报告图片
- 发送"归档医疗报告"
- 发送"上传体检报告"

## 阶段A：视觉识别

在支持视觉的agent会话中使用提示词模板分析图片，输出结构化JSON。

**提示词模板**：见 `stage_a_prompt.md`

**输出JSON Schema**：
```json
{
  "report_meta": {
    "report_type": "string",
    "hospital": "string",
    "exam_date": "YYYY-MM-DD",
    "patient_name": "string",
    "gender": "男|女",
    "age": number
  },
  "summary": "string",
  "items": [...],
  "confidence_check": {
    "extraction_confidence": number,
    "identity_match_score": number,
    "consistency_score": number,
    "total_archive_confidence": number,
    "hard_conflict": boolean,
    "conflict_notes": "string",
    "archive_recommendation": "string"
  },
  "raw_extract": {
    "ocr_text": "string"
  }
}
```

## 阶段B：归档执行

### ⚠️ 强制要求：必须执行完整归档策略

**所有医疗报告评估必须执行以下流程，不得跳过：**

1. **必须执行归档策略分析** - 根据置信度和硬冲突判断处理方式
2. **必须分析硬冲突** - 三层校验：身份匹配、指标冲突、时间冲突
3. **必须输出置信度评分** - extraction + identity + consistency
4. **必须执行身份对比** - B阶段必须读取用户档案，与A阶段提取的报告信息进行对比

**禁止行为：**
- ❌ 跳过归档策略直接给出建议
- ❌ 不分析硬冲突就归档
- ❌ 忽略置信度评分
- ❌ A阶段直接给出hard_conflict判断
- ❌ B阶段不做身份对比就归档

### 阶段A与阶段B的职责划分

**阶段A职责（视觉识别）：**
1. 提取报告中的基础信息（年龄、性别、姓名等）
2. 提取所有检验指标
3. 评估提取置信度（extraction_confidence）
4. **不负责判断 hard_conflict，该字段在阶段A输出中应设为 null 或忽略**

**阶段B职责（归档执行）：**
1. 接收阶段A的解析结果
2. **读取对应用户的 profile 档案**
3. **对比报告信息与档案信息：**
   - 年龄差距是否过大（如报告84岁 vs 档案35岁）
   - 性别是否一致
   - 姓名是否匹配（如可识别）
4. **根据对比结果设置 hard_conflict：**
   - 存在明显身份不匹配 → hard_conflict = true
   - 身份匹配或无法确认 → hard_conflict = false
5. 计算 identity_match_score 和 consistency_score
6. 根据硬冲突和总置信度选择归档策略 (A/B/C/D/E)

**阶段B必须执行的强制检查清单：**
- [ ] 已读取用户档案（profile表）
- [ ] 已对比报告年龄 vs 档案年龄
- [ ] 已对比报告性别 vs 档案性别
- [ ] 已对比报告姓名 vs 档案姓名（如有）
- [ ] 已根据对比结果设置 hard_conflict
- [ ] 已计算 identity_match_score
- [ ] 已选择正确的归档策略

**禁止行为：**
- ❌ 未读取用户档案就进行归档
- ❌ 未做身份对比就设置 hard_conflict = false
- ❌ 发现身份不匹配仍继续归档（应走E策略）

### 身份对比触发硬冲突的示例

| 档案信息 | 报告信息 | 判定 |
|---------|---------|------|
| 金，男，35岁 | 84岁，男性 | **硬冲突** - 年龄差距过大 |
| 芳芳，女，40岁 | 男性 | **硬冲突** - 性别不匹配 |
| 老姥姥，女，80岁 | 84岁，女性 | 无冲突 - 年龄接近，性别一致 |

> **注意**：硬冲突仅由**身份不匹配**触发，不是由**指标异常**触发。即使指标严重异常，只要身份匹配，也不应设置 hard_conflict。

---

**写表逻辑**：见 `stage_b_logic.py`

**目标表**：
| 表名 | Table ID |
|------|----------|
| raw_reports | tblnzCb5t90idIBy |
| reports_master | tblb0LB9FmoBSyQc |
| indicators_detail | tbl37m0LN99UvCi6 |
| health_master | tblqXVFHcREZWU6u |

## 置信度校验

三层校验：
1. **extraction_confidence**（识别置信度）：OCR质量、报告类型识别、指标提取完整度
2. **identity_match_score**（身份匹配分）：姓名、性别、出生日期匹配
3. **consistency_score**（档案一致性分）：与历史档案冲突检测

**总置信度** = 识别置信度×0.4 + 身份匹配分×0.3 + 档案一致性分×0.3

**归档建议规则**：
| 情况 | 建议 |
|------|------|
| 有硬冲突 | 硬冲突拦截 |
| 无硬冲突，总分<40 | 暂不自动归档 |
| 无硬冲突，总分<60 | 建议人工确认 |
| 无硬冲突，总分≥60 | 可归档 |

## 高频同步指标

以下指标会同步到health_master：
- 血压（收缩压/舒张压）
- 空腹血糖、HbA1c
- LDL-C、TC、TG
- UA、ALT、AST
- Cr、BUN

## 用户交互

### 归档确认模板
```
已识别到一份医疗报告：

📋 报告信息
• 报告类型：xxx
• 检查日期：xxxx-xx-xx
• 医院：xxx

🔍 关键异常项：
• xxx

📊 归档匹配结果：
• 识别置信度：高/中/低
• 身份匹配分：xx
• 档案一致性分：xx
• 总归档置信度：xx
• 是否存在硬冲突：是/否
• 归档建议：可归档/建议人工确认/暂不自动归档/硬冲突拦截

请回复：
• 归档 - 确认归档
• 放弃 - 放弃
```

### 归档成功模板
```
✅ 已归档成功

报告已存入：
• 原始报告表
• 报告主表
• 指标明细表（X项指标）
• 健康主档案（已同步X项关键指标）

归档时间：xxxx-xx-xx xx:xx
报告ID：RPT-xxxxxxxx-XXXXXXXX
```

## 文件结构

```
medical_report_archive/
├── SKILL.md            # 本文件
├── stage_a_prompt.md   # 阶段A提示词模板
├── stage_b_logic.py    # 阶段B写表逻辑
└── config.json        # 表配置
```
