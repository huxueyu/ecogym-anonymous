import re
import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

def load_metadata_info(folder_path):
    meta_path = os.path.join(folder_path, 'metadata.json')

    try:
        if not os.path.exists(meta_path):
            return "Metadata file not found."

        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        config = meta.get('config', {})

        model_config = config.get('full_config', {}).get('model_config', {})
        agent_model = model_config.get('model_name', 'Unknown')
        memory_model = model_config.get('env_model_name', 'Unknown')

        system_defaults = config.get('full_config', {}).get('system_config', {}).get('defaults', {})

        voting_models = system_defaults.get('initial_voting_models', [])
        if isinstance(voting_models, list):
            voting_str = ", ".join(voting_models)
        else:
            voting_str = str(voting_models)

        settle_agent = system_defaults.get('agent_model', 'Unknown')
        settle_system = system_defaults.get('system_model', 'Unknown')

        info_str = (
            f"Agent Model: {agent_model}\n"
            f"Memory Model: {memory_model}\n"
            f"Pricing Models (Voting): [{voting_str}]\n"
            f"Settlement Models: Agent({settle_agent}) vs System({settle_system})"
        )

        return info_str

    except Exception as e:
        print(f"读取 metadata.json 出错: {e}")
        return f"Error loading metadata: {e}"

def parse_log_file(file_path):
    tool_counts = Counter()

    pattern = re.compile(r"\[Tool Call\]\s+(.*?)\s+with args:\s*")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"正在分析 {len(lines)} 行日志...")

        for line in lines:
            if "[Tool Call]" in line:
                match = pattern.search(line)
                if match:
                    tool_name = match.group(1).strip()
                    tool_counts[tool_name] += 1

        return tool_counts

    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 '{file_path}'")
        return None
    except Exception as e:
        print(f"❌ 读取文件时发生错误：{e}")
        return None

def plot_tool_usage(tool_counts, output_path, model_info_text):
    if not tool_counts:
        print("⚠️ 没有找到任何工具调用记录，无法绘图。")
        return

    df = pd.DataFrame(list(tool_counts.items()), columns=['Tool Name', 'Count'])
    df = df.sort_values(by='Count', ascending=False)

    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(max(10, len(df) * 0.8), 8))

    plt.subplots_adjust(top=0.75)

    barplot = sns.barplot(x='Tool Name', y='Count', data=df, palette="viridis", hue='Tool Name', legend=False)

    for container in barplot.containers:
        barplot.bar_label(container, padding=3)

    ax = plt.gca()

    ax.text(
        0.0, 1.12,
        model_info_text,
        transform=ax.transAxes,
        fontsize=10,
        fontfamily='monospace',
        verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor='#dee2e6', alpha=0.9)
    )

    plt.title('Tool Usage Statistics', fontsize=16, y=1.15, fontweight='bold')

    plt.xlabel('Tool Name', fontsize=12)
    plt.ylabel('Call Count', fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=10)

    save_file = os.path.join(output_path, 'tool_call.png')
    plt.savefig(save_file, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"✅ 绘图完成，已保存至: {save_file}")

def main():
    while True:
        file_path = input("\n请输入日志文件夹路径（默认查找该路径下的 detailed.log）: ").strip()
        file_path = file_path.replace('"', '').replace("'", "")
        if file_path:
            break
        print("路径不能为空，请重新输入。")

    print("-" * 30)
    print("正在提取 Metadata...")
    model_info = load_metadata_info(file_path)
    print("提取内容预览:")
    print(model_info)
    print("-" * 30)

    logpath = os.path.join(file_path, 'detailed.log')
    counts = parse_log_file(logpath)

    if counts:
        print(f"\n统计结果: 共发现 {len(counts)} 种工具，总计调用 {sum(counts.values())} 次。")
        plot_tool_usage(counts, file_path, model_info)

if __name__ == "__main__":
    main()