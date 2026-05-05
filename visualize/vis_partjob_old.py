import os
import json
import pandas as pd
import matplotlib.pyplot as plt

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

def plot_chart(df, x_col, x_label, title, output_file, model_info_text, is_step_trace=False):
    if df.empty:
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

    plt.savefig(output_file, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"已保存图表: {output_file}")

def process_daily_trace(folder_path, model_info_text):
    file_path = os.path.join(folder_path, 'daily_trace.jsonl')
    data = load_jsonl(file_path)
    if not data: return

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
    output_path = os.path.join(folder_path, 'daily_trace.png')
    plot_chart(df, 'day', 'Day', 'Daily Trace Analysis', output_path, model_info_text, is_step_trace=True)

def process_state_trace(folder_path, model_info_text):
    file_path = os.path.join(folder_path, 'state_trace.jsonl')
    data = load_jsonl(file_path)
    if not data: return

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
    output_path = os.path.join(folder_path, 'state_trace.png')
    plot_chart(df, 'step', 'Step', 'State Trace Analysis', output_path, model_info_text, is_step_trace=True)

def main():
    log_dir = input("请输入日志文件夹路径: ").strip()
    log_dir = log_dir.replace('"', '').replace("'", "")

    if not os.path.exists(log_dir):
        print("错误: 路径不存在。")
        return

    print("-" * 30)
    print("正在提取 Metadata...")
    model_info = load_metadata_info(log_dir)
    print("提取内容预览:")
    print(model_info)
    print("-" * 30)

    process_daily_trace(log_dir, model_info)
    process_state_trace(log_dir, model_info)

    print("全部完成！")

if __name__ == "__main__":
    main()