#!/usr/bin/env python3
"""
ChromaDB Memory 完整使用指南
展示如何调用ChromaDB的记忆功能
"""

import sys
import os
import uuid
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

import chromadb
from chromadb.config import Settings

class ChromaDbMemoryAdapter:
    """ChromaDB记忆适配器"""
    def __init__(self, collection_name="memory_collection", persist_directory="./chroma_memory_db"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"SUCCESS: 使用现有集合 '{collection_name}'")
        except ValueError:
            encoder
        from sentence_transformers import SentenceTransformer
        small_model = SentenceTransformer("paraphrase-MiniLM-L3-v2")
        
        print(f"SUCCESS: 创建新集合 '{collection_name}'")
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"description": "MemoryManager vector collection"},
            embedding_function=small_model.encode
        )
    
    def add_texts_to_collection(self, collection_name, texts, metadatas=None, ids=None):
        """添加文本到集合"""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"SUCCESS: 添加了 {len(texts)} 个文档到ChromaDB")
        return ids
    
    def search_collection(self, collection_name, query, limit=5, filter=None):
        """搜索集合"""
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=filter
        )
        
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'id': results['ids'][0][i] if results['ids'] and results['ids'][0] else str(uuid.uuid4()),
                    'text': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                    'score': 1.0 - results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0
                })
        
        print(f"SUCCESS: ChromaDB搜索找到 {len(formatted_results)} 个相关文档")
        return formatted_results
    
    def update_text_in_collection(self, collection_name, text_id, new_text, new_metadata=None):
        """更新文本"""
        try:
            self.collection.delete(ids=[text_id])
            
            metadata = new_metadata or {}
            self.collection.add(
                documents=[new_text],
                metadatas=[metadata],
                ids=[text_id]
            )
            
            print(f"SUCCESS: 更新了文档 {text_id}")
            return True
        except Exception as e:
            print(f"ERROR: 更新失败: {e}")
            return False
    
    def delete_text_from_collection(self, collection_name, text_id):
        """删除文本"""
        try:
            self.collection.delete(ids=[text_id])
            print(f"SUCCESS: 删除了文档 {text_id}")
            return True
        except Exception as e:
            print(f"ERROR: 删除失败: {e}")
            return False
    
    def get_collection_size(self, collection_name):
        """获取集合大小"""
        try:
            count = self.collection.count()
            return count
        except Exception as e:
            print(f"ERROR: 获取大小失败: {e}")
            return 0


def demo_chromadb_memory_usage():
    """演示ChromaDB记忆的完整使用流程"""
    print("=== ChromaDB Memory 完整使用指南 ===")
    
    try:
        import chromadb
        print("SUCCESS: ChromaDB已安装")
    except ImportError:
        print("ERROR: ChromaDB未安装，请先安装: pip install chromadb")
        return False

    print("\n1. 创建ChromaDB适配器...")
    adapter = ChromaDbMemoryAdapter()
    
    from agno.memory.manager import MemoryManager
    from agno.models.message import Message
    
    print("\n2. 创建MemoryManager...")
    memory_manager = MemoryManager(
        db=adapter,
        vector_collection="user_memories",
        vector_chunk_size=500,
        vector_similarity_threshold=0.6,
        max_vector_memories=1000,
        window_size=10,
        scratch_pad_ttl=1800,
        memory_analytics=True
    )
    
    print("SUCCESS: MemoryManager创建成功")
    print(f"   集合名称: {memory_manager.vector_collection}")
    
    print("\n3. 添加长期记忆...")
    
    personal_info = [
        "我的名字是张三，今年25岁，是一名软件工程师。",
        "我住在北京，喜欢编程和阅读技术书籍。",
        "我目前在学习Python和机器学习相关技术。",
        "我的工作重点是Web开发和数据分析。",
        "我计划在今年内完成一个个人项目。"
    ]
    
    personal_metadata = [
        {"type": "personal", "category": "identity", "importance": "high"},
        {"type": "personal", "category": "location", "importance": "medium"},
        {"type": "personal", "category": "interests", "importance": "high"},
        {"type": "personal", "category": "work", "importance": "high"},
        {"type": "personal", "category": "goals", "importance": "medium"}
    ]
    
    personal_ids = memory_manager.add_to_vector_memory(
        texts=personal_info,
        metadatas=personal_metadata,
        importance_score=0.8
    )
    print(f"SUCCESS: 添加了 {len(personal_ids)} 条个人记忆")
    
    tech_knowledge = [
        "Python是一种高级编程语言，以其简洁和可读性著称。",
        "机器学习是人工智能的一个子集，专注于算法和统计模型。",
        "Web开发包括前端和后端开发，前端负责用户界面，后端负责服务器逻辑。",
        "数据分析使用统计方法和工具来提取数据中的洞察。",
        "版本控制工具如Git帮助开发者管理代码变更。"
    ]
    
    tech_metadata = [
        {"type": "knowledge", "category": "programming", "topic": "python"},
        {"type": "knowledge", "category": "ai", "topic": "machine_learning"},
        {"type": "knowledge", "category": "web", "topic": "development"},
        {"type": "knowledge", "category": "data", "topic": "analysis"},
        {"type": "knowledge", "category": "tools", "topic": "version_control"}
    ]
    
    tech_ids = memory_manager.add_to_vector_memory(
        texts=tech_knowledge,
        metadatas=tech_metadata,
        importance_score=0.7
    )
    print(f"SUCCESS: 添加了 {len(tech_ids)} 条技术知识记忆")
    
    print("\n4. 搜索和检索记忆...")
    
    print("\n搜索个人相关记忆:")
    personal_results = memory_manager.search_vector_memory(
        query="个人信息",
        limit=3
    )
    print(f"找到 {len(personal_results.memories)} 条个人记忆:")
    for i, memory in enumerate(personal_results.memories):
        print(f"  {i+1}. {memory['content'][:50]}... (相似度: {memory['score']:.3f})")
        print(f"     元数据: {memory['metadata']}")
    
    print("\n搜索技术相关记忆:")
    tech_results = memory_manager.search_vector_memory(
        query="编程技术",
        limit=3
    )
    print(f"找到 {len(tech_results.memories)} 条技术记忆:")
    for i, memory in enumerate(tech_results.memories):
        print(f"  {i+1}. {memory['content'][:50]}... (相似度: {memory['score']:.3f})")
        print(f"     元数据: {memory['metadata']}")
    
    print("\n按元数据过滤搜索:")
    filtered_results = memory_manager.search_vector_memory(
        query="学习",
        limit=5,
        filter_metadata={"type": "personal"}
    )
    print(f"找到 {len(filtered_results.memories)} 条个人学习相关记忆:")
    for i, memory in enumerate(filtered_results.memories):
        print(f"  {i+1}. {memory['content'][:50]}... (相似度: {memory['score']:.3f})")
    
    print("\n5. 更新记忆...")
    if personal_ids:
        update_success = memory_manager.update_vector_memory(
            memory_id=personal_ids[0],
            new_content="我的名字是张三，今年26岁，是一名高级软件工程师。",
            new_metadata={"type": "personal", "category": "identity", "importance": "high", "updated": True}
        )
        print(f"更新结果: {'成功' if update_success else '失败'}")
    
    print("\n6. 删除记忆...")
    if len(tech_ids) > 1:
        delete_success = memory_manager.delete_vector_memory(tech_ids[-1])
        print(f"删除结果: {'成功' if delete_success else '失败'}")
    
    print("\n7. 使用短期记忆...")
    
    conversation = [
        Message(content="你好，我想了解一下你的技术背景", role="user"),
        Message(content="我是一名软件工程师，主要使用Python进行开发", role="assistant"),
        Message(content="你能帮我学习机器学习吗？", role="user"),
        Message(content="当然可以！机器学习是很有趣的领域", role="assistant"),
        Message(content="我应该从哪里开始学习？", role="user"),
        Message(content="建议从Python基础开始，然后学习NumPy和Pandas", role="assistant")
    ]
    
    for msg in conversation:
        memory_manager.add_to_rolling_window(msg)
    
    recent_conversation = memory_manager.get_rolling_window(limit=3)
    print(f"SUCCESS: 添加了 {len(recent_conversation)} 条对话记录")
    print("最近的对话:")
    for i, msg in enumerate(recent_conversation):
        print(f"  {i+1}. [{msg.role}]: {msg.content}")
    
        print("\n8. 使用工作记忆...")
    
    memory_manager.add_to_scratch_pad(
        key="current_task",
        value="帮助用户学习机器学习",
        metadata={"priority": "high", "deadline": "2024-02-01"}
    )
    
    memory_manager.add_to_scratch_pad(
        key="learning_progress",
        value={"completed": ["Python基础"], "current": "NumPy学习", "next": "Pandas学习"},
        metadata={"type": "progress", "last_updated": "2024-01-15"}
    )
    
    memory_manager.add_to_scratch_pad(
        key="user_preferences",
        value={"learning_style": "hands-on", "difficulty": "intermediate", "time_available": "2小时/天"},
        metadata={"type": "preferences"}
    )
    
    current_task = memory_manager.get_from_scratch_pad("current_task")
    learning_progress = memory_manager.get_from_scratch_pad("learning_progress")
    user_preferences = memory_manager.get_from_scratch_pad("user_preferences")
    
    print(f"当前任务: {current_task}")
    print(f"学习进度: {learning_progress}")
    print(f"用户偏好: {user_preferences}")
    
    print("\n9. 统一搜索所有记忆...")
    
    unified_results = memory_manager.search_all_memories(
        query="学习",
        memory_types=["vector", "rolling", "scratch"],
        limit_per_type=2
    )
    
    print("统一搜索结果:")
    for memory_type, results in unified_results.items():
        if "error" not in results:
            print(f"  {memory_type}: {len(results['memories'])} 个结果")
            for i, memory in enumerate(results['memories'][:2]):
                if memory_type == "vector":
                    print(f"    {i+1}. {memory['content'][:40]}... (相似度: {memory['score']:.3f})")
                elif memory_type == "rolling":
                    print(f"    {i+1}. [{memory.get('role', 'unknown')}]: {memory['content'][:40]}...")
                elif memory_type == "scratch":
                    print(f"    {i+1}. {memory['key']}: {memory['value']}")
        else:
            print(f"  {memory_type}: 错误 - {results['error']}")
    
    print("\n10. 获取记忆统计...")
    
    summary = memory_manager.get_memory_summary()
    print("记忆统计:")
    print(f"  总记忆数: {summary['overview']['total_memories']}")
    print(f"  向量记忆: {summary['vector_memory']['count']}")
    print(f"  滚动窗口: {summary['rolling_window']['count']}")
    print(f"  工作记忆: {summary['scratch_pad']['count']}")
    print(f"  内存使用: {summary['overview']['memory_usage_bytes']} 字节")
    
    print("\n11. 记忆管理...")
    
    cleanup_stats = memory_manager.cleanup_all_memories()
    print(f"清理统计:")
    print(f"  向量清理: {cleanup_stats['vector_cleaned']}")
    print(f"  滚动清理: {cleanup_stats['rolling_cleaned']}")
    print(f"  工作清理: {cleanup_stats['scratch_cleaned']}")
    
    export_data = memory_manager.export_memories(
        memory_types=["rolling", "scratch"],
        include_metadata=True
    )
    print(f"导出记忆: {len(export_data['memories'])} 种类型")
    
    return True

def main():
    """主函数"""
    print("ChromaDB Memory 完整使用指南")
    print("=" * 50)
    
    success = demo_chromadb_memory_usage()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: ChromaDB Memory使用指南演示完成！")
        print("\n关键调用方法总结:")
        print("1. 添加记忆: memory_manager.add_to_vector_memory()")
        print("2. 搜索记忆: memory_manager.search_vector_memory()")
        print("3. 更新记忆: memory_manager.update_vector_memory()")
        print("4. 删除记忆: memory_manager.delete_vector_memory()")
        print("5. 统一搜索: memory_manager.search_all_memories()")
        print("6. 获取统计: memory_manager.get_memory_summary()")
    else:
        print("ERROR: 演示失败，请检查ChromaDB安装")

if __name__ == "__main__":
    main()
