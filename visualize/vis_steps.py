import json
from typing import Dict, Any, Optional

filename = '/root/repo/open-vending-bench/logs/sessions/partjob_bench_20251230_202707/steps.jsonl'

def remove_all_tasks_db(data: Any) -> Any:
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key != 'all_tasks_db':
                result[key] = remove_all_tasks_db(value)
        return result
    elif isinstance(data, list):
        return [remove_all_tasks_db(item) for item in data]
    else:
        return data

def read_line_number(filename: str, line_num: int) -> Optional[Dict[str, Any]]:
    if line_num < 1:
        print(f"错误：行号必须大于0，当前输入：{line_num}")
        return None

    current_line = 0

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                current_line += 1

                if current_line == line_num:
                    line = line.strip()

                    if not line:
                        print(f"第 {line_num} 行为空行")
                        return None

                    try:
                        data = json.loads(line)
                        processed_data = remove_all_tasks_db(data)
                        return processed_data
                    except json.JSONDecodeError as e:
                        print(f"第 {line_num} 行JSON解析失败: {e}")
                        print(f"行内容（前200字符）: {line[:200]}")
                        return None

        print(f"文件只有 {current_line} 行，无法读取第 {line_num} 行")
        return None

    except FileNotFoundError:
        print(f"文件未找到: {filename}")
        return None
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return None

target_line = 675
print(f"正在读取第 {target_line} 行数据...")
result = read_line_number(filename, target_line)

if result:
    print(f"\n第 {target_line} 行数据:")
    print("=" * 60)

    print(result['step'])
    print(result['tools_called'])
    print(result['messages'])

    print("=" * 60)

    print(f"\n数据基本信息:")
    print(f"数据类型: {type(result)}")

    if isinstance(result, dict):
        print(f"字典包含的键: {list(result.keys())}")
        for key in ['step', 'timestamp', 'type', 'action', 'thought']:
            if key in result:
                value = result[key]
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {value}")

    json_str = json.dumps(result)
    print(f"\n数据大小: {len(json_str)} 字符")

else:
    print(f"未能成功读取第 {target_line} 行数据")