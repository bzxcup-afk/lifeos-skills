# -*- coding: utf-8 -*-
"""
问题导向干预入口模块 v1.0

当用户表达"改善某个问题"或"希望为某个问题制定计划"的意愿时：
1. 识别请求属于"问题导向干预请求"
2. 规范化问题名称，映射到对应的问题ID
3. 输出干预原则与计划方式说明
4. 查询/创建知识 md 文件
5. 提取结构化信息返回给后续模块

第一版只实现 sleep-insomnia (失眠/睡眠改善)
"""

import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# ============================================================================
# 路径配置
# ============================================================================

SKILL_DIR = Path(r"C:\Users\Jin\.openclaw\workspace-coding\skills\lifeos-main")
KNOWLEDGE_DIR = SKILL_DIR / "knowledge" / "problems"


# ============================================================================
# 问题规范化映射表
# ============================================================================

PROBLEM_MAPPING: Dict[str, List[str]] = {
    "sleep-insomnia": [
        "失眠", "睡不好", "睡眠问题", "入睡困难",
        "夜里总醒", "容易醒", "早醒", "睡眠浅",
        "改善睡眠", "改善睡眠问题", "睡眠改善"
    ],
    "hypertension": [
        "高血压", "血压高", "控制血压", "血压控制不好"
    ],
    "weight-loss": [
        "减肥", "瘦身", "控制体重", "减重"
    ],
    "brain-enhancement": [
        "脑力", "提升脑力", "改善脑力", "增强脑力",
        "记忆力下降", "注意力不集中", "思维迟缓",
        "认知改善", "提升认知", "大脑疲劳", "用脑过度",
        "脑子不转", "脑子转不动"
    ]
}

# 反向映射：关键词 -> canonical_id
_KEYWORD_TO_CANONICAL: Dict[str, str] = {}
for canonical_id, keywords in PROBLEM_MAPPING.items():
    for kw in keywords:
        _KEYWORD_TO_CANONICAL[kw] = canonical_id

# 规范化 ID -> 显示名称
CANONICAL_DISPLAY_NAMES: Dict[str, str] = {
    "sleep-insomnia": "失眠 / 睡眠改善",
    "hypertension": "高血压",
    "weight-loss": "减肥 / 体重控制",
    "brain-enhancement": "脑力提升 / 认知改善"
}


# ============================================================================
# 触发检测
# ============================================================================

# 问题导向干预的触发意图词
INTERVENTION_INTENT_PATTERNS = [
    # 改善/计划类
    r"改善(.+?)(问题|情况)?$",
    r"帮我制定(.+?)(计划|方案)",
    r"帮我调理(.+?)$",
    r"帮我做一个(.+?)(计划|方案)",
    r"我想改善(.+?)$",
    r"最近(.+?)(很困扰|困扰我|难受|不舒服)，帮我安排",
    r"最近(.+?)想(.+?)调理",
    r"(.+?)问题.*改善",
    r"(.+?)不好.*想调",
    r"(.+?)问题.*想解决",
    r"想调理(.+?)$",
    r"想改善(.+?)$",
]

# 停用词：这些表达不应该触发干预入口
STOP_PATTERNS = [
    r"什么是",
    r"请问",
    r"怎么治疗",
    r"怎么改善",
    r"告诉我",
    r"解释一下",
]


def detect_intervention_intent(user_message: str) -> Optional[Dict[str, Any]]:
    """
    检测用户消息是否属于"问题导向干预请求"

    返回:
        如果匹配，返回 {"matched": True, "problem_topic": "xxx", "original": "xxx"}
        如果不匹配，返回 None
    """
    text = user_message.strip()

    # 先检查是否是纯知识问答（停用词）
    for pattern in STOP_PATTERNS:
        if re.search(pattern, text):
            return None

    # 检查是否匹配干预意图模式
    for pattern in INTERVENTION_INTENT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            # 提取问题主题
            groups = match.groups()
            # 找到非空的捕获组作为问题主题
            problem_topic = None
            for g in groups:
                if g and g.strip():
                    problem_topic = g.strip()
                    break

            if not problem_topic:
                continue

            # 尝试规范化
            canonical_id = normalize_problem(problem_topic)
            if canonical_id:
                return {
                    "matched": True,
                    "problem_topic": problem_topic,
                    "canonical_id": canonical_id,
                    "original_message": text
                }

    return None


def normalize_problem(problem_topic: str) -> Optional[str]:
    """
    将用户描述的问题主题规范化为 canonical_id

    返回:
        canonical_id 或 None（无法识别）
    """
    topic = problem_topic.strip()

    # 清理无意义助词（如"一下"、"稍微"等）
    # "我想改善一下失眠" -> "改善失眠"
    topic = re.sub(r'[稍稍稍微]*(一下|一些|稍微)', '', topic).strip()

    # 精确匹配
    if topic in _KEYWORD_TO_CANONICAL:
        return _KEYWORD_TO_CANONICAL[topic]

    # 模糊匹配：检查是否包含某个已知关键词
    for keyword, canonical_id in _KEYWORD_TO_CANONICAL.items():
        if keyword in topic or topic in keyword:
            return canonical_id

    # 特殊处理：纯"睡眠"相关 -> sleep-insomnia
    if topic in ["睡眠", "睡", "觉"]:
        return "sleep-insomnia"
    
    # 增强模糊匹配：包含"睡"但没完全匹配的情况
    if "睡" in topic:
        return "sleep-insomnia"
    
    # 增强模糊匹配：包含"血压"但没完全匹配的情况
    if "血压" in topic:
        return "hypertension"
    
    # 增强模糊匹配：包含"体重"或"胖"但没完全匹配的情况
    if "体重" in topic or "胖" in topic:
        return "weight-loss"

    return None


# ============================================================================
# 知识文件操作
# ============================================================================

def get_knowledge_file_path(canonical_id: str) -> Path:
    """获取问题知识文件的路径"""
    return KNOWLEDGE_DIR / f"{canonical_id}.md"


def read_knowledge_file(canonical_id: str) -> Optional[str]:
    """
    读取问题知识文件

    返回:
        文件内容或 None
    """
    file_path = get_knowledge_file_path(canonical_id)
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return None


def create_minimal_knowledge_file(canonical_id: str, display_name: str) -> str:
    """
    为指定问题创建最小版知识文件

    返回:
        创建的文件内容
    """
    file_path = get_knowledge_file_path(canonical_id)

    # 根据 canonical_id 生成最小版内容
    if canonical_id == "sleep-insomnia":
        content = _generate_sleep_insomnia_template(display_name)
    elif canonical_id == "hypertension":
        content = _generate_hypertension_template(display_name)
    elif canonical_id == "weight-loss":
        content = _generate_weight_loss_template(display_name)
    else:
        content = _generate_generic_template(canonical_id, display_name)

    file_path.write_text(content, encoding="utf-8")
    return content


def _generate_sleep_insomnia_template(display_name: str) -> str:
    return f"""# {display_name}问题干预知识

## 1. 问题概述
- 常见表现：入睡困难、夜间易醒、早醒、睡眠浅、白天疲劳
- 干预目标：不是一次性完全解决，而是逐步改善节律、减少刺激因素、提高可执行度

## 2. 干预原则
- 先稳定节律，再逐步增加其他措施
- 优先低负担、易执行的调整
- 每周只抓少量关键事项
- 不假设用户依从度高
- 不完全依赖用户口头反馈，要结合记录
- 对老人用户温和引导，不强硬纠正

## 3. 可干预维度
- 作息与起床时间
- 昼夜节律与晨间光照
- 白天活动与午睡
- 饮食刺激物（咖啡因、酒精）
- 睡前行为（刷手机、剧烈活动）
- 药物使用情况
- 情绪压力因素

## 4. 候选措施
- 固定起床时间（即使没睡好也按时起）
- 早晨接触自然光 15-30 分钟
- 限制午睡不超过 30 分钟
- 下午减少咖啡因摄入
- 睡前 1 小时停止刷手机
- 建立睡前放松流程（温水澡、拉伸、阅读）
- 记录夜间醒来次数
- 记录助眠药使用情况

## 5. 生成计划前优先补齐的信息
- 一般几点睡、几点起
- 每天大概睡几个小时
- 主要问题是入睡难、易醒还是早醒
- 是否正在服用助眠药
- 白天是否明显困倦
- 是否愿意接收提醒

## 6. 风险与边界
- 长期严重失眠需进一步评估
- 疑似呼吸暂停、明显情绪问题、明显药物依赖需要谨慎处理
- 药物相关默认只做记录、提醒、风险提示，不擅自给减药方案
"""


def _generate_hypertension_template(display_name: str) -> str:
    return f"""# {display_name}问题干预知识

## 1. 问题概述
- 常见表现：收缩压 ≥ 140mmHg 或舒张压 ≥ 90mmHg、头晕、头痛
- 干预目标：生活方式干预辅助控压，重点监测和规律用药

## 2. 干预原则
- 以规律监测为基础，建立血压记录习惯
- 优先低负担调整（限盐、运动、减重）
- 药物干预需遵医嘱，不擅自停药或换药
- 不假设用户依从度高
- 对老人用户温和引导，关注体位性低血压风险

## 3. 可干预维度
- 钠盐摄入量
- 体重控制
- 规律运动
- 烟酒摄入
- 药物依从性
- 睡眠与压力
- 寒冷保暖

## 4. 候选措施
- 记录每日血压（早、晚各一次）
- 减少腌制食品、加工食品
- 每周至少 150 分钟中等强度有氧运动
- 记录用药情况（是否规律服用）
- 监测体重变化
- 保持大便通畅

## 5. 生成计划前优先补齐的信息
- 目前血压一般是多少（高/正常/偏低）
- 是否正在服用降压药
- 每天摄盐量大概多少
- 运动习惯如何
- 体重是否超重
- 是否有其他慢性病（糖尿病、肾病等）

## 6. 风险与边界
- 血压 > 180/110 mmHg 需立即就医
- 血压波动大、出现胸闷头痛需警惕
- 药物调整必须遵医嘱，系统不擅自给出减药方案
- 生活方式干预不能替代药物治疗
"""


def _generate_weight_loss_template(display_name: str) -> str:
    return f"""# {display_name}问题干预知识

## 1. 问题概述
- 常见表现：BMI ≥ 24、体脂率偏高、乏力
- 干预目标：科学减重、改善代谢、提高体能

## 2. 干预原则
- 以饮食控制为主，运动干预为辅
- 减重目标：每周 0.5-1kg 为宜，不追求快速
- 优先建立记录习惯（饮食记录、体重记录）
- 不推荐极端饮食
- 对老人用户关注肌肉流失风险

## 3. 可干预维度
- 热量摄入（饮食结构与量）
- 运动消耗（有氧 + 力量）
- 作息规律
- 进食时间（间歇性禁食可能性）
- 心理因素（情绪性进食）

## 4. 候选措施
- 记录每日饮食（可用拍照或文字）
- 控制精制碳水化合物
- 增加蛋白质摄入
- 每周 3-5 次有氧运动，每次 30-60 分钟
- 每周 2-3 次力量训练
- 记录体重变化（每周固定时间）
- 保持规律作息

## 5. 生成计划前优先补齐的信息
- 目前体重、身高（计算 BMI）
- 目前的饮食习惯（大概吃什么）
- 运动习惯如何
- 减重动机和目标是多少
- 是否有运动损伤或关节问题
- 时间精力是否允许规律运动

## 6. 风险与边界
- BMI ≥ 30 或有代谢综合征需专业指导
- 极度限制饮食可能导致营养不良
- 运动计划需考虑关节健康
- 快速减重（> 1kg/周）可能有健康风险
"""


def _generate_generic_template(canonical_id: str, display_name: str) -> str:
    return f"""# {display_name}问题干预知识

## 1. 问题概述
- 常见表现：
- 干预目标：

## 2. 干预原则
- 先稳定基础状态
- 优先低负担调整
- 每周只抓少量关键事项
- 不假设用户依从度高
- 对老人用户温和引导

## 3. 可干预维度
-

## 4. 候选措施
-

## 5. 生成计划前优先补齐的信息
-

## 6. 风险与边界
-
"""


# ============================================================================
# ============================================================================
# 维度解释（仅用于用户回复，不写入 md 文件）
# ============================================================================

DIMENSION_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "sleep-insomnia": {
        "作息与起床时间": "作息规律是睡眠的基石——每天固定时间睡觉和起床，能帮助身体形成稳定的生物钟，让入睡和醒来的过程更自然。",
        "昼夜节律与晨间光照": "人的身体靠昼夜节律调节睡眠——早晨接触自然光（阳光）能重置生物钟，告诉身体'该清醒了'，到晚上自然就会产生困意。",
        "白天活动与午睡": "白天的活动量和午睡都会影响夜间睡眠——适量运动能提升睡眠质量，但午睡超过30分钟容易导致晚上难以入睡。",
        "饮食刺激物（咖啡因、酒精）": "咖啡因半衰期长，下午喝咖啡可能到睡前还有残留；酒精虽然让人容易入睡，但会严重降低睡眠质量，导致夜间频繁醒来。",
        "睡前行为（刷手机、剧烈活动）": "手机屏幕发出的蓝光会抑制褪黑素分泌，让大脑以为还是白天；剧烈运动则让身体处于兴奋状态，不利入睡。",
        "药物使用情况": "有些药物可能影响睡眠，同时助眠药物的效果和依赖性也需要关注，记录用药情况能帮助判断失眠原因。",
        "情绪压力因素": "焦虑和压力会让大脑在睡前处于'待机'状态，常见的'想太多睡不着'就是这个原因，需要专门的方法来处理。",
    },
    "hypertension": {
        "钠盐摄入量": "高盐饮食直接升高血压——每天盐摄入量控制在5克以下，血压可能会有明显下降。",
        "体重控制": "每减重10公斤，收缩压可能下降5-20mmHg；体重下来了，血管负担自然减轻。",
        "规律运动": "每周150分钟中等强度有氧运动（如快走、游泳），能让血管更有弹性，血压自然下降。",
        "烟酒摄入": "吸烟损伤血管内皮，喝酒会让血压波动；戒烟限酒对血压控制非常重要。",
        "药物依从性": "降压药需要规律服用——漏服或擅自停药会导致血压反弹，危害更大。",
        "睡眠与压力": "睡眠差和压力大都会让交感神经兴奋，升高血压；管理好情绪本身就在降压。",
        "寒冷保暖": "低温会让血管收缩，血压升高——保暖不只是防感冒，对高血压患者也很重要。",
    },
    "weight-loss": {
        "热量摄入（饮食结构与量）": "减重的核心是热量缺口——吃进去的比消耗的少，体重才会下降；不是某一种食物让你胖，而是整体热量。",
        "运动消耗（有氧 + 力量）": "有氧运动直接燃烧脂肪，力量训练能增加肌肉、提高基础代谢，让你躺着也能多消耗热量。",
        "作息规律": "睡眠不足会升高饥饿素、降低瘦素，让人更容易饿、更想吃高热量食物——熬夜真的会胖。",
        "进食时间（间歇性禁食可能性）": "进食时间窗口也会影响代谢——晚间进食过多会让身体在休息时还在处理热量。",
        "心理因素（情绪性进食）": "压力大、情绪低落时很多人会靠吃来安慰自己，这叫情绪性进食，需要先认识它才能控制。",
    },
    "brain-enhancement": {
        "睡眠质量与时长": "睡眠是大脑最好的修复剂——每晚7-9小时睡眠能清除脑内代谢废物，海马体在睡眠中巩固记忆。睡不好，脑子就转不动。",
        "有氧运动与身体活动": "有氧运动促进大脑血流，带来更多氧气和营养物质；运动后2小时内认知表现明显提升。",
        "饮食与营养摄入": "大脑虽然只占体重2%，却消耗20%能量——Omega-3、葡萄糖、维生素都影响认知表现，饿着肚子脑子会变迟钝。",
        "认知刺激与学习新技能": "大脑用进废退——持续学习新技能、接触新信息能促进神经可塑性，让大脑保持活跃。",
        "压力管理与情绪状态": "慢性压力会释放皮质醇，损害海马体神经元；焦虑和抑郁会明显影响注意力和决策能力。",
        "社交互动": "社交需要调动大脑多个区域——面对面交流比刷社交媒体更能刺激认知。",
        "工作/学习节奏与定时休息": "大脑持续工作会积累认知疲劳——番茄工作法（25分钟休息5分钟）能维持最佳认知状态。",
        "屏幕时间与信息摄入量": "大量碎片化信息让大脑处于浅层加工——信息过载会降低专注力和深度思考能力。",
    },
}


# ============================================================================
# 知识文件解析
# ============================================================================

def parse_knowledge_content(content: str) -> Dict[str, Any]:
    """
    解析知识文件内容，提取结构化信息

    返回:
        {
            "intervention_principles": [...],
            "intervention_dimensions": [...],
            "candidate_actions": [...],
            "required_info_to_ask": [...],
            "risk_boundaries": [...]
        }
    """
    result = {
        "intervention_principles": [],
        "intervention_dimensions": [],
        "candidate_actions": [],
        "required_info_to_ask": [],
        "risk_boundaries": []
    }

    current_section = None
    lines = content.split("\n")

    for line in lines:
        line = line.strip()

        # 检测章节
        if line.startswith("## 2. 干预原则"):
            current_section = "intervention_principles"
            continue
        elif line.startswith("## 3. 可干预维度"):
            current_section = "intervention_dimensions"
            continue
        elif line.startswith("## 4. 候选措施"):
            current_section = "candidate_actions"
            continue
        elif line.startswith("## 5. 生成计划前优先补齐"):
            current_section = "required_info_to_ask"
            continue
        elif line.startswith("## 6. 风险与边界"):
            current_section = "risk_boundaries"
            continue
        elif line.startswith("#"):
            current_section = None
            continue

        # 解析列表项
        if current_section and line.startswith("-"):
            item = line[1:].strip()
            if item:
                result[current_section].append(item)

    return result


# ============================================================================
# 干预原则输出模板
# ============================================================================

# 默认闭环时间建议（按问题类型）
DEFAULT_CLOSED_LOOP_SUGGESTIONS: Dict[str, Dict[str, str]] = {
    "sleep-insomnia": {
        "default_time": "08:00",
        "default_action": "测一下睡眠情况",
        "feedback_day": "下周三",
        "default_message": "每天早上8点左右提醒你简单记一下昨晚睡得怎么样"
    },
    "hypertension": {
        "default_time": "08:00",
        "default_action": "测一下血压",
        "feedback_day": "下周三",
        "default_message": "每天早上8点左右提醒你测一下血压"
    },
    "weight-loss": {
        "default_time": "08:00",
        "default_action": "称一下体重",
        "feedback_day": "下周三",
        "default_message": "每天早上8点左右提醒你称一下体重"
    },
    "brain-enhancement": {
        "default_time": "08:00",
        "default_action": "记录一下前一天的状态",
        "feedback_day": "下周三",
        "default_message": "每天早上8点左右提醒你简单回顾一下前一天的状态"
    }
}


def build_first_round_output(
    display_name: str,
    principles: List[str],
    dimensions: List[str],
    user_topic: str,
    canonical_id: str = ""
) -> str:
    """
    构建第一轮输出：干预原则与计划方式说明

    **重要修改（2026-04-09）：**
    - 用户表达改善意愿后，不再只是输出知识就结束
    - 必须直接推进闭环，给出具体的提醒建议
    - 不给二元判断题，直接确认闭环

    参数:
        display_name: 问题显示名称
        principles: 干预原则列表
        dimensions: 可干预维度列表
        user_topic: 用户原始描述的问题主题
        canonical_id: 用于查找维度解释

    返回:
        格式化输出文本（含闭环建议）
    """
    # 获取该问题的维度解释（仅用户端展示，不写 md）
    explanations = DIMENSION_EXPLANATIONS.get(canonical_id, {})

    # 取核心维度（前 4 个）
    key_dimensions = dimensions[:4] if len(dimensions) > 4 else dimensions

    # 格式化维度描述 + 解释
    dimensions_parts = []
    for dim in key_dimensions:
        if dim in explanations:
            dimensions_parts.append(f"**{dim}**：{explanations[dim]}")
        else:
            dimensions_parts.append(dim)

    # 如果有未展示的维度，加一句概括
    remaining = dimensions[4:] if len(dimensions) > 4 else []
    remaining_text = "" if not remaining else f"此外还涉及{len(remaining)}个方面，"

    # 获取该问题的闭环建议
    loop_config = DEFAULT_CLOSED_LOOP_SUGGESTIONS.get(canonical_id, DEFAULT_CLOSED_LOOP_SUGGESTIONS["sleep-insomnia"])
    default_message = loop_config["default_message"]
    feedback_day = loop_config["feedback_day"]

    # 核心修改：直接推进闭环，不给判断题
    # 用户没说不要 = 默认要
    output = f"""针对"{user_topic}"这个问题，一般会从以下几个方面来改善：

{"\n\n".join(dimensions_parts)}

{remaining_text}我会依据这些原则，结合你的资料和实际习惯，帮你逐步整理出一个负担不要太重、可执行的干预思路。

{default_message}，{feedback_day}我再来问你效果怎么样，看要不要调整。

（本次为入口阶段，先按这个节奏试一周，待信息补齐后再细化计划。）"""

    return output


# ============================================================================
# 入口函数
# ============================================================================

def handle_intervention_intake(user_message: str, force_create: bool = False) -> Dict[str, Any]:
    """
    处理问题导向干预入口的主函数

    参数:
        user_message: 用户消息文本
        force_create: 是否强制创建知识文件（即使不存在也创建最小版）

    返回:
        {
            "success": bool,
            "should_respond": bool,
            "reply_message": str,
            "structured_data": {...}  # 供后续模块使用
        }
    """
    # 1. 检测是否是干预意图
    intent = detect_intervention_intent(user_message)

    if not intent:
        return {
            "success": False,
            "should_respond": False,
            "reply_message": "",
            "structured_data": None
        }

    canonical_id = intent["canonical_id"]
    display_name = CANONICAL_DISPLAY_NAMES.get(canonical_id, intent["problem_topic"])
    user_topic = intent["problem_topic"]

    # 清理无意义助词（如"一下"），让显示更自然
    user_topic_clean = re.sub(r'[稍稍稍微]*(一下|一些|稍微)', '', user_topic).strip()
    if user_topic_clean:
        user_topic = user_topic_clean

    # 2. 尝试读取知识文件
    knowledge_content = read_knowledge_file(canonical_id)
    file_existed = knowledge_content is not None

    # 3. 如果文件不存在，创建最小版
    if not file_existed or force_create:
        knowledge_content = create_minimal_knowledge_file(canonical_id, display_name)
        file_existed = False  # 标记为新创建

    # 4. 解析知识文件
    parsed = parse_knowledge_content(knowledge_content)

    # 5. 构建第一轮输出（传入 canonical_id 以获取维度解释）
    first_round_output = build_first_round_output(
        display_name=display_name,
        principles=parsed["intervention_principles"],
        dimensions=parsed["intervention_dimensions"],
        user_topic=user_topic,
        canonical_id=canonical_id
    )

    # 6. 组装结构化数据（供后续模块使用）
    structured_data = {
        "canonical_id": canonical_id,
        "display_name": display_name,
        "knowledge_file": str(get_knowledge_file_path(canonical_id)),
        "file_was_newly_created": not file_existed,
        "intervention_principles": parsed["intervention_principles"],
        "intervention_dimensions": parsed["intervention_dimensions"],
        "candidate_actions": parsed["candidate_actions"],
        "required_info_to_ask": parsed["required_info_to_ask"],
        "risk_boundaries": parsed["risk_boundaries"]
    }

    # 7. 添加文件状态说明
    file_status = "已为您创建了这个问题的基础知识模板" if not file_existed else "已找到这个问题对应的知识文件"

    reply_message = f"""{file_status}。

{first_round_output}

---
📋 知识文件信息：
- 文件：knowledge/problems/{canonical_id}.md
- 可干预维度：{len(parsed['intervention_dimensions'])} 个
- 候选措施：{len(parsed['candidate_actions'])} 项
"""

    return {
        "success": True,
        "should_respond": True,
        "reply_message": reply_message.strip(),
        "structured_data": structured_data
    }


# ============================================================================
# 命令行入口（调试用）
# ============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("问题导向干预入口 - 调试模式")
    print("=" * 60)
    print()

    # 测试用例
    test_messages = [
        "改善睡眠问题",
        "帮我制定一个改善失眠的计划",
        "最近总是睡不好，想调理一下",
        "最近总是睡不好，困扰我，帮我安排",
        "我想改善高血压",
        "帮我做一个减肥的计划",
        # 负例
        "什么是失眠？",
        "请问高血压怎么治疗？",
    ]

    print("测试用例：")
    print("-" * 40)
    for msg in test_messages:
        result = handle_intervention_intake(msg)
        print(f"\n输入：{msg}")
        if result["success"]:
            print(f"[PASS] canonical_id: {result['structured_data']['canonical_id']}")
            print(f"   display_name: {result['structured_data']['display_name']}")
            print(f"   file_created: {result['structured_data']['file_was_newly_created']}")
            print(f"   reply_snippet: {result['reply_message'][:100]}...")
        else:
            print(f"[FAIL] Not matched as intervention intent")
    print()
    print("=" * 60)
