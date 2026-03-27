#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeOS 对话层适配器

专门处理来自对话（Feishu/其他平台）的数据记录请求。
负责：
1. 身份识别和路由到 profile_id
2. 调用本地数据库服务记录数据
3. 生成简洁的回复消息

使用示例：
    from chat_adapter import ChatAdapter
    
    adapter = ChatAdapter()
    result = adapter.handle_sleep_record(
        chat_id="ou_xxx",
        sender_name="金",
        hours=7.5
    )
    print(result['reply_message'])  # 已记录 7.5 小时睡眠
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from local_adapter import save_daily_log, get_profile, is_local_mode
from lifeos_service import get_service


class ChatAdapter:
    """
    对话层适配器
    
    封装对话层与数据层的交互逻辑
    """
    
    def __init__(self):
        self._profile_cache = {}
    
    def _resolve_profile_id(self, chat_id: str, sender_name: str) -> Optional[str]:
        """
        根据 chat_id 和 sender_name 解析 profile_id
        
        从 config/bitable_config.json 的 identity_mapping 中查找匹配
        """
        try:
            # 读取配置文件
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'bitable_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            identity_mappings = config.get('identity_mapping', [])
            
            # 构建 chat_key
            chat_key = chat_id
            if not chat_id.startswith(('ou_', 'oc_')):
                chat_key = chat_id
            
            # 标准化 sender_name
            normalized_name = sender_name.strip() if sender_name else ''
            
            # 查找匹配
            for mapping in identity_mappings:
                # 匹配 chat_id
                mapping_chat_id = mapping.get('chat_id', '')
                mapping_chat_key = mapping.get('chat_key', mapping_chat_id)
                
                chat_match = (chat_key == mapping_chat_id or 
                             chat_key == mapping_chat_key)
                
                # 匹配 name
                mapping_names = mapping.get('names', [mapping.get('name', '')])
                name_match = normalized_name in [n.strip() for n in mapping_names]
                
                if chat_match and name_match:
                    profile_id = mapping.get('profile_id')
                    if profile_id:
                        return profile_id
                    # 兼容旧配置
                    bitable_key = mapping.get('bitable_key', '')
                    if bitable_key:
                        # 从 bitable_key 推断 profile_id
                        key_map = {
                            'lifeos_jin': '001',
                            'lifeos_fangfang': '002',
                            'lifeos_laoma': '003',
                            'lifeos_laolao': '004'
                        }
                        return key_map.get(bitable_key, '001')
            
            # 默认返回 001
            return '001'
            
        except Exception as e:
            print(f"[ChatAdapter] Error resolving profile_id: {e}")
            return '001'
    
    def _get_profile_name(self, profile_id: str) -> str:
        """获取用户显示名"""
        name_map = {
            '001': '金',
            '002': '芳芳',
            '003': '老妈',
            '004': '老爹'
        }
        return name_map.get(profile_id, '用户')
    
    # ========================================================================
    # 公开 API：睡眠记录
    # ========================================================================
    
    def handle_sleep_record(self, chat_id: str, sender_name: str,
                           hours: float, quality: Optional[int] = None,
                           date: Optional[str] = None) -> Dict[str, Any]:
        """
        处理睡眠记录请求
        
        Args:
            chat_id: 聊天会话ID
            sender_name: 发送者昵称
            hours: 睡眠时长（小时）
            quality: 睡眠质量（1-10，可选）
            date: 日期（默认今天）
        
        Returns:
            {
                'success': bool,
                'profile_id': str,
                'reply_message': str,  # 可直接发送给用户的回复
                'data': dict  # 保存的数据
            }
        """
        # 解析用户身份
        profile_id = self._resolve_profile_id(chat_id, sender_name)
        user_name = self._get_profile_name(profile_id)
        
        # 确定日期
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # 获取服务并保存
            svc = get_service(profile_id)
            
            # 构建数据
            data = {
                'date': date,
                'sleep_hours': hours,
            }
            if quality is not None:
                data['sleep_quality'] = quality
            
            # 合并现有数据
            existing = svc.health.get_daily_log(date)
            if existing:
                for key in ['fatigue_score', 'energy_score', 'weight_kg', 'had_training',
                           'training_brief', 'diet_status', 'body_status_notes', 
                           'today_summary', 'state_tags']:
                    if existing.get(key) and key not in data:
                        data[key] = existing[key]
            
            log_id = svc.health.save_daily_log(data)
            
            # 构建回复消息
            quality_text = f"，质量 {quality}/10" if quality else ""
            reply = f"已记录 {date} 睡眠 {hours} 小时{quality_text}"
            
            return {
                'success': True,
                'profile_id': profile_id,
                'reply_message': reply,
                'data': {
                    'log_id': log_id,
                    'date': date,
                    'sleep_hours': hours,
                    'sleep_quality': quality
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'profile_id': profile_id,
                'reply_message': f"记录失败：{str(e)}",
                'data': None
            }
    
    # 简化接口别名
    record_sleep = handle_sleep_record


# ============================================================================
# 便捷函数（供简单场景直接使用）
# ============================================================================

def record_sleep(chat_id: str, sender_name: str, hours: float,
                quality: Optional[int] = None) -> str:
    """
    快捷记录睡眠，返回可直接回复用户的消息
    
    示例：
        reply = record_sleep("ou_xxx", "金", 7.5, 8)
        # reply: "已记录 2026-03-26 睡眠 7.5 小时，质量 8/10"
    """
    adapter = ChatAdapter()
    result = adapter.record_sleep(chat_id, sender_name, hours, quality)
    return result['reply_message']


def get_user_profile(chat_id: str, sender_name: str) -> Optional[Dict[str, Any]]:
    """
    获取用户资料
    """
    adapter = ChatAdapter()
    profile_id = adapter._resolve_profile_id(chat_id, sender_name)
    return get_profile(profile_id)
