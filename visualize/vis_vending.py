

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime


class VendingVisualizer:

    def __init__(self, sessions_dir: str = "./logs/sessions"):
        self.sessions_dir = Path(sessions_dir)
        if not self.sessions_dir.exists():
            raise ValueError(f"Sessions directory not found: {sessions_dir}")

    def get_all_vending_sessions(self) -> List[str]:
        sessions = []
        for item in self.sessions_dir.iterdir():
            if item.is_dir() and item.name.startswith('vending_bench') and (item / "steps.jsonl").exists():
                sessions.append(item.name)
        return sorted(sessions, reverse=True)

    def get_latest_session(self) -> Optional[str]:
        sessions = self.get_all_vending_sessions()
        return sessions[0] if sessions else None

    def calculate_inventory_value(self, product_quantities: Dict[str, int],
                                  wholesale_prices: Dict[str, float]) -> float:
        total_value = 0.0
        for product, quantity in product_quantities.items():
            wholesale_price = wholesale_prices.get(product, 0.0)
            total_value += quantity * wholesale_price
        return total_value

    def calculate_pending_orders_value(self, orders: list) -> float:
        total_value = 0.0
        for order in orders:
            if order.get("status") == "processing":
                total_value += order.get("total_cost", 0.0)
        return total_value

    def load_session_data(self, session_name: str) -> Tuple[List[int], List[float], List[float], Dict]:
        session_path = self.sessions_dir / session_name
        steps_file = session_path / "steps.jsonl"
        metadata_file = session_path / "metadata.json"

        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        day_data = {}

        with open(steps_file, 'r') as f:
            for line in f:
                if line.strip():
                    step_data = json.loads(line)

                    state = step_data.get('state_after') or step_data.get('state_before')

                    if state and 'day' in state and 'money' in state:
                        day = state['day']
                        money = state['money']

                        product_quantities = state.get('product_quantities', {})
                        wholesale_prices = state.get('wholesale_prices', {})
                        inventory_value = self.calculate_inventory_value(product_quantities, wholesale_prices)

                        orders = state.get('orders', [])
                        pending_orders_value = self.calculate_pending_orders_value(orders)

                        net_worth = money + inventory_value + pending_orders_value

                        day_data[day] = (money, net_worth)

        days = []
        money_values = []
        net_worth_values = []

        for day in sorted(day_data.keys()):
            money, net_worth = day_data[day]
            days.append(day)
            money_values.append(money)
            net_worth_values.append(net_worth)

        return days, money_values, net_worth_values, metadata

    def load_product_data(self, session_name: str) -> Tuple[List[int], List[int], List[int], Dict]:
        session_path = self.sessions_dir / session_name
        steps_file = session_path / "steps.jsonl"
        metadata_file = session_path / "metadata.json"

        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        all_products_seen = set()
        day_data = {}

        with open(steps_file, 'r') as f:
            for line in f:
                if line.strip():
                    step_data = json.loads(line)

                    state = step_data.get('state_after') or step_data.get('state_before')

                    if state and 'day' in state:
                        day = state['day']

                        products = state.get('products', [])
                        if isinstance(products, list):
                            all_products_seen.update(products)

                        total_explored = len(all_products_seen)

                        product_quantities = state.get('product_quantities', {})
                        products_with_inventory = sum(1 for qty in product_quantities.values() if qty > 0)

                        if day not in day_data:
                            day_data[day] = (total_explored, products_with_inventory)
                        else:
                            prev_explored, prev_inventory = day_data[day]
                            day_data[day] = (max(prev_explored, total_explored), max(prev_inventory, products_with_inventory))

        sorted_days = sorted(day_data.keys())
        max_explored_so_far = 0
        for day in sorted_days:
            explored, inventory = day_data[day]
            if explored < max_explored_so_far:
                explored = max_explored_so_far
            max_explored_so_far = explored
            day_data[day] = (explored, inventory)

        days = []
        total_explored_values = []
        with_inventory_values = []

        for day in sorted(day_data.keys()):
            total_explored, with_inventory = day_data[day]
            days.append(day)
            total_explored_values.append(total_explored)
            with_inventory_values.append(with_inventory)

        return days, total_explored_values, with_inventory_values, metadata

    def load_tool_calls_data(self, session_name: str) -> Tuple[List[int], Dict[str, List[int]], Dict]:
        session_path = self.sessions_dir / session_name
        steps_file = session_path / "steps.jsonl"
        metadata_file = session_path / "metadata.json"

        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        day_tool_counts = {}

        with open(steps_file, 'r') as f:
            for line in f:
                if line.strip():
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

    def plot_sessions(
        self,
        session_names: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        show: bool = False,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (14, 8),
        all_sessions: bool = False,
        show_money: bool = False
    ) -> None:
        if session_names is None:
            if all_sessions:
                session_names = self.get_all_vending_sessions()
            else:
                latest = self.get_latest_session()
                session_names = [latest] if latest else []

        if not session_names:
            print("No vending bench sessions found to visualize.")
            return

        fig, ax = plt.subplots(figsize=figsize)

        colors = plt.cm.tab10(range(len(session_names)))

        def create_short_label(session_name: str, metadata: Dict) -> str:
            label = session_name

            if metadata.get('config', {}).get('model_name'):
                model = metadata['config']['model_name']
                if len(model) > 15:
                    model = model[:12] + "..."
                return f"{label} ({model})"
            return label

        for idx, session_name in enumerate(session_names):
            try:
                days, money_values, net_worth_values, metadata = self.load_session_data(session_name)

                if not days:
                    print(f"Warning: No data found for session {session_name}")
                    continue

                label = create_short_label(session_name, metadata)
                color = colors[idx]

                if show_money:
                    ax.plot(days, money_values, marker='o', markersize=3,
                           linewidth=2, alpha=0.7, color=color, linestyle='-',
                           label=f"{label} - Money")

                    if days and money_values:
                        ax.scatter(days[0], money_values[0], color=color,
                                 s=100, marker='o', edgecolors='black', linewidths=2, zorder=5)
                        ax.scatter(days[-1], money_values[-1], color=color,
                                 s=100, marker='o', edgecolors='black', linewidths=2, zorder=5)

                net_worth_linestyle = '--' if show_money else '-'
                net_worth_marker = 's' if show_money else 'o'
                net_worth_label = f"{label} - Net Worth" if show_money else f"{label}"

                ax.plot(days, net_worth_values, marker=net_worth_marker, markersize=3,
                       linewidth=2, alpha=0.7, color=color, linestyle=net_worth_linestyle,
                       label=net_worth_label)

                if days and net_worth_values:
                    ax.scatter(days[0], net_worth_values[0], color=color,
                             s=100, marker=net_worth_marker, edgecolors='black', linewidths=2, zorder=5)
                    ax.scatter(days[-1], net_worth_values[-1], color=color,
                             s=100, marker=net_worth_marker, edgecolors='black', linewidths=2, zorder=5)

            except Exception as e:
                print(f"Error loading session {session_name}: {e}")
                continue

        session_labels_dict = {}
        for session_name in session_names:
            try:
                _, _, _, metadata = self.load_session_data(session_name)
                session_labels_dict[session_name] = create_short_label(session_name, metadata)
            except:
                session_labels_dict[session_name] = session_name

        if title:
            ax.set_title(title, fontsize=16, fontweight='bold')
        else:
            if show_money:
                title_text = 'Vending Machine Business: Money & Net Worth vs Day'
            else:
                title_text = 'Vending Machine Business: Net Worth vs Day'

            if len(session_names) == 1:
                session_label = session_labels_dict.get(session_names[0], session_names[0])
                ax.set_title(f'{title_text}\nSession: {session_label}',
                            fontsize=16, fontweight='bold')
            else:
                ax.set_title(title_text, fontsize=16, fontweight='bold')

        ax.set_xlabel('Day', fontsize=14)
        ax.set_ylabel('Value ($)', fontsize=14)
        ax.grid(True, alpha=0.3, linestyle='--')

        if len(session_names) <= 3:
            ax.legend(loc='best', fontsize=9, framealpha=0.9)
        elif len(session_names) <= 6:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, framealpha=0.9)
            plt.tight_layout()
        else:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7, framealpha=0.9)
            plt.tight_layout()

        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y:.2f}'))

        note_text = 'Net Worth = Money + Inventory Value + Pending Orders (in transit, 3-day delivery)'
        ax.text(0.5, -0.12, note_text, transform=ax.transAxes,
               fontsize=9, ha='center', style='italic', color='gray')

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {output_file}")
        elif not show:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_output = f"./logs/vending_money_networth_vs_day_{timestamp}.png"
            plt.savefig(default_output, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {default_output}")

        if show:
            plt.show()

        plt.close()

    def plot_product_exploration(
        self,
        session_names: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        show: bool = False,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (14, 8),
        all_sessions: bool = False
    ) -> None:
        if session_names is None:
            if all_sessions:
                session_names = self.get_all_vending_sessions()
            else:
                latest = self.get_latest_session()
                session_names = [latest] if latest else []

        if not session_names:
            print("No vending bench sessions found to visualize.")
            return

        fig, ax = plt.subplots(figsize=figsize)

        colors = plt.cm.tab10(range(len(session_names)))

        def create_short_label(session_name: str, metadata: Dict) -> str:
            label = session_name

            if metadata.get('config', {}).get('model_name'):
                model = metadata['config']['model_name']
                if len(model) > 15:
                    model = model[:12] + "..."
                return f"{label} ({model})"
            return label

        for idx, session_name in enumerate(session_names):
            try:
                days, total_explored, with_inventory, metadata = self.load_product_data(session_name)

                if not days:
                    print(f"Warning: No data found for session {session_name}")
                    continue

                label = create_short_label(session_name, metadata)
                color = colors[idx]

                ax.plot(days, total_explored, marker='o', markersize=3,
                       linewidth=2, alpha=0.7, color=color, linestyle='-',
                       label=f"{label} - Explored")

                ax.plot(days, with_inventory, marker='s', markersize=3,
                       linewidth=2, alpha=0.7, color=color, linestyle='--',
                       label=f"{label} - With Inventory")

                if days and total_explored:
                    ax.scatter(days[0], total_explored[0], color=color,
                             s=100, marker='o', edgecolors='black', linewidths=2, zorder=5)
                    ax.scatter(days[-1], total_explored[-1], color=color,
                             s=100, marker='o', edgecolors='black', linewidths=2, zorder=5)

                if days and with_inventory:
                    ax.scatter(days[0], with_inventory[0], color=color,
                             s=100, marker='s', edgecolors='black', linewidths=2, zorder=5)
                    ax.scatter(days[-1], with_inventory[-1], color=color,
                             s=100, marker='s', edgecolors='black', linewidths=2, zorder=5)

            except Exception as e:
                print(f"Error loading session {session_name}: {e}")
                continue

        session_labels_dict = {}
        for session_name in session_names:
            try:
                _, _, _, metadata = self.load_product_data(session_name)
                session_labels_dict[session_name] = create_short_label(session_name, metadata)
            except:
                session_labels_dict[session_name] = session_name

        if title:
            ax.set_title(title, fontsize=16, fontweight='bold')
        else:
            if len(session_names) == 1:
                session_label = session_labels_dict.get(session_names[0], session_names[0])
                ax.set_title(f'Vending Machine Business: Product Exploration vs Day\nSession: {session_label}',
                            fontsize=16, fontweight='bold')
            else:
                ax.set_title('Vending Machine Business: Product Exploration vs Day',
                            fontsize=16, fontweight='bold')

        ax.set_xlabel('Day', fontsize=14)
        ax.set_ylabel('Number of Products', fontsize=14)
        ax.grid(True, alpha=0.3, linestyle='--')

        if len(session_names) <= 3:
            ax.legend(loc='best', fontsize=9, framealpha=0.9)
        elif len(session_names) <= 6:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, framealpha=0.9)
            plt.tight_layout()
        else:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7, framealpha=0.9)
            plt.tight_layout()

        note_text = 'Explored = Total unique products discovered | With Inventory = Products currently in stock (qty > 0)'
        ax.text(0.5, -0.12, note_text, transform=ax.transAxes,
               fontsize=9, ha='center', style='italic', color='gray')

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Product exploration plot saved to: {output_file}")
        elif not show:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_output = f"./logs/vending_products_vs_day_{timestamp}.png"
            plt.savefig(default_output, dpi=300, bbox_inches='tight')
            print(f"Product exploration plot saved to: {default_output}")

        if show:
            plt.show()

        plt.close()

    def plot_tool_calls(
        self,
        session_names: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        show: bool = False,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (14, 8),
        all_sessions: bool = False
    ) -> None:
        if session_names is None:
            if all_sessions:
                session_names = self.get_all_vending_sessions()
            else:
                latest = self.get_latest_session()
                session_names = [latest] if latest else []

        if not session_names:
            print("No vending bench sessions found to visualize.")
            return

        fig, ax = plt.subplots(figsize=figsize)

        colors = plt.cm.tab10(range(len(session_names)))

        def create_short_label(session_name: str, metadata: Dict) -> str:
            label = session_name

            if metadata.get('config', {}).get('model_name'):
                model = metadata['config']['model_name']
                if len(model) > 15:
                    model = model[:12] + "..."
                return f"{label} ({model})"
            return label

        line_styles = ['-', '--', '-.', ':', '-', '--']
        markers = ['o', 's', '^', 'v', 'D', 'p']

        for idx, session_name in enumerate(session_names):
            try:
                days, tool_calls_by_type, metadata = self.load_tool_calls_data(session_name)

                if not days:
                    print(f"Warning: No data found for session {session_name}")
                    continue

                label = create_short_label(session_name, metadata)
                base_color = colors[idx]

                tool_names = sorted(tool_calls_by_type.keys())
                for tool_idx, tool_name in enumerate(tool_names):
                    tool_counts = tool_calls_by_type[tool_name]

                    if len(session_names) > 1:
                        tool_color = base_color
                        alpha = 0.7
                    else:
                        tool_color = colors[tool_idx % len(colors)]
                        alpha = 0.8

                    if len(session_names) > 1:
                        tool_label = f"{label} - {tool_name}"
                    else:
                        tool_label = tool_name

                    linestyle = line_styles[tool_idx % len(line_styles)]
                    marker = markers[tool_idx % len(markers)]
                    ax.plot(days, tool_counts, marker=marker, markersize=3,
                           linewidth=2, alpha=alpha, color=tool_color, linestyle=linestyle,
                           label=tool_label)

                    if days and tool_counts and tool_counts[-1] > 0:
                        ax.scatter(days[0], tool_counts[0], color=tool_color,
                                 s=80, marker=marker, edgecolors='black', linewidths=1.5, zorder=5, alpha=alpha)
                        ax.scatter(days[-1], tool_counts[-1], color=tool_color,
                                 s=80, marker=marker, edgecolors='black', linewidths=1.5, zorder=5, alpha=alpha)

            except Exception as e:
                print(f"Error loading session {session_name}: {e}")
                continue

        session_labels_dict = {}
        for session_name in session_names:
            try:
                _, _, metadata = self.load_tool_calls_data(session_name)
                session_labels_dict[session_name] = create_short_label(session_name, metadata)
            except:
                session_labels_dict[session_name] = session_name

        if title:
            ax.set_title(title, fontsize=16, fontweight='bold')
        else:
            if len(session_names) == 1:
                session_label = session_labels_dict.get(session_names[0], session_names[0])
                ax.set_title(f'Vending Machine Business: Tool Calls by Type vs Day\nSession: {session_label}',
                            fontsize=16, fontweight='bold')
            else:
                ax.set_title('Vending Machine Business: Tool Calls by Type vs Day',
                            fontsize=16, fontweight='bold')

        ax.set_xlabel('Day', fontsize=14)
        ax.set_ylabel('Cumulative Tool Calls', fontsize=14)
        ax.grid(True, alpha=0.3, linestyle='--')

        if len(session_names) == 1:
            ax.legend(loc='best', fontsize=9, framealpha=0.9)
        elif len(session_names) <= 3:
            ax.legend(loc='best', fontsize=8, framealpha=0.9)
        elif len(session_names) <= 6:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7, framealpha=0.9)
            plt.tight_layout()
        else:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=6, framealpha=0.9)
            plt.tight_layout()

        note_text = 'Cumulative count of tool calls by type (each tool shown as a separate line)'
        ax.text(0.5, -0.12, note_text, transform=ax.transAxes,
               fontsize=9, ha='center', style='italic', color='gray')

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Tool calls plot saved to: {output_file}")
        elif not show:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_output = f"./logs/vending_tool_calls_vs_day_{timestamp}.png"
            plt.savefig(default_output, dpi=300, bbox_inches='tight')
            print(f"Tool calls plot saved to: {default_output}")

        if show:
            plt.show()

        plt.close()

    def print_session_summary(self, session_names: Optional[List[str]] = None,
                            all_sessions: bool = False) -> None:
        if session_names is None:
            if all_sessions:
                session_names = self.get_all_vending_sessions()
            else:
                latest = self.get_latest_session()
                session_names = [latest] if latest else []

        print("\n" + "="*80)
        print("VENDING BENCH SESSION SUMMARY")
        print("="*80)

        for session_name in session_names:
            try:
                days, money_values, net_worth_values, metadata = self.load_session_data(session_name)

                if not days or not money_values:
                    continue

                initial_money = money_values[0]
                final_money = money_values[-1]
                money_change = final_money - initial_money
                money_change_pct = (money_change / initial_money * 100) if initial_money > 0 else 0

                initial_net_worth = net_worth_values[0]
                final_net_worth = net_worth_values[-1]
                net_worth_change = final_net_worth - initial_net_worth
                net_worth_change_pct = (net_worth_change / initial_net_worth * 100) if initial_net_worth > 0 else 0

                max_money = max(money_values)
                min_money = min(money_values)
                max_net_worth = max(net_worth_values)
                min_net_worth = min(net_worth_values)

                final_inventory_value = final_net_worth - final_money

                print(f"\n{session_name}")
                print(f"  Model: {metadata.get('config', {}).get('model_name', 'N/A')}")
                print(f"  Days simulated: {days[-1]}")
                print(f"\n  MONEY:")
                print(f"    Initial: ${initial_money:.2f}")
                print(f"    Final: ${final_money:.2f}")
                print(f"    Change: ${money_change:.2f} ({money_change_pct:+.1f}%)")
                print(f"    Peak: ${max_money:.2f}")
                print(f"    Lowest: ${min_money:.2f}")
                print(f"\n  NET WORTH:")
                print(f"    Initial: ${initial_net_worth:.2f}")
                print(f"    Final: ${final_net_worth:.2f}")
                print(f"    Change: ${net_worth_change:.2f} ({net_worth_change_pct:+.1f}%)")
                print(f"    Peak: ${max_net_worth:.2f}")
                print(f"    Lowest: ${min_net_worth:.2f}")
                print(f"\n  INVENTORY:")
                print(f"    Final value: ${final_inventory_value:.2f}")
                print(f"    Percentage of net worth: {(final_inventory_value/final_net_worth*100):.1f}%")

                print(f"\n  Steps: {len(days)}")

            except Exception as e:
                print(f"\nError processing {session_name}: {e}")

        print("\n" + "="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Visualize vending bench session data: money and net worth vs day',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vis_vending.py

  python vis_vending.py --show-money

  python vis_vending.py --all

  python vis_vending.py --sessions vending_bench_20260114_020118

  python vis_vending.py --show

  python vis_vending.py --output my_analysis.png

  python vis_vending.py --money-only

  python vis_vending.py --products-only

  python vis_vending.py --tools-only

  python vis_vending.py --summary-only
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
        help='Visualize all vending bench sessions (default: only latest)'
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
        default=[14, 8],
        metavar=('WIDTH', 'HEIGHT'),
        help='Figure size in inches (default: 14 8)'
    )

    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Print summary statistics only (no plot)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available vending bench sessions and exit'
    )

    parser.add_argument(
        '--money-only',
        action='store_true',
        help='Only plot net worth (skip product exploration and tool calls)'
    )

    parser.add_argument(
        '--products-only',
        action='store_true',
        help='Only plot product exploration (skip money and net worth)'
    )

    parser.add_argument(
        '--product-output',
        help='Output file path for the product exploration plot (default: auto-generated)'
    )

    parser.add_argument(
        '--tools-only',
        action='store_true',
        help='Only plot tool calls (skip money, net worth, and product exploration)'
    )

    parser.add_argument(
        '--tool-output',
        help='Output file path for the tool calls plot (default: auto-generated)'
    )

    parser.add_argument(
        '--show-money',
        action='store_true',
        help='Show both money and net worth (default: only show net worth)'
    )

    args = parser.parse_args()

    try:
        visualizer = VendingVisualizer(sessions_dir=args.sessions_dir)

        if args.list:
            sessions = visualizer.get_all_vending_sessions()
            print(f"\nFound {len(sessions)} vending bench session(s):\n")
            for session in sessions:
                print(f"  - {session}")
            print()
            return

        visualizer.print_session_summary(args.sessions, all_sessions=args.all)

        if not args.summary_only:
            if not args.products_only and not args.tools_only:
                visualizer.plot_sessions(
                    session_names=args.sessions,
                    output_file=args.output,
                    show=args.show,
                    title=args.title,
                    figsize=tuple(args.figsize),
                    all_sessions=args.all,
                    show_money=args.show_money
                )

            if not args.money_only and not args.tools_only:
                visualizer.plot_product_exploration(
                    session_names=args.sessions,
                    output_file=args.product_output,
                    show=args.show,
                    title=args.title,
                    figsize=tuple(args.figsize),
                    all_sessions=args.all
                )

            if not args.money_only and not args.products_only:
                visualizer.plot_tool_calls(
                    session_names=args.sessions,
                    output_file=args.tool_output,
                    show=args.show,
                    title=args.title,
                    figsize=tuple(args.figsize),
                    all_sessions=args.all
                )

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())

