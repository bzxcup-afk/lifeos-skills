/**
 * medicine/index.ts
 * 药品模块主入口
 * 
 * 集成到 LifeOS 主技能，触发词：
 * - 药、吃药、服药、用药
 * - 具体药物名称（见 parser.ts）
 */

import { MedicineContext, MedicineContextStore } from './context';
import { extractDrugName, getDrugTips, hasDrugMention } from './parser';
import { matchTimeSlot, getTimeSlotList, TimeSlot } from './time_slot';
import { createPlan, getUserPlans } from './storage';
import { handleTakenConfirmation, getUserTodayStatus } from './reminder';

// 消息处理结果
export interface MedicineResult {
  // 是否处理了消息
  handled: boolean;
  
  // 回复消息
  reply?: string;
  
  // 是否需要询问时间槽
  askTimeSlot?: boolean;
  
  // 是否已确认时间槽
  confirmed?: boolean;
  
  // 是否有错误
  error?: string;
}

// 处理用户消息
export function handleMedicineMessage(
  text: string,
  chatId: string,
  senderId: string,
  senderName: string,
  channelType: 'group' | 'direct',
  mentionTarget?: string
): MedicineResult {
  const trimmed = text.trim();
  
  // 获取或创建上下文
  const ctx = MedicineContextStore.fromMessage(
    chatId, senderId, senderName, channelType, mentionTarget
  );
  
  // 处理"已吃"确认
  if (trimmed === '已吃' || trimmed === '吃了' || trimmed === '吃完了') {
    const result = handleTakenConfirmation(senderId, senderName, chatId, channelType);
    
    if (result.success) {
      return {
        handled: true,
        confirmed: true,
        reply: `✅ 已记录\n\n${result.message}`
      };
    } else {
      return {
        handled: true,
        reply: result.message
      };
    }
  }
  
  // 处理"今天吃了什么"等查询
  if (trimmed.includes('今天') && (trimmed.includes('吃了') || trimmed.includes('服药'))) {
    const status = getUserTodayStatus(senderId);
    
    if (status.total === 0) {
      return {
        handled: true,
        reply: '今天还没有服药记录'
      };
    }
    
    const detailText = status.details
      .map(d => `${d.timeSlot}: ${d.drug} (${d.status})`)
      .join('\n');
    
    return {
      handled: true,
      reply: `今日服药情况：
${detailText}

已完成: ${status.taken}/${status.total}`
    };
  }
  
  // 检查是否在等待时间槽输入
  if (ctx.state === 'awaiting_time_slot' && ctx.pending_drug) {
    const timeSlot = matchTimeSlot(trimmed);
    
    if (!timeSlot) {
      return {
        handled: true,
        askTimeSlot: true,
        reply: `无法识别"${trimmed}"，请从以下时间槽选择：\n${getTimeSlotList()}`
      };
    }
    
    // 创建用药计划
    const plan = createPlan({
      user_id: senderId,
      user_name: senderName,
      drug_name: ctx.pending_drug,
      time_slot: timeSlot,
      channel_type: channelType,
      channel_id: chatId,
      mention_target: mentionTarget || senderName
    });
    
    // 清除上下文
    ctx.state = 'idle';
    ctx.pending_drug = undefined;
    MedicineContextStore.clear(chatId, senderId);
    
    // 确认消息
    const atMsg = channelType === 'group' ? `@${senderName} ` : '';
    
    return {
      handled: true,
      confirmed: true,
      reply: `${atMsg}好的，我会在这个群里提醒你，${timeSlot}服用「${plan.drug_name}」`
    };
  }
  
  // 检查药物提及
  if (hasDrugMention(trimmed)) {
    const drugName = extractDrugName(trimmed);
    
    if (!drugName) {
      return {
        handled: true,
        reply: '提到了药物，但无法识别具体药名，请再说一次'
      };
    }
    
    // 获取药物提示
    const tips = getDrugTips(drugName);
    const tipsText = tips.length > 0 
      ? `\n\n💊 ${tips.join('\n')}` 
      : '';
    
    // 检查用户是否已设置过该药
    const existingPlans = getUserPlans(senderId);
    const hasExisting = existingPlans.some(p => p.drug_name === drugName);
    
    if (hasExisting) {
      return {
        handled: true,
        reply: `「${drugName}」已经在你的用药计划中了。\n要查看今日服药情况吗？发送"今天吃了什么"查看。${tipsText}`
      };
    }
    
    // 设置上下文等待时间槽
    ctx.state = 'awaiting_time_slot';
    ctx.pending_drug = drugName;
    MedicineContextStore.set(chatId, senderId, ctx);
    
    return {
      handled: true,
      askTimeSlot: true,
      reply: `「${drugName}」，了解。${tipsText}\n\n请告诉我是哪个时间服用？\n${getTimeSlotList()}`
    };
  }
  
  // 药物模块未处理
  return { handled: false };
}

// 获取模块状态（用于调试）
export function getMedicineStatus(): object {
  return {
    module: 'medicine',
    version: '1.0.0',
    timeSlots: ['起床后', '早餐前', '早餐后', '午餐前', '午餐后', '晚餐前', '晚餐后', '睡前']
  };
}
