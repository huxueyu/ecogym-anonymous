# -*- coding: utf-8 -*-

import json
from datetime import datetime
from textwrap import dedent
from typing import Any, Callable, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass

from agno.db.base import BaseDb
from agno.models.base import Model
from agno.db.schemas import UserMemory
from agno.models.message import Message
from agno.memory.vectormem import VectorMem
from agno.memory.rolling_window import RollingWindow
from agno.memory.scratch_pad import ScratchPad

class MemorySearchResponse(BaseModel):
    memory_ids: List[str] = Field(..., description="the IDs of the memories that are most semantically similar to the query.")
    scores: List[float] = Field(default=[], description="similarity scores for each memory.")
    memories: List[Dict[str, Any]] = Field(default=[], description="the actual memory content and metadata.")

@dataclass
class MemoryManager:
    model: Optional[Model] = None
    system_message: Optional[str] = None
    memory_capture_instructions: Optional[str] = None
    additional_instructions: Optional[str] = None

    memories_updated: bool = False
    delete_memories: bool = True
    clear_memories: bool = True
    update_memories: bool = True
    add_memories: bool = True

    db: Optional[BaseDb] = None

    debug_mode: bool = False

    def __init__(self,
        
        database_collection_name: str, database_persist_directory: str,
        
        model: Optional[Model] = None, system_message: Optional[str] = None,
        memory_capture_instructions: Optional[str] = None, additional_instructions: Optional[str] = None,
        db: Optional[BaseDb] = None, delete_memories: bool = False, update_memories: bool = True,
        add_memories: bool = True, clear_memories: bool = False, debug_mode: bool = False,
        
        vec_chunk_size: int = 1000, vec_chunk_overlap: int = 200, vec_similarity_threshold: float = 0.7, max_vec_memories: int = 10000,
        vec_emb_model_name: str = "all‑MiniLM‑L6‑v2", vec_emb_model_device: str = "cpu",
        
        window_size: int = 10, threshold_ratio: float = 0.7,
        
        pad_size: int = 10, pad_ttl: int = 1800, **kwargs
    ):
        self.model = model
        self.system_message = system_message
        self.memory_capture_instructions = memory_capture_instructions
        self.additional_instructions = additional_instructions
        self.db = db
        self.delete_memories = delete_memories
        self.update_memories = update_memories
        self.add_memories = add_memories
        self.clear_memories = clear_memories
        self.debug_mode = debug_mode
        
        self.vecmem = VectorMem(collection_name=database_collection_name, persist_directory=database_persist_directory,
            chunk_size=vec_chunk_size, chunk_overlap=vec_chunk_overlap, similarity_threshold=vec_similarity_threshold,
            max_memories=max_vec_memories, embedding_model_name=vec_emb_model_name, device=vec_emb_model_device)
        self.window = RollingWindow(window_size=window_size, threshold_ratio=threshold_ratio)
        self.pad = ScratchPad(size=pad_size, ttl=pad_ttl)
    
    def get_user_memories(self, user_id: Optional[str] = None, limit: int = 5) -> Optional[List[UserMemory]]:
        def _get_time(m: UserMemory): return getattr(m, "updated_at", None) or datetime.min
        
        vectormem_memories = self.vecmem.get_user_memories(user_id=user_id, limit=limit)
        rolling_window_memories = self.window.get_user_memories(user_id=user_id, limit=limit)
        scratch_pad_memories = self.pad.get_user_memories(user_id=user_id, limit=limit)
        
        all_memories: List[UserMemory] = []
        all_memories.extend(rolling_window_memories)
        all_memories.extend(scratch_pad_memories)
        
        all_memories.sort(key=_get_time)
        
        return all_memories[-limit:] if limit is not None else all_memories

    def create_user_memories(self, messages: List[Message], user_id: Optional[str] = None, **kwargs) -> str:
        summary = {"status": "ok", "model_content": None, "actions_executed": [], "errors": []}

        existing_objs = self.get_user_memories(user_id=user_id)
        existing_memories = []
        for memory in existing_objs:
            mem_text = getattr(memory, "memory", None) or str(memory)
            mem_id = getattr(memory, "memory_id", None) or getattr(memory, "id", None) or ""
            existing_memories.append({"memory_id": mem_id, "memory": mem_text})

        model_content = None
        actions = None
        system_msg = self._get_system_prompt(existing_memories)
        messages_for_model = [system_msg] + messages
        response = self.model.response(messages=messages_for_model)
        model_content = getattr(response, "content", "") or ""
        summary["model_content"] = model_content
        actions = self._parse_actions(model_content)

        if actions:
            applied = self._apply_actions(actions, user_id=user_id)
            summary["actions_executed"] = applied.get("applied", [])
            if applied.get("errors"): summary["errors"].extend(applied.get("errors"))
            if applied.get("applied"): self.memories_updated = True
        else:
            self.vecmem.create_user_memories(messages=messages, user_id=user_id, **kwargs)
            self.window.create_user_memories(messages=messages, user_id=user_id, **kwargs)
            self.pad.create_user_memories(messages=messages, user_id=user_id, **kwargs)

        if summary["errors"]: summary["status"] = "ok_with_errors"

        return json.dumps(summary)

    def _get_system_prompt(self, existing_memories: List[Dict[str, Any]]) -> Message:
        instructions = dedent(
            """
            You are a Memory Manager. Given the user's new messages and a list of existing memories,
            output a single JSON object (no extra text) with an `actions` list. Each action has:

            - op: "add" | "update" | "delete"
            - target: "vecmem" | "window" | "pad"
            - memory: text for add/update (for pad you may provide key/value instead)
            - memory_id: (for update/delete) the memory id
            - key/value: (alternative for pad) when targeting pad

            Example:
            {"actions": [{"op":"add","target":"vecmem","memory":"User likes coffee"}]}

            Rules:
            - Only output valid JSON. Do not include commentary.
            - Keep memories concise and factual.
            """
        )

        lines = [instructions, "<existing_memories>"]
        for mem in existing_memories:
            lines.append(f"ID: {mem.get('memory_id','')}")
            lines.append(f"Memory: {mem.get('memory','')}")
            lines.append("")
        lines.append("</existing_memories>")

        return Message(role="system", content="\n".join(lines))

    def _parse_actions(self, content: str) -> Optional[List[Dict[str, Any]]]:
        if not content: return None
        
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "actions" in parsed and isinstance(parsed["actions"], list):
                return parsed["actions"]
        except Exception:
            pass

        try:
            start = content.index("{")
            end = content.rindex("}")
            substring = content[start:end + 1]
            parsed = json.loads(substring)
            if isinstance(parsed, dict) and "actions" in parsed:
                return parsed["actions"]
        except Exception:
            pass

        return None

    def _apply_actions(self, actions: List[Dict[str, Any]], user_id: str = "default") -> Dict[str, Any]:
        results = {"applied": [], "errors": []}

        for act in actions:
            op = act.get("op")
            target = act.get("target", "vecmem")
            mem_text = act.get("memory") or act.get("content")
            mem_id = act.get("memory_id") or act.get("id")

            try:
                if target == "vecmem":
                    if op == "add":
                        self.vecmem.create_user_memories(messages=[Message(role="system", content=mem_text)], user_id=user_id)
                        results["applied"].append({"op": op, "target": target})
                    
                    elif op == "update" and mem_id:
                        ok = self.vecmem._update(mem_id, mem_text)
                        if ok: results["applied"].append({"op": op, "target": target, "memory_id": mem_id})
                        else: results["errors"].append(f"vecmem_update_failed:{mem_id}")
                    
                    elif op == "delete" and mem_id:
                        ok = self.vecmem._del(mem_id)
                        if ok: results["applied"].append({"op": op, "target": target, "memory_id": mem_id})
                        else: results["errors"].append(f"vecmem_delete_failed:{mem_id}")
                    
                    else:
                        results["errors"].append(f"vecmem_unsupported_op:{act}")

                elif target == "window":
                    if op == "add":
                        self.window.create_user_memories(messages=[Message(role="system", content=mem_text)], user_id=user_id)
                        results["applied"].append({"op": op, "target": target})
                    
                    elif op in ("update", "delete") and mem_id:
                        found = False
                        try:
                            dq = getattr(self.window, "window", None)
                            if dq is not None:
                                for idx, msg in enumerate(list(dq)):
                                    mid = getattr(msg, "id", None) or getattr(msg, "memory_id", None) or getattr(msg, "message_id", None)
                                    if mid and str(mid) == str(mem_id):
                                        found = True
                                        if op == "update":
                                            if hasattr(msg, "content"):
                                                msg.content = mem_text
                                            else:
                                                dq_list = list(dq)
                                                dq_list[idx] = Message(role=getattr(msg, "role", "system"), content=mem_text)
                                                self.window.window = type(self.window.window)(dq_list, maxlen=self.window.window.maxlen) if hasattr(self.window.window, "maxlen") else type(self.window.window)(dq_list)
                                            results["applied"].append({"op": op, "target": target, "memory_id": mem_id})
                                        else:
                                            dq_list = list(dq)
                                            del dq_list[idx]
                                            self.window.window = type(self.window.window)(dq_list, maxlen=self.window.window.maxlen) if hasattr(self.window.window, "maxlen") else type(self.window.window)(dq_list)
                                            results["applied"].append({"op": op, "target": target, "memory_id": mem_id})
                                        break
                        except Exception:
                            pass

                        if not found:
                            results["errors"].append(f"window_mem_not_found:{mem_id}")

                    else:
                        results["errors"].append(f"window_unsupported_op:{act}")

                elif target in ("pad", "scratch"):
                    if op == "add":
                        key = act.get("key") or f"pad_{uuid.uuid4().hex[:8]}"
                        value = act.get("value") if ("value" in act) else mem_text
                        self.pad._add(key, value, ttl=None, metadata={"source": "model_action"})
                    
                    elif op == "update":
                        key = act.get("key") or mem_id
                        value = act.get("value") or mem_text
                        if key is None:
                            results["errors"].append("pad_update_missing_key")
                        else:
                            ok = self.pad._update(key, value, extend_ttl=True)
                            if ok: results["applied"].append({"op": op, "target": target, "key": key})
                            else: results["errors"].append(f"pad_update_failed:{key}")
                    
                    elif op == "delete":
                        key = act.get("key") or mem_id
                        if key is None:
                            results["errors"].append("pad_delete_missing_key")
                        else:
                            ok = self.pad._del(key)
                            if ok: results["applied"].append({"op": op, "target": target, "key": key})
                            else: results["errors"].append(f"pad_delete_failed:{key}")
                    
                    else:
                        results["errors"].append(f"pad_unsupported_op:{act}")

                else:
                    results["errors"].append(f"unknown_target:{target}")

            except Exception as e:
                results["errors"].append(f"apply_exception:{e}")

        return results
