

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime


class SessionVisualizer:

    def __init__(self, sessions_dir: str = "./logs/sessions"):
        self.sessions_dir = Path(sessions_dir)
        if not self.sessions_dir.exists():
            raise ValueError(f"Sessions directory not found: {sessions_dir}")

    def get_all_sessions(self) -> List[str]:
        sessions = []
        for item in self.sessions_dir.iterdir():
            if item.is_dir() and (item / "steps.jsonl").exists():
                sessions.append(item.name)
        return sorted(sessions, reverse=True)

    def get_latest_session(self) -> Optional[str]:
        sessions = self.get_all_sessions()
        return sessions[0] if sessions else None

    def load_session_data(self, session_name: str) -> Tuple[List[int], List[float], Dict]:
        session_path = self.sessions_dir / session_name
        steps_file = session_path / "steps.jsonl"
        metadata_file = session_path / "metadata.json"

        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        is_operation_bench = session_name.startswith('operation_bench')
        is_vending_bench = session_name.startswith('vending_bench')
        is_partjob_bench = session_name.startswith('partjob_bench')
        metric_key = 'dau' if is_operation_bench else 'money'

        if is_operation_bench:
            metadata['_bench_type'] = 'operation'
        elif is_vending_bench:
            metadata['_bench_type'] = 'vending'
        elif is_partjob_bench:
            metadata['_bench_type'] = 'partjob'
        else:
            metadata['_bench_type'] = 'unknown'

        days = []
        metric_values = []
        seen_states = set()

        with open(steps_file, 'r') as f:
            for line in f:
                if line.strip():
                    step_data = json.loads(line)

                    state = step_data.get('state_after') or step_data.get('state_before')

                    if state and 'day' in state and metric_key in state:
                        day = state['day']
                        metric_value = state[metric_key]

                        state_key = (day, round(metric_value, 2))
                        if state_key not in seen_states:
                            seen_states.add(state_key)
                            days.append(day)
                            metric_values.append(metric_value)

        metadata['_metric_key'] = metric_key
        metadata['_is_operation_bench'] = is_operation_bench

        return days, metric_values, metadata

    def load_session_data_by_step(self, session_name: str) -> Tuple[List[int], List[float], List[int], Dict]:
        session_path = self.sessions_dir / session_name
        steps_file = session_path / "steps.jsonl"
        metadata_file = session_path / "metadata.json"

        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        is_operation_bench = session_name.startswith('operation_bench')
        is_vending_bench = session_name.startswith('vending_bench')
        is_partjob_bench = session_name.startswith('partjob_bench')
        metric_key = 'dau' if is_operation_bench else 'money'

        if is_operation_bench:
            metadata['_bench_type'] = 'operation'
        elif is_vending_bench:
            metadata['_bench_type'] = 'vending'
        elif is_partjob_bench:
            metadata['_bench_type'] = 'partjob'
        else:
            metadata['_bench_type'] = 'unknown'

        steps = []
        metric_values = []
        day_values = []

        with open(steps_file, 'r') as f:
            for line in f:
                if line.strip():
                    step_data = json.loads(line)

                    state = step_data.get('state_after') or step_data.get('state_before')
                    step_num = step_data.get('step', 0)

                    if state and metric_key in state and step_num > 0:
                        metric_value = state[metric_key]
                        day = state.get('day', 0)
                        steps.append(step_num)
                        metric_values.append(metric_value)
                        day_values.append(day)

        metadata['_metric_key'] = metric_key
        metadata['_is_operation_bench'] = is_operation_bench

        return steps, metric_values, day_values, metadata

    def plot_sessions(
        self,
        session_names: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        show: bool = False,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 7),
        all_sessions: bool = False
    ) -> None:
        if session_names is None:
            if all_sessions:
                session_names = self.get_all_sessions()
            else:
                latest = self.get_latest_session()
                session_names = [latest] if latest else []

        if not session_names:
            print("No sessions found to visualize.")
            return

        plt.figure(figsize=figsize)

        colors = plt.cm.tab10(range(len(session_names)))

        metric_key = None
        metric_label = None
        plot_title = None

        def create_short_label(session_name: str, metadata: Dict) -> str:
            parts = session_name.split('_')
            if len(parts) >= 3:
                date_part = parts[-2] if len(parts) >= 2 else ''
                time_part = parts[-1] if len(parts) >= 1 else ''
                if len(date_part) == 8 and len(time_part) >= 6:
                    formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    formatted_time = f"{time_part[:2]}:{time_part[2:4]}"
                    short_name = f"{formatted_date} {formatted_time}"
                else:
                    short_name = session_name[-20:] if len(session_name) > 20 else session_name
            else:
                short_name = session_name[-20:] if len(session_name) > 20 else session_name

            if metadata.get('config', {}).get('model_name'):
                model = metadata['config']['model_name']
                if len(model) > 15:
                    model = model[:12] + "..."
                return f"{short_name} ({model})"
            return short_name

        for idx, session_name in enumerate(session_names):
            try:
                days, metric_values, metadata = self.load_session_data(session_name)

                if not days:
                    print(f"Warning: No data found for session {session_name}")
                    continue

                if metric_key is None:
                    metric_key = metadata.get('_metric_key', 'money')
                    bench_type = metadata.get('_bench_type', 'unknown')
                    is_operation_bench = metadata.get('_is_operation_bench', False)

                    if is_operation_bench or bench_type == 'operation':
                        metric_label = 'DAU'
                        plot_title = 'Platform Operations: DAU vs Day'
                    elif bench_type == 'vending':
                        metric_label = 'Money ($)'
                        plot_title = 'Vending Machine Business: Money vs Day'
                    elif bench_type == 'partjob':
                        metric_label = 'Money ($)'
                        plot_title = 'Part-Time Job Business: Money vs Day'
                    else:
                        metric_label = 'Money ($)'
                        plot_title = 'Business Simulation: Money vs Day'

                label = create_short_label(session_name, metadata)

                plt.plot(days, metric_values, marker='o', markersize=3,
                        linewidth=2, alpha=0.7, color=colors[idx], label=label)

                if days and metric_values:
                    plt.scatter(days[0], metric_values[0], color=colors[idx],
                              s=100, marker='o', edgecolors='black', linewidths=2, zorder=5)
                    plt.scatter(days[-1], metric_values[-1], color=colors[idx],
                              s=100, marker='s', edgecolors='black', linewidths=2, zorder=5)

            except Exception as e:
                print(f"Error loading session {session_name}: {e}")
                continue

        if title:
            plt.title(title, fontsize=16, fontweight='bold')
        else:
            plt.title(plot_title or 'Session Metrics vs Day', fontsize=16, fontweight='bold')

        plt.xlabel('Day', fontsize=14)
        plt.ylabel(metric_label or 'Metric', fontsize=14)
        plt.grid(True, alpha=0.3, linestyle='--')

        if len(session_names) <= 5:
            plt.legend(loc='upper left', fontsize=9, framealpha=0.9,
                      bbox_to_anchor=(0, 1), ncol=1)
        elif len(session_names) <= 10:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, framealpha=0.9)
            plt.tight_layout()
        else:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7, framealpha=0.9)
            plt.tight_layout()

        if len(session_names) <= 5:
            circle_patch = mpatches.Patch(color='gray', label='○ Start')
            square_patch = mpatches.Patch(color='gray', label='□ End')
            first_legend = plt.gca().legend(loc='upper left', fontsize=9, framealpha=0.9,
                                          bbox_to_anchor=(0, 0.85), ncol=1)
            plt.gca().add_artist(first_legend)

        ax = plt.gca()
        if metric_key == 'money':
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y:.2f}'))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{int(y)}'))

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {output_file}")
        elif not show:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_output = f"./logs/money_vs_day_{timestamp}.png"
            plt.savefig(default_output, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {default_output}")

        if show:
            plt.show()

        plt.close()

    def plot_sessions_by_step(
        self,
        session_names: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        show: bool = False,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 7),
        all_sessions: bool = False,
        show_day_markers: bool = True,
        annotate_days: bool = True
    ) -> None:
        if session_names is None:
            if all_sessions:
                session_names = self.get_all_sessions()
            else:
                latest = self.get_latest_session()
                session_names = [latest] if latest else []

        if not session_names:
            print("No sessions found to visualize.")
            return

        plt.figure(figsize=figsize)

        colors = plt.cm.tab10(range(len(session_names)))

        metric_key = None
        metric_label = None
        plot_title = None

        def create_short_label(session_name: str, metadata: Dict) -> str:
            parts = session_name.split('_')
            if len(parts) >= 3:
                date_part = parts[-2] if len(parts) >= 2 else ''
                time_part = parts[-1] if len(parts) >= 1 else ''
                if len(date_part) == 8 and len(time_part) >= 6:
                    formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    formatted_time = f"{time_part[:2]}:{time_part[2:4]}"
                    short_name = f"{formatted_date} {formatted_time}"
                else:
                    short_name = session_name[-20:] if len(session_name) > 20 else session_name
            else:
                short_name = session_name[-20:] if len(session_name) > 20 else session_name

            if metadata.get('config', {}).get('model_name'):
                model = metadata['config']['model_name']
                if len(model) > 15:
                    model = model[:12] + "..."
                return f"{short_name} ({model})"
            return short_name

        for idx, session_name in enumerate(session_names):
            try:
                steps, metric_values, day_values, metadata = self.load_session_data_by_step(session_name)

                if not steps:
                    print(f"Warning: No data found for session {session_name}")
                    continue

                if metric_key is None:
                    metric_key = metadata.get('_metric_key', 'money')
                    bench_type = metadata.get('_bench_type', 'unknown')
                    is_operation_bench = metadata.get('_is_operation_bench', False)

                    if is_operation_bench or bench_type == 'operation':
                        metric_label = 'DAU'
                        plot_title = 'Platform Operations: DAU vs Step'
                    elif bench_type == 'vending':
                        metric_label = 'Money ($)'
                        plot_title = 'Vending Machine Business: Money vs Step'
                    elif bench_type == 'partjob':
                        metric_label = 'Money ($)'
                        plot_title = 'Part-Time Job Business: Money vs Step'
                    else:
                        metric_label = 'Money ($)'
                        plot_title = 'Business Simulation: Money vs Step'

                label = create_short_label(session_name, metadata)

                plt.plot(steps, metric_values, marker='o', markersize=3,
                        linewidth=2, alpha=0.7, color=colors[idx], label=label)

                if steps and metric_values:
                    plt.scatter(steps[0], metric_values[0], color=colors[idx],
                              s=100, marker='o', edgecolors='black', linewidths=2, zorder=5)
                    plt.scatter(steps[-1], metric_values[-1], color=colors[idx],
                              s=100, marker='s', edgecolors='black', linewidths=2, zorder=5)

                if show_day_markers and (len(session_names) == 1 or idx == 0):
                    day_changes = []
                    for i in range(1, len(day_values)):
                        if day_values[i] != day_values[i-1]:
                            day_changes.append((steps[i], day_values[i]))

                    for step, day in day_changes:
                        plt.axvline(x=step, color='gray', linestyle='--', alpha=0.3, linewidth=1)

                        if annotate_days:
                            max_day = max(day_values) if day_values else 0
                            annotation_interval = max(1, max_day // 10)

                            if day % annotation_interval == 0 or day == 1:
                                y_pos = metric_values[steps.index(step)] if step in steps else max(metric_values)
                                plt.text(step, y_pos, f'Day {day}',
                                       rotation=90, verticalalignment='bottom',
                                       fontsize=8, alpha=0.6, color='gray')

            except Exception as e:
                print(f"Error loading session {session_name}: {e}")
                continue

        if title:
            plt.title(title, fontsize=16, fontweight='bold')
        else:
            plt.title(plot_title or 'Session Metrics vs Step', fontsize=16, fontweight='bold')

        plt.xlabel('Step', fontsize=14)
        plt.ylabel(metric_label or 'Metric', fontsize=14)
        plt.grid(True, alpha=0.3, linestyle='--')

        if len(session_names) <= 5:
            plt.legend(loc='upper left', fontsize=9, framealpha=0.9,
                      bbox_to_anchor=(0, 1), ncol=1)
        elif len(session_names) <= 10:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, framealpha=0.9)
            plt.tight_layout()
        else:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7, framealpha=0.9)
            plt.tight_layout()

        ax = plt.gca()
        if metric_key == 'money':
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y:.2f}'))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{int(y)}'))

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {output_file}")
        elif not show:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_output = f"./logs/money_vs_step_{timestamp}.png"
            plt.savefig(default_output, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {default_output}")

        if show:
            plt.show()

        plt.close()

    def print_session_summary(self, session_names: Optional[List[str]] = None, all_sessions: bool = False) -> None:
        if session_names is None:
            if all_sessions:
                session_names = self.get_all_sessions()
            else:
                latest = self.get_latest_session()
                session_names = [latest] if latest else []

        print("\n" + "="*80)
        print("SESSION SUMMARY")
        print("="*80)

        for session_name in session_names:
            try:
                days, metric_values, metadata = self.load_session_data(session_name)

                if not days or not metric_values:
                    continue

                metric_key = metadata.get('_metric_key', 'money')
                is_operation_bench = metadata.get('_is_operation_bench', False)

                initial_value = metric_values[0]
                final_value = metric_values[-1]
                change = final_value - initial_value
                change_pct = (change / initial_value * 100) if initial_value > 0 else 0
                max_value = max(metric_values)
                min_value = min(metric_values)

                print(f"\n{session_name}")
                print(f"  Model: {metadata.get('config', {}).get('model_name', 'N/A')}")
                print(f"  Days simulated: {days[-1]}")

                if is_operation_bench:
                    print(f"  Initial DAU: {int(initial_value)}")
                    print(f"  Final DAU: {int(final_value)}")
                    print(f"  DAU Change: {int(change)} ({change_pct:+.1f}%)")
                    print(f"  Peak DAU: {int(max_value)}")
                    print(f"  Lowest DAU: {int(min_value)}")
                else:
                    print(f"  Initial money: ${initial_value:.2f}")
                    print(f"  Final money: ${final_value:.2f}")
                    print(f"  Profit: ${change:.2f} ({change_pct:+.1f}%)")
                    print(f"  Peak money: ${max_value:.2f}")
                    print(f"  Lowest money: ${min_value:.2f}")

                print(f"  Steps: {len(days)}")

            except Exception as e:
                print(f"\nError processing {session_name}: {e}")

        print("\n" + "="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Visualize vending machine session data: money vs day',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python visualize_sessions.py
  python visualize_sessions.py --mode step
  python visualize_sessions.py --mode both
  python visualize_sessions.py --all
  python visualize_sessions.py --sessions vending_bench_20251220_010110
  python visualize_sessions.py --show
  python visualize_sessions.py --output my_analysis.png
  python visualize_sessions.py --summary-only
        """
    )

    parser.add_argument(
        '--sessions-dir',
        default='./logs/sessions',
        help='Path to sessions directory (default: ./logs/sessions)'
    )

    parser.add_argument(
        '--sessions',
        nargs='+',
        help='Specific session names to visualize'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Visualize all sessions (default: only latest session)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file path for the plot (default: auto-generated)'
    )

    parser.add_argument(
        '--show',
        action='store_true',
        help='Display plot interactively (default: save to file)'
    )

    parser.add_argument(
        '--title',
        help='Custom title for the plot'
    )

    parser.add_argument(
        '--figsize',
        nargs=2,
        type=int,
        default=[12, 7],
        metavar=('WIDTH', 'HEIGHT'),
        help='Figure size in inches (default: 12 7)'
    )

    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Print summary statistics only (no plot)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available sessions and exit'
    )

    parser.add_argument(
        '--mode',
        choices=['day', 'step', 'both'],
        default='day',
        help='Plot mode: "day" for money vs day, "step" for money vs step, "both" for both plots (default: day)'
    )

    parser.add_argument(
        '--no-day-markers',
        action='store_true',
        help='Disable vertical lines showing day changes in step plot'
    )

    parser.add_argument(
        '--no-day-annotations',
        action='store_true',
        help='Disable day number annotations in step plot'
    )

    args = parser.parse_args()

    try:
        visualizer = SessionVisualizer(sessions_dir=args.sessions_dir)

        if args.list:
            sessions = visualizer.get_all_sessions()
            print(f"\nFound {len(sessions)} session(s):\n")
            for session in sessions:
                print(f"  - {session}")
            print()
            return

        visualizer.print_session_summary(args.sessions, all_sessions=args.all)

        if not args.summary_only:
            if args.mode == 'day':
                output_file = args.output
                if output_file and not output_file.endswith('.png'):
                    output_file = output_file.replace('.png', '_day.png')
                elif output_file is None:
                    output_file = None
                visualizer.plot_sessions(
                    session_names=args.sessions,
                    output_file=output_file,
                    show=args.show,
                    title=args.title,
                    figsize=tuple(args.figsize),
                    all_sessions=args.all
                )
            elif args.mode == 'step':
                output_file = args.output
                if output_file and not output_file.endswith('.png'):
                    output_file = output_file.replace('.png', '_step.png')
                elif output_file is None:
                    output_file = None
                visualizer.plot_sessions_by_step(
                    session_names=args.sessions,
                    output_file=output_file,
                    show=args.show,
                    title=args.title,
                    figsize=tuple(args.figsize),
                    all_sessions=args.all,
                    show_day_markers=not args.no_day_markers,
                    annotate_days=not args.no_day_annotations
                )
            elif args.mode == 'both':
                output_file_day = args.output
                if output_file_day:
                    if output_file_day.endswith('.png'):
                        output_file_day = output_file_day.replace('.png', '_day.png')
                    else:
                        output_file_day = output_file_day + '_day.png'
                else:
                    output_file_day = None

                visualizer.plot_sessions(
                    session_names=args.sessions,
                    output_file=output_file_day,
                    show=False,
                    title=args.title,
                    figsize=tuple(args.figsize),
                    all_sessions=args.all
                )

                output_file_step = args.output
                if output_file_step:
                    if output_file_step.endswith('.png'):
                        output_file_step = output_file_step.replace('.png', '_step.png')
                    else:
                        output_file_step = output_file_step + '_step.png'
                else:
                    output_file_step = None

                visualizer.plot_sessions_by_step(
                    session_names=args.sessions,
                    output_file=output_file_step,
                    show=args.show,
                    title=args.title,
                    figsize=tuple(args.figsize),
                    all_sessions=args.all,
                    show_day_markers=not args.no_day_markers,
                    annotate_days=not args.no_day_annotations
                )

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())

