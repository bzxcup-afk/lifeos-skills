import { handleMedicineMessage } from './medicine/index';

const chatId = 'oc_e6f4934bd9394f3eebad6093f81fcdee';
const senderId = 'ou_5843b2b72f4ffc8dd9d136d462eea22c';
const senderName = '老爸';
const channelType = 'group';
const mentionTarget = '@老爸';

async function run() {
  // First, check current plans
  const { getUserPlans } = await import('./medicine/storage');
  console.log('=== Before update ===');
  getUserPlans(senderId).forEach(p => console.log(`- ${p.drug_name}: ${p.time_slot}`));

  // Update aspirin to 早饭前
  console.log('\n=== Update aspirin to 早饭前 ===');
  const r1 = handleMedicineMessage('阿司匹林早饭前', chatId, senderId, senderName, channelType, mentionTarget);
  console.log('Result:', JSON.stringify(r1, null, 2));

  // Update nifedipine to 早饭前
  console.log('\n=== Update nifedipine to 早饭前 ===');
  const r2 = handleMedicineMessage('硝苯地平早饭前', chatId, senderId, senderName, channelType, mentionTarget);
  console.log('Result:', JSON.stringify(r2, null, 2));

  // Final plans
  console.log('\n=== After update ===');
  getUserPlans(senderId).forEach(p => console.log(`- ${p.drug_name}: ${p.time_slot}`));
}

run();
