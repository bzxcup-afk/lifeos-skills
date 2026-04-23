import * as fs from 'fs';
import * as path from 'path';

const PLANS_FILE = path.join(__dirname, 'medicine', 'medicine_plans.json');

interface MedicationPlan {
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

function readPlans(): MedicationPlan[] {
  const content = fs.readFileSync(PLANS_FILE, 'utf-8');
  const data = JSON.parse(content);
  if (!Array.isArray(data)) {
    throw new Error('Plans file is not an array');
  }
  return data;
}

function writePlans(plans: MedicationPlan[]): void {
  fs.writeFileSync(PLANS_FILE, JSON.stringify(plans, null, 2), 'utf-8');
}

const senderId = 'ou_5843b2b72f4ffc8dd9d136d462eea22c';
const plans = readPlans();

console.log('=== Before ===');
plans.filter(p => p.user_id === senderId).forEach(p => {
  console.log(`- ${p.drug_name}: ${p.time_slot}`);
});

// Find and update 老爸's plans
plans.forEach(p => {
  if (p.user_id === senderId && p.active) {
    if (p.drug_name === '硝苯地平') {
      p.time_slot = '早饭前';
      console.log(`Updated ${p.drug_name} -> 早饭前`);
    }
    if (p.drug_name === '阿司匹林') {
      p.time_slot = '早饭前';
      console.log(`Updated ${p.drug_name} -> 早饭前`);
    }
  }
});

writePlans(plans);

// Verify
console.log('\n=== After ===');
readPlans().filter(p => p.user_id === senderId).forEach(p => {
  console.log(`- ${p.drug_name}: ${p.time_slot}`);
});
