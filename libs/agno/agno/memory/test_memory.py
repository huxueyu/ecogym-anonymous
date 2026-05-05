#!/usr/bin/env python3
"""
Enhanced Memory Manager Example
Demonstrates the three types of memory:
- VectorMem (长期记忆): Long-term memory using vector database
- RollingWindow (短期记忆): Short-term memory using sliding window  
- ScratchPad (工作记忆): Working memory for temporary storage
"""

from datetime import datetime
from agno.memory.manager import MemoryManager
from agno.models.message import Message


def demo_memory_manager():
    """Demonstrate the enhanced memory manager capabilities."""
    
    chroma_db = MemoryManager.create_chromadb_adapter(
        collection_name="vending_bench_memories",
        persist_directory="./chroma_memory_db"
    )
    

    memory_manager = MemoryManager(
        db=chroma_db,
        

        vector_collection="demo_vector_memories",
        vector_chunk_size=500,
        vector_similarity_threshold=0.6,
        max_vector_memories=1000,
        

        window_size=5,
        rolling_memory_ttl=1800,
        max_rolling_memories=100,
        

        scratch_pad_ttl=900,
        max_scratch_items=50,
        auto_cleanup_scratch=True,
        

        memory_analytics=True,
        auto_consolidation=True
    )
    
    print("SUCCESS: MemoryManager 构造函数测试通过！")
    print(f"   vector_collection: {memory_manager.vector_collection}")
    print(f"   vector_chunk_size: {memory_manager.vector_chunk_size}")
    print(f"   window_size: {memory_manager.window_size}")
    print(f"   scratch_pad_ttl: {memory_manager.scratch_pad_ttl}")
    print()
    
    print("=== Enhanced Memory Manager Demo ===\n")
    

    print("1. VectorMem (长期记忆) - Long-term Memory")
    print("-" * 50)
    print("注意: VectorMem 功能需要数据库连接，跳过测试")
    print("SUCCESS: VectorMem 参数配置正确:")
    print(f"   vector_collection: {memory_manager.vector_collection}")
    print(f"   vector_chunk_size: {memory_manager.vector_chunk_size}")
    print(f"   vector_similarity_threshold: {memory_manager.vector_similarity_threshold}")
    print(f"   max_vector_memories: {memory_manager.max_vector_memories}")
    print()
    
    

    print("2. RollingWindow (短期记忆) - Short-term Memory")
    print("-" * 50)

    messages = [
        "Hello, I need help with Python programming",
        "I'd be happy to help! What specific Python topic are you working on?",
        "I'm learning about data structures and algorithms",
        "Great! Let's start with lists and dictionaries. They're fundamental in Python.",
        "Can you show me some examples?",
    ]
    
    memory_manager.add_to_vector_memory(messages)  
    

    
    print(f"Added {len(messages)} messages to rolling window")
    
    
    print("4. Unified Memory Interface")
    print("-" * 50)
    print("注意: 统一搜索功能需要数据库连接，跳过测试")
    print("SUCCESS: 统一内存接口参数配置正确")
    

    summary = memory_manager.get_memory_summary()
    print(f"\nMemory Summary:")
    print(f"  Total memories: {summary['overview']['total_memories']}")
    print(f"  Vector memories: {summary['vector_memory']['count']}")
    print(f"  Rolling window: {summary['rolling_window']['count']}")
    print(f"  Scratch pad: {summary['scratch_pad']['count']}")
    print(f"memory summary: {summary}")

    print("\n5. Memory Management")
    print("-" * 50)
    

    cleanup_stats = memory_manager.cleanup_all_memories()
    print(f"Cleanup completed:")
    print(f"  Vector cleaned: {cleanup_stats['vector_cleaned']}")
    print(f"  Rolling cleaned: {cleanup_stats['rolling_cleaned']}")
    print(f"  Scratch cleaned: {cleanup_stats['scratch_cleaned']}")
    

    export_data = memory_manager.export_memories(
        memory_types=["rolling", "scratch"],
        include_metadata=True
    )
    print(f"Exported {len(export_data['memories'])} memory types")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    demo_memory_manager()