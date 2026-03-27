/**
 * medicine/storage.ts
 * 药品模块数据存储（JSON文件）
 */

import * as fs from 'fs';
import * as path from 'path';

export interface MedicationPlan {
  id: string;
  user_id: string;
  user_name: string;
  drug_name: string;
  time_slot: string;
  channel_type: 'group' | 'direct';
  channel_id: string;
  mention_target: string;
  created_at: string;
  active: boolean;
}

export interface MedicationRecord {
  id: string;
  plan_id: string;
  user_id: string;
  drug_name: string;
  date: string;
  time_slot: string;
  status: 'pending' | 'taken' | 'missed';
  taken_at?: string;
}

// 存储目录
const DATA_DIR = path.join(__dirname);
const PLANS_FILE = path.join(DATA_DIR, 'medicine_plans.json');
const RECORDS_FILE = path.join(DATA_DIR, 'medicine_records.json');

// 读取JSON文件
function readJson<T>(filePath: string, defaultValue: T): T {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(content);
    }
  } catch (e) {
    console.error(`[medicine] 读取文件失败 ${filePath}:`, e);
  }
  return defaultValue;
}

// 写入JSON文件
function writeJson<T>(filePath: string, data: T): void {
  try {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
  } catch (e) {
    console.error(`[medicine] 写入文件失败 ${filePath}:`, e);
  }
}

// 生成UUID
function genId(): string {
  return 'med_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 9);
}

// ==================== 用药计划 ====================

export function getAllPlans(): MedicationPlan[] {
  return readJson<MedicationPlan[]>(PLANS_FILE, []);
}

export function getActivePlans(): MedicationPlan[] {
  return getAllPlans().filter(p => p.active);
}

export function getUserPlans(userId: string): MedicationPlan[] {
  return getActivePlans().filter(p => p.user_id === userId);
}

export function getPlansByChannel(channelId: string, timeSlot: string): MedicationPlan[] {
  return getActivePlans().filter(
    p => p.channel_id === channelId && p.time_slot === timeSlot
  );
}

export function createPlan(data: Omit<MedicationPlan, 'id' | 'created_at' | 'active'>): MedicationPlan {
  const plans = getAllPlans();
  
  // 检查是否已存在相同的计划
  const existing = plans.find(
    p => p.user_id === data.user_id && 
         p.drug_name === data.drug_name && 
         p.time_slot === data.time_slot &&
         p.active
  );
  
  if (existing) {
    console.log(`[medicine] 计划已存在: ${existing.id}`);
    return existing;
  }
  
  const plan: MedicationPlan = {
    ...data,
    id: genId(),
    created_at: new Date().toISOString(),
    active: true
  };
  
  plans.push(plan);
  writeJson(PLANS_FILE, plans);
  
  console.log(`[medicine] 创建计划: ${plan.id} - ${plan.drug_name} @ ${plan.time_slot}`);
  
  // 同步到 Bitable 表
  syncToBitable(plan).catch(err => {
    console.error('[medicine] 同步到 Bitable 失败:', err);
  });
  
  return plan;
}

// 同步药品计划到 Bitable
async function syncToBitable(plan: MedicationPlan): Promise<void> {
  try {
    // 判断是药品还是补剂
    const supplementKeywords = ["鱼油", "维生素", "VK", "VC", "VD", "VA", "VB", "镁", "锌", "钙", 
      "辅酶", "Q10", "益生菌", "益生元", "胶原蛋白", "叶黄素", "氨糖",
      "AKG", "alpha", "酮戊二酸", "NMN", "NAD", "硫辛酸", "肌酸", "BCAA"];
    
    const isSupplement = supplementKeywords.some(kw => 
      plan.drug_name.toLowerCase().includes(kw.toLowerCase())
    );
    
    // 时间槽映射
    const timeSlotMapping: Record<string, string> = {
      "起床后": "早餐前",
      "早餐前": "早餐前",
      "早餐后": "早餐后",
      "午餐前": "午餐前",
      "午餐后": "午餐后",
      "晚餐前": "晚餐前",
      "晚餐后": "晚餐后",
      "睡前": "睡前"
    };
    const timing = timeSlotMapping[plan.time_slot] || plan.time_slot;
    
    // 提取剂量
    const dosageMatch = plan.drug_name.match(/(\d+\s*(mg|g|μg|mcg|IU|ml|毫升|片|粒|颗|支|瓶))/i);
    const dosage = dosageMatch ? dosageMatch[1] : "";
    
    // 构建请求体
    const fields = {
      "item_id": plan.id,
      "profile_id": "001", // 默认用户ID
      "name": plan.drug_name,
      "item_type": isSupplement ? "补剂" : "药品",
      "dosage": dosage,
      "frequency": "每天",
      "timing": [timing], // 多选字段
      "with_food": isSupplement ? "随餐" : "均可",
      "purpose": `由用户设定，服用时间：${plan.time_slot}`,
      "source_type": "用户设定",
      "status": plan.active ? "启用" : "暂停",
      "notes": `来源：${plan.channel_type} 渠道`
    };
    
    // 调用 Python 脚本写入 Bitable
    const { spawn } = require('child_process');
    const scriptPath = path.join(__dirname, '..', 'scripts', 'bitable_ops.py');
    
    const pythonProcess = spawn('python', [
      scriptPath,
      'create',
      'medication_supplement_list',
      JSON.stringify(fields)
    ], {
      cwd: path.join(__dirname, '..'),
      env: {
        ...process.env,
        PYTHONIOENCODING: 'utf-8'
      }
    });
    
    let stdout = '';
    let stderr = '';
    
    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error('[medicine] Bitable 同步失败:', stderr);
      } else {
        console.log(`[medicine] 已同步到 Bitable: ${plan.drug_name}`);
      }
    });
    
  } catch (error) {
    console.error('[medicine] 同步到 Bitable 失败:', error);
  }
}

export function deactivatePlan(planId: string): boolean {
  const plans = getAllPlans();
  const idx = plans.findIndex(p => p.id === planId);
  
  if (idx === -1) return false;
  
  plans[idx].active = false;
  writeJson(PLANS_FILE, plans);
  return true;
}

// ==================== 服药记录 ====================

export function getAllRecords(): MedicationRecord[] {
  return readJson<MedicationRecord[]>(RECORDS_FILE, []);
}

export function getTodayRecords(date?: string): MedicationRecord[] {
  const d = date || new Date().toISOString().split('T')[0];
  return getAllRecords().filter(r => r.date === d);
}

export function getPendingRecords(channelId: string, timeSlot: string, date?: string): MedicationRecord[] {
  const d = date || new Date().toISOString().split('T')[0];
  return getAllRecords().filter(
    r => r.date === d && r.time_slot === timeSlot && r.status === 'pending'
  );
}

export function createRecord(data: Omit<MedicationRecord, 'id'>): MedicationRecord {
  const records = getAllRecords();
  
  const record: MedicationRecord = {
    ...data,
    id: genId()
  };
  
  records.push(record);
  writeJson(RECORDS_FILE, records);
  
  console.log(`[medicine] 创建记录: ${record.id} - ${record.drug_name} @ ${record.time_slot}`);
  return record;
}

export function markAsTaken(recordId: string): boolean {
  const records = getAllRecords();
  const idx = records.findIndex(r => r.id === recordId);
  
  if (idx === -1) return false;
  
  records[idx].status = 'taken';
  records[idx].taken_at = new Date().toISOString();
  writeJson(RECORDS_FILE, records);
  
  console.log(`[medicine] 标记已服用: ${recordId}`);
  return true;
}

export function markAllTakenInSlot(userId: string, timeSlot: string, date?: string): number {
  const d = date || new Date().toISOString().split('T')[0];
  const records = getAllRecords();
  let count = 0;
  
  for (const record of records) {
    if (record.user_id === userId && 
        record.time_slot === timeSlot && 
        record.date === d && 
        record.status === 'pending') {
      record.status = 'taken';
      record.taken_at = new Date().toISOString();
      count++;
    }
  }
  
  if (count > 0) {
    writeJson(RECORDS_FILE, records);
    console.log(`[medicine] 标记 ${count} 条记录为已服用`);
  }
  
  return count;
}

// 创建或更新每日记录（用于提醒场景）
export function ensureTodayRecords(plans: MedicationPlan[]): MedicationRecord[] {
  const today = new Date().toISOString().split('T')[0];
  const existing = getTodayRecords(today);
  const newRecords: MedicationRecord[] = [];
  
  for (const plan of plans) {
    // 检查今天是否已有该计划对应的记录
    const hasRecord = existing.some(
      r => r.plan_id === plan.id && r.time_slot === plan.time_slot
    );
    
    if (!hasRecord) {
      const record = createRecord({
        plan_id: plan.id,
        user_id: plan.user_id,
        drug_name: plan.drug_name,
        date: today,
        time_slot: plan.time_slot,
        status: 'pending'
      });
      newRecords.push(record);
    }
  }
  
  return newRecords;
}
