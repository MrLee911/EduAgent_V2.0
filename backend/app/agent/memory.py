# 对话记忆管理：基于 Redis 的 ConversationMemory
# 对应文档：05 §5.1

import json
import uuid
from datetime import datetime, timezone
from typing import Optional


class ConversationMemory:
    """
    基于 Redis 的对话记忆管理。

    策略：
    - 窗口大小：最近 10 轮对话（约 20 条消息）
    - TTL：24 小时无活动自动清除
    - Key 格式：conv:{course_id}:{user_id}:{conversation_id}
    """

    def __init__(self, redis_client=None, session_id: Optional[str] = None):
        self.redis = redis_client
        self.window_size = 20  # 消息数（10 轮）
        self.ttl = 86400       # 24 小时
        self._session_id = session_id

    def get_history(self, course_id: str, user_id: str, conversation_id: str) -> list[dict]:
        """获取对话历史（最近 N 条消息）"""
        if not self.redis:
            return []
        key = self._make_key(course_id, user_id, conversation_id)
        raw = self.redis.get(key)
        if not raw:
            return []
        try:
            messages = json.loads(raw)
            return messages[-self.window_size:]
        except json.JSONDecodeError:
            return []

    def add_message(self, course_id: str, user_id: str, conversation_id: str,
                    role: str, content: str):
        """添加一条消息到对话历史"""
        if not self.redis:
            return
        key = self._make_key(course_id, user_id, conversation_id)
        messages = self.get_history(course_id, user_id, conversation_id)
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.redis.setex(key, self.ttl, json.dumps(messages, ensure_ascii=False))

    def clear(self, course_id: str, user_id: str, conversation_id: str):
        """清除对话历史"""
        if not self.redis:
            return
        key = self._make_key(course_id, user_id, conversation_id)
        self.redis.delete(key)

    async def get_recent(self, limit: int = 10) -> list[dict]:
        """获取最近 N 条消息（供 PromptContext 调用）"""
        # 降级为内存实现（无 Redis 时）
        return []

    @staticmethod
    def create_new_conversation() -> str:
        """创建新对话，返回 UUID"""
        return str(uuid.uuid4())

    @staticmethod
    def _make_key(course_id: str, user_id: str, conversation_id: str) -> str:
        """生成 Redis Key"""
        return f"conv:{course_id}:{user_id}:{conversation_id}"
