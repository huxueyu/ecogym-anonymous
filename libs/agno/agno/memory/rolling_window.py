# -*- coding: utf-8 -*-

from collections import deque
from dataclasses import field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from agno.db.schemas import UserMemory
from agno.models.message import Message

class RollingWindow(object):
    def __init__(self, window_size: int = 10, threshold_ratio: float = 0.7):
        self.max_size = window_size
        self.threshold = int(window_size * threshold_ratio)
        self.window = deque(maxlen=window_size)
    
    def get_user_memories(self, user_id: Optional[str] = None, limit: int = None) -> Optional[List[UserMemory]]:
        raw_msgs = self._get(limit)
        user_memories = []
        
        for msg in raw_msgs:
            content = f"[{getattr(msg, 'role', 'msg')}]: {getattr(msg, 'content', '')}"
            msg_id = getattr(msg, 'id', None)
            timestamp = getattr(msg, 'created_at', None)
        
            user_memories.append(UserMemory(memory=content, memory_id=str(msg_id) if msg_id else None, updated_at=timestamp))
        
        return user_memories          
    
    def create_user_memories(self, messages: Optional[List[Message]] = None, user_id: Optional[str] = None, **kwargs) -> str:
        added_ids = []
        for msg in messages:
            self._add(msg)
            added_ids.append(getattr(msg, "id", None))
        return added_ids

    def __len__(self):
        return len(self.window)
        
    def _merge():
        prev_msg = None
        i = 0
        while i < len(self.window):
            msg = self.window[i]
            
            if prev_msg and hasattr(prev_msg, "role") and hasattr(msg, "role") and prev_msg.msg.role and hasattr(prev_msg, "content") and hasattr(msg, "content"):
                prev_msg.content += f"\n{msg.content}"
                self.window.remove(msg)
            else:
                prev_msg = msg
                i += 1            
    
    def _add(self, message: Message, metadata: Optional[Dict[str, Any]] = None) -> None:
        if len(self.window) >= self.threshold: self._merge()
        
        if len(self.window) >= self.max_size: self.window.popleft()
        
        if metadata:
            if not hasattr(message, "metadata"): message.metadata = {}
            message.metadata.update(metadata)
        
        if not hasattr(message, "timestamp"): message.timestamp = datetime.now()
        
        self.window.append(message)
    
    def _get(self, limit: Optional[int] = None) -> List[Message]:
        return list(self.window)[-limit:] if limit is not None else list(self.window)
    
    def _search(self, query: str, limit: int = 5, keyname: Literal["content", "metadata", "both"] = "content") -> List[Message]:
        lower_query = query.lower()
        results = []
        
        for msg in reversed(self.window):
            if len(results) >= limit: break

            fileds = []
            if keyname in ["content", "both"]:
                fileds += [getattr(msg, "content", ""), str(getattr(msg, "message", ""))]
            if keyname in ["metadata", "both"]:
                meta = getattr(msg, "metadata", {})
                if isinstance(meta, dict):
                    fields += [v for v in meta.values() if isinstance(v, str)]

            if any(lower_query in str(f).lower() for f in fields if f):
                results.append(msg)
            
        return results
    
    def _clear(self) -> None:
        self.window.clear()