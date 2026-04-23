import { handleMedicineMessage } from './medicine/index';

const result = handleMedicineMessage(
  '现在吃硝苯地平控释片，阿司匹林',
  'oc_e6f4934bd9394f3eebad6093f81fcdee',
  'ou_5843b2b72f4ffc8dd9d136d462eea22c',
  '老爸',
  'group',
  '@老爸'
);

console.log(JSON.stringify(result, null, 2));
