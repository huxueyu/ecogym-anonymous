# -*- coding: utf-8 -*-

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from agno.db.schemas import UserMemory
from agno.models.message import Message

class VectorMem(object):
    def __init__(self, collection_name: str = "vector_memories", persist_directory: str = "./chroma_memory_db",
        chunk_size: int = 1000, chunk_overlap: int = 200, similarity_threshold: float = 0.7,
        max_memories: int = 10000, embedding_model_name: str = "all‑MiniLM‑L6‑v2", device: str = "cpu"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.similarity_threshold = similarity_threshold
        self.max_memories = max_memories
        
        self.embedding_model_name = embedding_model_name
        self.device = device
        
        self.client = None
        self.collection = None
        self._init_chromadb()
            
    # compatible with the agno framework
    def get_user_memories(self, user_id: Optional[str] = None, limit: int = None) -> Optional[List[UserMemory]]:
        filter_metadata = {"user_id": {"$eq": user_id}} if user_id else None
        results = self._search(query="", limit=limit, filter_metadata=filter_metadata)
        user_memories = []
        for r in results:
            user_memories.append(UserMemory(memory=r["text"], memory_id=r["id"], metadata=r["metadata"], created_at=r["metadata"].get("created_at"),updated_at=datetime.now()))
        return user_memories
    
    # compatible with the agno framework
    def create_user_memories(self, messages: Optional[List[Message]] = None, user_id: Optional[str] = None, **kwargs) -> str:
        texts, metadatas, ids = [], [], []
        for msg in messages:
            content = getattr(msg, "content", "")
            if not content: continue
            
            meta = getattr(msg, "metadata", {})
            meta.update({"user_id": user_id if user_id is not None else "anonymous", "source": getattr(msg, "role", "unknown"), "memory_type": "vector", "created_at": datetime.now()})
            
            texts.append(content)
            metadatas.append(meta)
            ids.append(str(getattr(msg, "id", uuid.uuid4().hex)))
        
        return self._add(texts, metadatas=metadatas, ids=ids)

    
    def __len__(self):
        try:
            return self.collection.count()
        except Exception as e:
            print(f"[VectorMem] fail with len(): {e}")
            return 0
    
    def _init_chromadb(self):

        self.client = chromadb.PersistentClient(path=self.persist_directory, settings=Settings(anonymized_telemetry=False))
        
        try:
            self.collection = self.client.get_collection(name=self.collection_name)  
            print(f"[VectorMem] using existing collection '{self.collection_name}'")
        except Exception:
            self.collection = self.client.create_collection(name=self.collection_name, metadata={"description": "Vector memory collection (semantic)"})     
            print(f"[VectorMem] create new collection '{self.collection_name}'")
    
    def _chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap
        return chunks
    
    def _add(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> List[str]:
        if not texts: return []
        
        if ids is None: ids = [str(uuid.uuid4()) for _ in texts]
        
        if metadatas is None: metadatas = [{} for _ in texts]

        chunked_texts, chunked_metas, chunked_ids = [], [], []

        for i, text in enumerate(texts):
            chunks = self._chunk_text(text)
            for j, chunk in enumerate(chunks):
                chunked_texts.append(chunk)
                meta = metadatas[i].copy()
                meta.update({"chunk_index": j, "total_chunks": len(chunks), "memory_type": "vector", "created_at": datetime.now().isoformat()})
                chunked_metas.append(meta)
                chunked_ids.append(f"{ids[i]}_chunk_{j}")

        self.collection.add(documents=chunked_texts, metadatas=chunked_metas, ids=chunked_ids)
        print(f"[VectorMem] add {len(chunked_texts)} vector memory to collection '{self.collection_name}'")
        return chunked_ids
    
    def _search(self, query: str, limit: int = 5, similarity_threshold: Optional[float] = None, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        threshold = similarity_threshold if similarity_threshold is not None else self.similarity_threshold
        results = self.collection.query(query_texts=[query], n_results=limit, where=filter_metadata)

        docs = results.get("documents", [[]])[0]
        ids = results.get("ids", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        filtered = []
        for i, text in enumerate(docs):
            score = 1.0 - distances[i]
            if score >= threshold:
                filtered.append({"id": ids[i], "text": text, "metadata": metas[i], "score": score})
        return filtered
    
    def _update(self, memory_id: str, new_text: str, new_metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            self.collection.delete(ids=[memory_id])
            self.collection.add(documents=[new_text], metadatas=[new_metadata if new_metadata is not None else {}], ids=[memory_id])
            
            print(f"[VectorMem] update memory {memory_id}")
            return True
        except Exception as e:
            
            print(f"[VectorMem] fail to update memory {memory_id}: {e}")
            return False
        
    def _del(self, memory_id: str) -> bool:
        try:
            self.collection.delete(ids=[memory_id])
            
            print(f"[VectorMem] delete memory {memory_id}")
            return True
        except Exception as e:
            print(f"[VectorMem] fail to delete memory {memory_id}: {e}")
            return False