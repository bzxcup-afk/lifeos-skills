import { handleMedicineMessage } from './medicine/index';
import { getUserPlans } from './medicine/storage';

const chatId = 'oc_e6f4934bd9394f3eebad6093f81fcdee';
const senderId = 'ou_5843b2b72f4ffc8dd9d136d462eea22c';
const senderName = '老爸';
const channelType = 'group';
const mentionTarget = '@老爸';

async function run() {
  // Drug 1: 硝苯地平
  console.log('=== 1. 硝苯地平 ===');
  const r1 = handleMedicineMessage('硝苯地平', chatId, senderId, senderName, channelType, mentionTarget);
  console.log('Result:', r1.askTimeSlot ? '(ask time slot)' : r1.reply);

  // Drug 2: 阿司匹林
  console.log('\n=== 2. 阿司匹林 ===');
  const r2 = handleMedicineMessage('阿司匹林', chatId, senderId, senderName, channelType, mentionTarget);
  console.log('Result:', r2.askTimeSlot ? '(ask time slot)' : r2.reply);

  // Time slot for 阿司匹林
  console.log('\n=== 3. Time slot for 阿司匹林 (晚餐后) ===');
  const r3 = handleMedicineMessage('晚餐后', chatId, senderId, senderName, channelType, mentionTarget);
  console.log('Result:', r3.reply);

  // Check plans
  console.log('\n=== Current plans ===');
  const plans = getUserPlans(senderId);
  plans.forEach(p => console.log(`- ${p.drug_name}: ${p.time_slot}`));
}

run();
