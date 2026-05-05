import os
import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import glob

def load_jsonl(file_path):
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    except FileNotFoundError:
        print(f"提示: 找不到日志文件 {file_path}")
        return None
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None

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

def plot_chart(df, x_col, x_label, title, output_file, model_info_text, is_step_trace=False, show_plot=False):
    if df.empty:
        print(f"数据为空，跳过绘图: {title}")
        return

    fig, ax1 = plt.subplots(figsize=(14, 9))

    plt.subplots_adjust(top=0.80)

    x = df[x_col]

    ax1.set_xlabel(x_label, fontsize=12, fontweight='bold')
    ax1.set_ylabel('Status (0-100)', color='black', fontsize=12, fontweight='bold')

    line1, = ax1.plot(x, df['energy'], label='Energy', color='green', linewidth=2, alpha=0.8)
    line2, = ax1.plot(x, df['stress'], label='Stress', color='red', linewidth=2, linestyle='--', alpha=0.8)

    lines = [line1, line2]

    if is_step_trace and 'skill_rating' in df.columns:
        line3, = ax1.plot(x, df['skill_rating'], label='Skill Rating', color='purple', linestyle='-.', linewidth=1.5)
        lines.append(line3)

    ax1.tick_params(axis='y', labelcolor='black')
    ax1.grid(True, linestyle=':', alpha=0.6)

    ax2 = ax1.twinx()
    ax2.set_ylabel('Money ($)', color='blue', fontsize=12, fontweight='bold')
    line_money, = ax2.plot(x, df['money'], label='Money', color='blue', linewidth=2.5)
    ax2.tick_params(axis='y', labelcolor='blue')

    lines.append(line_money)

    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', bbox_to_anchor=(0, 1.0), frameon=True, shadow=True, ncol=4)

    fig.suptitle(title, fontsize=18, fontweight='bold', y=0.97)

    ax1.text(
        0.0, 1.02,
        model_info_text,
        transform=ax1.transAxes,
        fontsize=10,
        fontfamily='monospace',
        verticalalignment='bottom',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor='#dee2e6', alpha=0.9)
    )

    if output_file:
        plt.savefig(output_file, bbox_inches='tight', dpi=150)
        print(f"已保存图表: {output_file}")

    if show_plot:
        plt.show()

    plt.close()

def process_daily_trace(folder_path, model_info_text, output_file=None, show_plot=False):
    file_path = os.path.join(folder_path, 'daily_trace.jsonl')
    data = load_jsonl(file_path)
    if not data:
        print(f"daily_trace.jsonl 数据为空或不存在: {file_path}")
        return

    parsed = []
    for entry in data:
        summary = entry.get('summary', {})
        skill_rating_dict = summary.get('skill_rating', {})

        if isinstance(skill_rating_dict, dict) and skill_rating_dict:
            skill = sum(skill_rating_dict.values()) / len(skill_rating_dict)
        else:
            skill = 0

        parsed.append({
            'day': entry.get('day'),
            'money': summary.get('money', 0),
            'stress': summary.get('stress', 0),
            'energy': summary.get('energy', 0),
            'skill_rating': skill
        })

    df = pd.DataFrame(parsed)

    if output_file is None:
        output_file = os.path.join(folder_path, 'daily_trace.png')

    plot_chart(df, 'day', 'Day', 'Daily Trace Analysis', output_file, model_info_text, is_step_trace=True, show_plot=show_plot)

def process_state_trace(folder_path, model_info_text, output_file=None, show_plot=False):
    file_path = os.path.join(folder_path, 'state_trace.jsonl')
    data = load_jsonl(file_path)
    if not data:
        print(f"state_trace.jsonl 数据为空或不存在: {file_path}")
        return

    parsed = []
    for entry in data:
        state = entry.get('state', {})
        skill_rating_dict = state.get('skill_rating', {})

        if isinstance(skill_rating_dict, dict) and skill_rating_dict:
            skill = sum(skill_rating_dict.values()) / len(skill_rating_dict)
        else:
            skill = 0

        parsed.append({
            'step': entry.get('step'),
            'money': state.get('money', 0),
            'stress': state.get('stress', 0),
            'energy': state.get('energy', 0),
            'skill_rating': skill
        })

    df = pd.DataFrame(parsed)

    if output_file is None:
        output_file = os.path.join(folder_path, 'state_trace.png')

    plot_chart(df, 'step', 'Step', 'State Trace Analysis', output_file, model_info_text, is_step_trace=True, show_plot=show_plot)

def visualize_session(session_dir, mode='day', output_file=None, show_plot=False):
    print(f"处理session: {os.path.basename(session_dir)}")
    print("-" * 30)

    model_info = load_metadata_info(session_dir)
    print("模型配置信息:")
    print(model_info)
    print("-" * 30)

    if mode == 'day':
        process_daily_trace(session_dir, model_info, output_file, show_plot)
    elif mode == 'step':
        process_state_trace(session_dir, model_info, output_file, show_plot)
    else:
        print(f"未知模式: {mode}")

def main():
    parser = argparse.ArgumentParser(description='可视化session日志数据')

    parser.add_argument('--sessions', nargs='+', help='要可视化的session IDs')
    parser.add_argument('--mode', choices=['day', 'step'], default='day',
                       help='可视化模式: day(天) 或 step(步骤)')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--show', action='store_true',
                       help='显示交互式图表')
    parser.add_argument('--logs-dir', default='logs',
                       help='logs目录路径 (默认: logs)')

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

        visualize_session(session_dir, args.mode, output_file, args.show)

    print("\n全部完成！")

if __name__ == "__main__":
    main()
