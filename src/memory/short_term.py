"""
短期记忆管理 - 支持长对话的滑动窗口 + 智能压缩
"""

import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

from ..models.base import Message

logger = logging.getLogger(__name__)


@dataclass
class ConversationSummary:
    """对话摘要"""
    level: int                          # 1=最近完整, 2=中期摘要, 3=早期摘要
    content: str
    start_time: datetime
    end_time: datetime
    message_count: int
    key_points: List[str] = field(default_factory=list)


class ShortTermMemory:
    """
    短期记忆管理器
    
    支持长对话的策略：
    1. 保留最近 N 轮完整对话
    2. 中期对话压缩成摘要
    3. 早期对话提取关键事实到长期记忆
    4. 关键节点永久保留
    """
    
    def __init__(
        self,
        max_recent: int = 10,            # 保留最近 10 轮
        max_mid_term: int = 20,          # 中期窗口 20 轮
        compression_threshold: int = 30  # 超过 30 轮开始压缩
    ):
        self.max_recent = max_recent
        self.max_mid_term = max_mid_term
        self.compression_threshold = compression_threshold
        
        # 三层存储
        self.recent_messages: List[Message] = []
        self.mid_term_summary: Optional[ConversationSummary] = None
        self.key_moments: List[Message] = []
        
        self.session_start = datetime.now()
        self.total_messages = 0
    
    def add_message(self, message: Message) -> None:
        """添加新消息"""
        self.recent_messages.append(message)
        self.total_messages += 1
        
        # 检查是否是关键节点
        if self._is_key_moment(message):
            self.key_moments.append(message)
            logger.info(f"💡 关键节点已记录: {message.content[:50]}...")
        
        # 检查是否需要压缩
        if len(self.recent_messages) > self.max_recent:
            self._compress_old_messages()
    
    def _is_key_moment(self, message: Message) -> bool:
        """判断是否为关键节点"""
        content = message.content.lower()
        
        # 用户明确要求记住
        if any(kw in content for kw in ["记住", "记住", "save this", "记住"]):
            return True
        
        # 重要决策或确认
        if any(kw in content for kw in ["确定", "确认", "decided", "confirm"]):
            return True
        
        # 包含具体数据/配置
        if any(kw in content for kw in ["密码", "key", "token", "config", "配置"]):
            return True
        
        # 用户纠正
        if any(kw in content for kw in ["不对", "错了", "应该是", "不对"]):
            return True
        
        return False
    
    def _compress_old_messages(self) -> None:
        """压缩旧消息到中期摘要"""
        # 取出最老的消息
        oldest = self.recent_messages.pop(0)
        
        # 如果有中期摘要，追加；否则创建新的
        if self.mid_term_summary is None:
            self.mid_term_summary = ConversationSummary(
                level=2,
                content=f"早期对话包含: {oldest.content[:100]}...",
                start_time=oldest.timestamp,
                end_time=oldest.timestamp,
                message_count=1
            )
        else:
            self.mid_term_summary.content += f"; {oldest.content[:50]}"
            self.mid_term_summary.end_time = oldest.timestamp
            self.mid_term_summary.message_count += 1
        
        logger.debug(f"📝 消息已压缩到中期摘要: {oldest.content[:50]}...")
    
    def get_context(self) -> str:
        """获取完整上下文供 LLM 使用"""
        parts = []
        
        # 早期摘要
        if self.mid_term_summary:
            parts.append(f"【早期对话摘要（{self.mid_term_summary.message_count}轮）】\n{self.mid_term_summary.content}")
        
        # 关键节点
        if self.key_moments:
            key_content = "\n".join([
                f"- [{m.role}] {m.content[:100]}"
                for m in self.key_moments[-5:]  # 只保留最近5个关键节点
            ])
            parts.append(f"【关键节点】\n{key_content}")
        
        # 最近对话
        if self.recent_messages:
            recent_content = "\n".join([
                f"{m.role}: {m.content}"
                for m in self.recent_messages
            ])
            parts.append(f"【最近对话】\n{recent_content}")
        
        return "\n\n".join(parts) if parts else "（对话刚开始）"
    
    def get_messages_for_llm(self, max_tokens: int = 4000) -> List[Dict[str, str]]:
        """获取适合 LLM 的消息格式（带长度限制）"""
        messages = []
        
        # 添加系统提示（如果有摘要）
        if self.mid_term_summary:
            messages.append({
                "role": "system",
                "content": f"对话摘要: {self.mid_term_summary.content[:500]}"
            })
        
        # 添加最近消息
        for msg in self.recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    def should_summarize(self) -> bool:
        """判断是否应该进行整体摘要"""
        return self.total_messages >= self.compression_threshold
    
    def generate_summary(self) -> str:
        """生成对话整体摘要"""
        summary_parts = [
            f"对话开始于 {self.session_start.strftime('%Y-%m-%d %H:%M')}",
            f"总共 {self.total_messages} 轮对话",
        ]
        
        if self.key_moments:
            summary_parts.append(f"关键节点: {len(self.key_moments)} 个")
        
        # 提取主题（简单实现：基于关键词频率）
        all_content = " ".join([m.content for m in self.recent_messages])
        # TODO: 使用 LLM 生成更智能的摘要
        
        return "; ".join(summary_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_messages": self.total_messages,
            "recent_count": len(self.recent_messages),
            "key_moments": len(self.key_moments),
            "has_mid_summary": self.mid_term_summary is not None,
            "session_duration_minutes": (datetime.now() - self.session_start).seconds // 60
        }
    
    def clear(self) -> None:
        """清空短期记忆"""
        self.recent_messages.clear()
        self.mid_term_summary = None
        self.key_moments.clear()
        self.total_messages = 0
        logger.info("🧹 短期记忆已清空")