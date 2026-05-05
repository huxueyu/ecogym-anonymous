# -*- coding: utf-8 -*-

import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from agno.db.schemas import UserMemory
from agno.models.message import Message

class ScratchPad(object):
    def __init__(self, size: int = 10, ttl: int = 1800):
        self.ttl = ttl
        self.max_size = size
        self.pad = {}
    

    def get_user_memories(self, user_id: Optional[str] = None, limit: int = None) -> Optional[List[UserMemory]]:
        curr_time = datetime.now()
        valid_items = [(k, v) for k, v in self.pad.items() if curr_time <= v["expires_at"]]
        valid_items.sort(key=lambda x: x[1]["updated_at"], reverse=True)
        if limit is not None: valid_items = valid_items[:limit]

        user_memories = []
        for key, item in valid_items:
            content = f"[scratch-var] {key} = {item['value']}"
            user_memories.append(UserMemory(memory=content, memory_id=key, metadata=item.get("metadata", {}), updated_at=item["updated_at"], created_at=item["created_at"]))

        return user_memories
    

    def create_user_memories(self, messages: Optional[List[Message]] = None, user_id: Optional[str] = None, **kwargs) -> str:
        
        # support format like `a=1`, `set a to 1`, `a: 0.8`
        pattern = re.compile(r'\b([A-Za-z_]\w*)\b\s*(?:=|:|->|to)\s*([-+]?\d*\.\d+|\d+|true|false|".*?"|\'.*?\'|\w+)', re.IGNORECASE)
        
        added_keys = []
        for msg in messages:
            text = getattr(msg, "content", str(msg))

            for var, val in re.findall(pattern, text):
                key = var.strip()
                val = val.strip().strip('\'"')

                if val.lower() in ("true", "false"): val_parsed = val.lower() == "true"
                elif re.fullmatch(r"[-+]?\d+", val): val_parsed = int(val)
                elif re.fullmatch(r"[-+]?\d*\.\d+", val): val_parsed = float(val)
                else: val_parsed = val

                self.add(key, val_parsed, metadata={"source": "scratch_text", "raw": text})
                added_keys.append(key)
        
        return added_keys
    
    def __len__(self):
        return len(self.pad)

    def _cleanup(self):
        curr_time = datetime.now()
        expired_keys = [k for k, v in self.pad.items() if curr_time > v["expires_at"]]
        for k in expired_keys: del self.pad[k]
        
        if len(self.pad) > self.max_size:
            sorted_items = sorted(self.pad.items(), key=lambda x: x[1].get("last_accessed", x[1]["created_at"]))
            for k, _ in sorted_items[:len(self.pad) - self.max_size]:
                del self.pad[k]
    
    def _add(self, key_name: str, value: Any, ttl: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None):
        if len(self.pad) >= self.size: self._cleanup()
        
        curr_ttl = ttl if ttl is not None else self.ttl
        start_time = datetime.now()
        expired_time = start_time + timedelta(seconds=ttl)
        
        self.pad[key_name] = {
            "value": value,
            "created_at": start_time,
            "updated_at": start_time,
            "last_accessed": start_time,
            "expires_at": expired_time,
            "metadata": metadata if metadata is not None else {},
            "access_count": 0,
        }    

    def _get(self, key_name: str, default_result: Any = None):
        if key_name not in self.pad: return default_result
        
        item = self.pad[key_name]
        curr_time = datetime.now()
        if curr_time > item["expires_at"]:
            del self.pad[key_name]
            return default_result

        item["access_count"] += 1
        item["last_accessed"] = curr_time
        
        return item["value"]

    def _update(self, key_name: str, value: Any, extend_ttl: bool = True) -> bool:
        if key_name not in self.pad: return False
        curr_time = datetime.now()
        
        self.pad[key_name]["value"] = value
        self.pad[key_name]["updated_at"] = curr_time
        
        if extend_ttl:
            self.pad[key_name]["expires_at"] = curr_time + timedelta(seconds=self.ttl)
        
        return True
    
    def _del(self, key_name: str) -> bool:
        if key_name in self.pad:
            del self.pad[key_name]
            return True
        return False
    
    def _search(self, query: str, search_metadata: bool = True) -> Dict[str, Any]:
        q = query.lower()
        curr_time = datetime.now()
        
        results = {}
        for k, v in self.pad.items():
            if curr_time > v["expires_at"]: continue
            
            str_v = str(v.get("value", "")).lower()
            metadata = v.get("metadata", {})
            
            if q in k.lower() or q in str_v or (search_metadata and any(q in str(mv).lower() for mv in metadata.values())):
                results[k] = v
        
        return results
    
    def _clear(self):
        self.pad.clear()
    