/**
 * medicine/reminder.ts
 * 药品提醒逻辑
 */

import { TimeSlot, getCurrentTimeSlot, TIME_SLOTS } from './time_slot';
import { 
  getPlansByChannel, 
  ensureTodayRecords, 
  getPendingRecords,
  markAllTakenInSlot,
  MedicationPlan 
} from './storage';

// 提醒结果
export interface ReminderResult {
  shouldRemind: boolean;
  channelId: string;
  channelType: 'group' | 'direct';
  mentionTarget: string;
  timeSlot: TimeSlot;
  drugs: string[];
  message: string;
}

// 按渠道+时间槽聚合的提醒
export interface AggregatedReminder {
  channelId: string;
  channelType: 'group' | 'direct';
  mentionTarget: string;
  timeSlot: TimeSlot;
  plans: MedicationPlan[];
}

// 按渠道分组
function groupByChannel(plans: MedicationPlan[]): Map<string, MedicationPlan[]> {
  const map = new Map<string, MedicationPlan[]>();
  
  for (const plan of plans) {
    const key = `${plan.channel_id}:${plan.channel_type}`;
    if (!map.has(key)) {
      map.set(key, []);
    }
    map.get(key)!.push(plan);
  }
  
  return map;
}

// 检查并生成提醒
export function checkReminders(): ReminderResult[] {
  const currentSlot = getCurrentTimeSlot();
  
  if (!currentSlot) {
    console.log('[medicine] 当前不在任何时间槽内');
    return [];
  }
  
  const today = new Date().toISOString().split('T')[0];
  
  // 获取所有活跃计划
  const allPlans = getPlansByChannel('*', currentSlot); // 需要修改为遍历所有渠道
  
  // 按渠道获取当前时间槽的计划
  // 注意：getPlansByChannel 第一个参数是 channelId，我们用 '*' 表示全部
  // 但实际上 storage.ts 的实现不支持 '*'，需要改进
  
  // 临时方案：遍历所有渠道
  const results: ReminderResult[] = [];
  
  // 这里需要获取所有活跃计划，然后按渠道+时间槽分组
  // 简化处理：让 storage.ts 提供新方法
  const { getActivePlans } = require('./storage');
  const activePlans = getActivePlans();
  
  // 筛选当前时间槽的计划
  const currentSlotPlans = activePlans.filter((p: MedicationPlan) => p.time_slot === currentSlot);
  
  if (currentSlotPlans.length === 0) {
    console.log(`[medicine] 当前时间槽 ${currentSlot} 没有待提醒的计划`);
    return [];
  }
  
  // 按渠道+时间槽聚合
  const channelMap = new Map<string, MedicationPlan[]>();
  
  for (const plan of currentSlotPlans) {
    const key = `${plan.channel_id}:${plan.channel_type}`;
    if (!channelMap.has(key)) {
      channelMap.set(key, []);
    }
    channelMap.get(key)!.push(plan);
  }
  
  // 生成每个渠道的提醒
  for (const [key, plans] of channelMap) {
    const [channelId, channelType] = key.split(':');
    
    // 确保今天的记录存在
    ensureTodayRecords(plans);
    
    // 检查是否有未完成的记录
    const pendingRecords = getPendingRecords(channelId, currentSlot, today);
    
    if (pendingRecords.length === 0) {
      continue;
    }
    
    // 生成提醒消息
    const drugs = [...new Set(plans.map(p => p.drug_name))];
    const mentionTarget = plans[0].mention_target;
    
    const message = `现在是${currentSlot}服药时间
今天需要服用：
${drugs.map(d => `- ${d}`).join('\n')}`;
    
    results.push({
      shouldRemind: true,
      channelId,
      channelType: channelType as 'group' | 'direct',
      mentionTarget,
      timeSlot: currentSlot,
      drugs,
      message
    });
  }
  
  return results;
}

// 处理"已吃"确认
export function handleTakenConfirmation(
  userId: string,
  userName: string,
  channelId: string,
  channelType: 'group' | 'direct'
): { success: boolean; count: number; message: string } {
  const currentSlot = getCurrentTimeSlot();
  
  if (!currentSlot) {
    return {
      success: false,
      count: 0,
      message: '现在不是服药时间，无需确认'
    };
  }
  
  const today = new Date().toISOString().split('T')[0];
  
  // 查找该用户在该渠道、该时间槽的待服药记录
  const { getAllRecords } = require('./storage');
  const records = getAllRecords();
  
  const pending = records.filter(
    r => r.user_id === userId && 
         r.time_slot === currentSlot && 
         r.date === today && 
         r.status === 'pending'
  );
  
  if (pending.length === 0) {
    return {
      success: false,
      count: 0,
      message: `未找到 ${currentSlot} 的待服药记录`
    };
  }
  
  // 标记所有为已服用
  const count = markAllTakenInSlot(userId, currentSlot, today);
  
  return {
    success: true,
    count,
    message: `已记录，${count} 种药已标记为服用`
  };
}

// 获取用户今日服药情况
export function getUserTodayStatus(userId: string): {
  total: number;
  taken: number;
  pending: number;
  details: Array<{ drug: string; timeSlot: string; status: string }>;
} {
  const today = new Date().toISOString().split('T')[0];
  
  const { getAllRecords } = require('./storage');
  const records = getAllRecords();
  
  const userRecords = records.filter(
    r => r.user_id === userId && r.date === today
  );
  
  const taken = userRecords.filter(r => r.status === 'taken').length;
  const pending = userRecords.filter(r => r.status === 'pending').length;
  
  return {
    total: userRecords.length,
    taken,
    pending,
    details: userRecords.map(r => ({
      drug: r.drug_name,
      timeSlot: r.time_slot,
      status: r.status === 'taken' ? '已服用' : '待服用'
    }))
  };
}
