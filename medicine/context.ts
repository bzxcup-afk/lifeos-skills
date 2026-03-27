/**
 * medicine/context.ts
 * 药品模块上下文：管理对话状态和渠道信息
 */

export interface MedicineContext {
  // 当前用户
  user_id: string;
  user_name: string;
  
  // 渠道信息
  channel_type: 'group' | 'direct';
  channel_id: string;
  
  // 提及目标（群里需要@的用户）
  mention_target: string;
  
  // 当前状态
  state: 'idle' | 'awaiting_time_slot';
  
  // 暂存的药物信息
  pending_drug?: string;
}

export class MedicineContextStore {
  // 内存中的上下文（按 chat_id + sender_id 索引）
  private static contexts: Map<string, MedicineContext> = new Map();
  
  private static key(chatId: string, senderId: string): string {
    return `${chatId}:${senderId}`;
  }
  
  static get(chatId: string, senderId: string): MedicineContext | undefined {
    return this.contexts.get(this.key(chatId, senderId));
  }
  
  static set(chatId: string, senderId: string, ctx: MedicineContext): void {
    this.contexts.set(this.key(chatId, senderId), ctx);
  }
  
  static clear(chatId: string, senderId: string): void {
    this.contexts.delete(this.key(chatId, senderId));
  }
  
  static fromMessage(
    chatId: string,
    senderId: string,
    senderName: string,
    channelType: 'group' | 'direct',
    mentionTarget?: string
  ): MedicineContext {
    const existing = this.get(chatId, senderId);
    if (existing) return existing;
    
    const ctx: MedicineContext = {
      user_id: senderId,
      user_name: senderName,
      channel_type: channelType,
      channel_id: chatId,
      mention_target: mentionTarget || senderName,
      state: 'idle'
    };
    
    this.set(chatId, senderId, ctx);
    return ctx;
  }
}
