import { handleMedicineMessage } from './medicine/index';

const chatId = 'oc_e6f4934bd9394f3eebad6093f81fcdee';
const senderId = 'ou_5843b2b72f4ffc8dd9d136d462eea22c';
const senderName = '老爸';
const channelType = 'group';
const mentionTarget = '@老爸';

// Add second drug
console.log('=== Add second drug (阿司匹林) ===');
const result = handleMedicineMessage(
  '阿司匹林',
  chatId, senderId, senderName, channelType, mentionTarget
);
console.log(JSON.stringify(result, null, 2));
