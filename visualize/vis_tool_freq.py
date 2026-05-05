import re
import os
import sys
import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from datetime import datetime
import glob

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

def get_latest_session_id(logs_dir="logs"):
    sessions_dir = os.path.join(logs_dir, "sessions")
    if not os.path.exists(sessions_dir):
        return None

    session_dirs = [d for d in os.listdir(sessions_dir)
                   if os.path.isdir(os.path.join(sessions_dir, d))]

    if not session_dirs:
        return None

    session_dirs.sort(key=lambda x: os.path.getctime(os.path.join(sessions_dir, x)), reverse=True)
    return session_dirs[0]

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

def plot_tool_usage(tool_counts, output_path, model_info_text, show_plot=False, output_file=None):
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

    if output_file is None:
        save_file = os.path.join(output_path, 'tool_call.png')
    else:
        save_file = output_file

    if output_path or output_file:
        plt.savefig(save_file, bbox_inches='tight', dpi=150)
        print(f"✅ 绘图完成，已保存至: {save_file}")

    if show_plot:
        plt.show()

    plt.close()

def process_session(session_dir, output_file=None, show_plot=False):
    print(f"\n处理session: {os.path.basename(session_dir)}")
    print("-" * 30)

    print("正在提取 Metadata...")
    model_info = load_metadata_info(session_dir)
    print("提取内容预览:")
    print(model_info)
    print("-" * 30)

    logpath = os.path.join(session_dir, 'detailed.log')
    if not os.path.exists(logpath):
        print(f"⚠️ 找不到 detailed.log 文件: {logpath}")
        return

    counts = parse_log_file(logpath)

    if counts:
        print(f"\n统计结果: 共发现 {len(counts)} 种工具，总计调用 {sum(counts.values())} 次。")
        plot_tool_usage(counts, session_dir, model_info, show_plot, output_file)

def main():
    parser = argparse.ArgumentParser(description='分析session日志中的工具调用统计')

    parser.add_argument('--sessions', nargs='+', help='要分析的session IDs')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--show', action='store_true',
                       help='显示交互式图表')
    parser.add_argument('--logs-dir', default='logs',
                       help='logs目录路径 (默认: logs)')
    parser.add_argument('--log-file', default='detailed.log',
                       help='日志文件名 (默认: detailed.log)')

    args = parser.parse_args()

    sessions_to_process = []

    if args.sessions:
        for session_id in args.sessions:
            session_dir = os.path.join(args.logs_dir, "sessions", session_id)
            if os.path.exists(session_dir):
                sessions_to_process.append(session_dir)
            else:
                print(f"警告: session目录不存在: {session_dir}")
    else:
        latest_session = get_latest_session_id(args.logs_dir)
        if latest_session:
            session_dir = os.path.join(args.logs_dir, "sessions", latest_session)
            sessions_to_process.append(session_dir)
            print(f"使用最新session: {latest_session}")
        else:
            print("错误: 找不到任何session目录")
            return

    if not sessions_to_process:
        print("错误: 没有有效的session可以处理")
        return

    for i, session_dir in enumerate(sessions_to_process):
        print(f"\n处理session {i+1}/{len(sessions_to_process)}")

        output_file = None
        if args.output:
            if len(sessions_to_process) > 1:
                name, ext = os.path.splitext(args.output)
                output_file = f"{name}_{i+1}{ext}"
            else:
                output_file = args.output

        process_session(session_dir, output_file, args.show)

    print("\n✅ 全部完成！")

if __name__ == "__main__":
    main()
