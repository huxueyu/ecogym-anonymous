import os
import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"提示: 找不到文件 {file_path}")
        return None
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None

def load_metadata_info(folder_path):
    meta_path = os.path.join(folder_path, 'metadata.json')
    try:
        if not os.path.exists(meta_path):
            return "Metadata not found"
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        config = meta.get('config', {})
        full_config = config.get('full_config', {})

        model_name = config.get('model_name', 'Unknown')
        run_settings = full_config.get('run_settings', {})
        max_days = run_settings.get('max_days', 'Unknown')
        max_actions = run_settings.get('max_actions_per_day', 1)

        return f"Model: {model_name} | Settings: {max_days} Days, {max_actions} Actions/Day"
    except:
        return "Error loading metadata"

def load_tool_calls_data(session_dir):
    steps_file = os.path.join(session_dir, 'steps.jsonl')
    metadata_file = os.path.join(session_dir, 'metadata.json')

    metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    if not os.path.exists(steps_file):
        print(f"未找到 steps.jsonl: {steps_file}")
        return [], {}, metadata

    day_tool_counts = {}

    with open(steps_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    step_data = json.loads(line)

                    state = step_data.get('state_after') or step_data.get('state_before')

                    if state and 'day' in state:
                        day = state['day']

                        tools_called = step_data.get('tools_called', [])
                        if isinstance(tools_called, list):
                            if day not in day_tool_counts:
                                day_tool_counts[day] = {}

                            for tool_call in tools_called:
                                tool_name = tool_call.get('tool_name')
                                if tool_name:
                                    if tool_name not in day_tool_counts[day]:
                                        day_tool_counts[day][tool_name] = 0
                                    day_tool_counts[day][tool_name] += 1
                except Exception as e:
                    print(f"解析 step 数据时出错: {e}")
                    continue

    all_tool_names = set()
    for day_counts in day_tool_counts.values():
        all_tool_names.update(day_counts.keys())
    all_tool_names = sorted(all_tool_names)

    days = sorted(day_tool_counts.keys())
    tool_calls_by_type = {tool_name: [] for tool_name in all_tool_names}

    cumulative_counts = {tool_name: 0 for tool_name in all_tool_names}

    for day in days:
        day_counts = day_tool_counts.get(day, {})
        for tool_name in all_tool_names:
            cumulative_counts[tool_name] += day_counts.get(tool_name, 0)
            tool_calls_by_type[tool_name].append(cumulative_counts[tool_name])

    return days, tool_calls_by_type, metadata

def get_y_limits(series, padding=0.1):
    if series.empty:
        return 0, 1

    y_min = series.min()
    y_max = series.max()
    diff = y_max - y_min

    if diff == 0:
        diff = y_max * 0.1 if y_max != 0 else 1.0

    lower = y_min - (diff * padding)
    upper = y_max + (diff * padding)

    lower = max(0, lower)
    return lower, upper

def plot_dynamic_metrics(df, output_file, model_info_text, show_plot=False):
    if df.empty:
        print("数据为空，跳过绘图")
        return

    fig, axs = plt.subplots(2, 2, figsize=(20, 12))

    plt.subplots_adjust(top=0.90, hspace=0.3, wspace=0.2)

    x = df['day']

    metrics_config = [
        {
            "ax": axs[0, 0],
            "col": "dau",
            "title": "Daily Active Users (DAU)",
            "ylabel": "Users",
            "color": "#1f77b4",
            "fill": True
        },
        {
            "ax": axs[0, 1],
            "col": "content_volume",
            "title": "Content Volume",
            "ylabel": "Total Content",
            "color": "#2ca02c",
            "fill": True
        },
        {
            "ax": axs[1, 0],
            "col": "retention_rate",
            "title": "Retention Rate",
            "ylabel": "Rate",
            "color": "#d62728",
            "fill": False
        },
        {
            "ax": axs[1, 1],
            "col": "content_quality",
            "title": "Content Quality Score",
            "ylabel": "Score",
            "color": "#ff7f0e",
            "fill": False
        }
    ]

    for item in metrics_config:
        ax = item["ax"]
        col = item["col"]
        data = df[col]

        lower, upper = get_y_limits(data, padding=0.15)

        ax.plot(x, data, color=item["color"], linewidth=2.5, label=item["title"])

        if item["fill"]:
            ax.fill_between(x, data, y2=lower, color=item["color"], alpha=0.1)

        ax.set_ylim(lower, upper)

        ax.set_title(item["title"], fontsize=14, fontweight='bold', color=item["color"])
        ax.set_ylabel(item["ylabel"], fontsize=11)
        ax.grid(True, linestyle=':', alpha=0.6)

        last_val = data.iloc[-1]
        ax.text(x.iloc[-1], last_val, f"{last_val:.2f}",
                color=item["color"], fontweight='bold', ha='left', va='center')

    axs[1, 0].set_xlabel('Day', fontsize=12)
    axs[1, 1].set_xlabel('Day', fontsize=12)

    last_day = df.iloc[-1]['day']
    last_dau = df.iloc[-1]['dau']

    fig.suptitle(f'Operation Benchmark: Dynamic Analysis (Day {last_day} | DAU: {last_dau})',
                 fontsize=20, fontweight='bold', y=0.96)

    fig.text(0.5, 0.92, model_info_text, ha='center', fontsize=12, fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', alpha=0.8))

    if output_file:
        plt.savefig(output_file, bbox_inches='tight', dpi=150)
        print(f"已保存动态图表: {output_file}")

    if show_plot:
        plt.show()

    plt.close()

def plot_tool_calls(days, tool_calls_by_type, output_file, model_info_text, show_plot=False):
    if not days or not tool_calls_by_type:
        print("工具调用数据为空，跳过绘图")
        return

    fig, ax = plt.subplots(figsize=(14, 8))

    line_styles = ['-', '--', '-.', ':', '-', '--']
    markers = ['o', 's', '^', 'v', 'D', 'p', '*', 'h']
    colors = plt.cm.tab10(range(len(tool_calls_by_type)))

    tool_names = sorted(tool_calls_by_type.keys())
    for idx, tool_name in enumerate(tool_names):
        tool_counts = tool_calls_by_type[tool_name]

        linestyle = line_styles[idx % len(line_styles)]
        marker = markers[idx % len(markers)]
        color = colors[idx % len(colors)]

        ax.plot(days, tool_counts, marker=marker, markersize=4,
               linewidth=2.5, alpha=0.8, color=color, linestyle=linestyle,
               label=tool_name)

        if tool_counts and tool_counts[-1] > 0:
            ax.scatter(days[0], tool_counts[0], color=color,
                     s=80, marker=marker, edgecolors='black', linewidths=1.5, zorder=5, alpha=0.8)
            ax.scatter(days[-1], tool_counts[-1], color=color,
                     s=80, marker=marker, edgecolors='black', linewidths=1.5, zorder=5, alpha=0.8)

            ax.text(days[-1], tool_counts[-1], f" {tool_counts[-1]}",
                   color=color, fontweight='bold', ha='left', va='center', fontsize=9)

    ax.set_title('Operation Benchmark: Tool Calls by Type', fontsize=16, fontweight='bold')
    ax.set_xlabel('Day', fontsize=14)
    ax.set_ylabel('Cumulative Tool Calls', fontsize=14)
    ax.grid(True, alpha=0.3, linestyle='--')

    if len(tool_names) <= 8:
        ax.legend(loc='best', fontsize=10, framealpha=0.9)
    else:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, framealpha=0.9)
        plt.tight_layout()

    fig.text(0.5, 0.92, model_info_text, ha='center', fontsize=11, fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', alpha=0.8),
             transform=fig.transFigure)

    note_text = 'Cumulative count of tool calls by type'
    ax.text(0.5, -0.12, note_text, transform=ax.transAxes,
           fontsize=10, ha='center', style='italic', color='gray')

    plt.subplots_adjust(top=0.88)

    if output_file:
        plt.savefig(output_file, bbox_inches='tight', dpi=150)
        print(f"已保存工具调用图表: {output_file}")

    if show_plot:
        plt.show()

    plt.close()

def process_session(session_dir, output_file=None, show_plot=False, plot_tools=True, skip_metrics=False):
    model_info = load_metadata_info(session_dir)

    if not skip_metrics:
        state_file = os.path.join(session_dir, 'state.json')
        state_data = load_json(state_file)

        if not state_data or 'state' not in state_data or 'dau_history' not in state_data['state']:
            print(f"跳过 {session_dir}: state.json 中缺少 dau_history")
        else:
            df = pd.DataFrame(state_data['state']['dau_history'])

            for col in ['dau', 'content_volume', 'content_quality', 'retention_rate']:
                if col not in df.columns: df[col] = 0

            if output_file is None:
                output_file = os.path.join(session_dir, 'operation_metrics_dynamic.png')

            plot_dynamic_metrics(df, output_file, model_info, show_plot)

    if plot_tools:
        days, tool_calls_by_type, _ = load_tool_calls_data(session_dir)
        if days and tool_calls_by_type:
            tool_output_file = os.path.join(session_dir, 'operation_tool_calls.png')
            plot_tool_calls(days, tool_calls_by_type, tool_output_file, model_info, show_plot)

def get_latest_session_id(logs_dir="logs"):
    sessions_dir = os.path.join(logs_dir, "sessions")
    if not os.path.exists(sessions_dir): return None
    session_dirs = [d for d in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, d))]
    if not session_dirs: return None
    session_dirs.sort(key=lambda x: os.path.getctime(os.path.join(sessions_dir, x)), reverse=True)
    return session_dirs[0]

def main():
    parser = argparse.ArgumentParser(
        description='Visualize operation bench session data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vis_operation.py

  python vis_operation.py --metrics-only

  python vis_operation.py --tools-only

  python vis_operation.py --all

  python vis_operation.py --show
        """
    )
    parser.add_argument('--sessions', '-s', nargs='+', help='指定要可视化的 session 名称')
    parser.add_argument('--output', help='输出文件路径（用于指标图）')
    parser.add_argument('--show', action='store_true', help='显示交互式图表')
    parser.add_argument('--logs-dir', default='logs', help='日志目录路径')
    parser.add_argument('--metrics-only', action='store_true', help='只生成指标图（跳过工具调用图）')
    parser.add_argument('--tools-only', action='store_true', help='只生成工具调用图（跳过指标图）')
    parser.add_argument('--all', action='store_true', help='可视化所有 operation bench sessions')
    args = parser.parse_args()

    target_sessions = []
    if args.sessions:
        for s in args.sessions:
            p = os.path.join(args.logs_dir, "sessions", s)
            if os.path.exists(p): target_sessions.append(p)
    elif args.all:
        sessions_dir = os.path.join(args.logs_dir, "sessions")
        if os.path.exists(sessions_dir):
            for item in os.listdir(sessions_dir):
                item_path = os.path.join(sessions_dir, item)
                if os.path.isdir(item_path) and item.startswith('operation_bench'):
                    target_sessions.append(item_path)
            target_sessions.sort(key=lambda x: os.path.getctime(x), reverse=True)
    else:
        latest = get_latest_session_id(args.logs_dir)
        if latest: target_sessions.append(os.path.join(args.logs_dir, "sessions", latest))

    if not target_sessions:
        print("未找到有效 session")
        return

    for i, s_dir in enumerate(target_sessions):
        print(f"\n处理 session: {os.path.basename(s_dir)}")

        plot_tools = not args.metrics_only
        skip_metrics = args.tools_only

        out = args.output
        if out and len(target_sessions) > 1:
            base, ext = os.path.splitext(out)
            out = f"{base}_{i+1}{ext}"

        process_session(s_dir, out, args.show, plot_tools=plot_tools, skip_metrics=skip_metrics)

    print("\n完成。")

if __name__ == "__main__":
    main()