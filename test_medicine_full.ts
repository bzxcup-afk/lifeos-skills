import { handleMedicineMessage } from './medicine/index';

const chatId = 'oc_e6f4934bd9394f3eebad6093f81fcdee';
const senderId = 'ou_5843b2b72f4ffc8dd9d136d462eea22c';
const senderName = '老爸';
const channelType = 'group';
const mentionTarget = '@老爸';

// Step 1: User says they're taking medications
console.log('=== Step 1: Initial message ===');
const result1 = handleMedicineMessage(
  '现在吃硝苯地平控释片，阿司匹林',
  chatId, senderId, senderName, channelType, mentionTarget
);
console.log(JSON.stringify(result1, null, 2));

// Step 2: User selects time slot (假设选睡前)
console.log('\n=== Step 2: Select time slot (睡前) ===');
const result2 = handleMedicineMessage(
  '睡前',
  chatId, senderId, senderName, channelType, mentionTarget
);
console.log(JSON.stringify(result2, null, 2));
