/**
 * medicine/time_slot.ts
 * 时间槽定义与匹配
 */

// 固定时间槽及其描述
export const TIME_SLOTS = [
  '起床后',
  '早餐前',
  '早餐后',
  '午餐前',
  '午餐后',
  '晚餐前',
  '晚餐后',
  '睡前'
] as const;

export type TimeSlot = typeof TIME_SLOTS[number];

// 时间槽到小时分钟的映射
// 触发时间：起床后7:00 / 早餐前7:30 / 早餐后8:00 / 午餐前11:00
//           午餐后12:00 / 晚餐前17:00 / 晚餐后18:00 / 睡前20:30
const TIME_SLOT_HOURS: Record<TimeSlot, { start: number; end: number }> = {
  '起床后': { start: 7, end: 8 },      // 7:00-8:00
  '早餐前': { start: 7, end: 8 },      // 7:30触发，窗口7:00-8:00
  '早餐后': { start: 8, end: 9 },      // 8:00-9:00
  '午餐前': { start: 11, end: 12 },    // 11:00-12:00
  '午餐后': { start: 12, end: 14 },    // 12:00-14:00
  '晚餐前': { start: 17, end: 18 },    // 17:00-18:00
  '晚餐后': { start: 18, end: 20 },    // 18:00-20:00
  '睡前': { start: 20, end: 21 }       // 20:30触发，窗口20:00-21:00
};

// 检查当前时间是否属于某个时间槽
export function getCurrentTimeSlot(): TimeSlot | null {
  const now = new Date();
  const hour = now.getHours();
  const minute = now.getMinutes();
  
  for (const [slot, { start, end }] of Object.entries(TIME_SLOT_HOURS)) {
    if (hour >= start && hour < end) {
      return slot as TimeSlot;
    }
  }
  
  return null;
}

// 获取时间槽对应的描述时间
export function getTimeSlotDisplay(slot: TimeSlot): string {
  const { start, end } = TIME_SLOT_HOURS[slot];
  return `${start}:00-${end}:00`;
}

// 匹配用户输入的时间槽
export function matchTimeSlot(input: string): TimeSlot | null {
  const trimmed = input.trim();
  
  // 精确匹配
  if (TIME_SLOTS.includes(trimmed as TimeSlot)) {
    return trimmed as TimeSlot;
  }
  
  // 模糊匹配
  const lower = trimmed.toLowerCase();
  
  const aliasMap: Record<string, TimeSlot> = {
    '早上': '起床后',
    '早晨': '起床后',
    '起来': '起床后',
    '早饭前': '早餐前',
    '早饭': '早餐前',
    '早餐': '早餐前',
    '早饭后': '早餐后',
    '午饭前': '午餐前',
    '午饭': '午餐前',
    '午餐': '午餐前',
    '午饭后': '午餐后',
    '晚饭前': '晚餐前',
    '晚饭': '晚餐前',
    '晚餐': '晚餐前',
    '晚饭后': '晚餐后',
    '晚上': '睡前',
    '夜晚': '睡前',
    '休息前': '睡前',
    '睡觉前': '睡前',
    '睡前': '睡前',
    '上床': '睡前'
  };
  
  for (const [alias, slot] of Object.entries(aliasMap)) {
    if (lower.includes(alias)) {
      return slot;
    }
  }
  
  return null;
}

// 获取时间槽列表（用于询问用户）
export function getTimeSlotList(): string {
  return TIME_SLOTS.map((slot, i) => `${i + 1}. ${slot}`).join('\n');
}
