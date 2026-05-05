import re
import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as mpatches
from scipy.interpolate import make_interp_spline
import warnings

warnings.filterwarnings('ignore')

COLOR_PALETTE = [
    "#4E008E",
    "#2A4D8E",
    "#008E83",
    "#6ACC6A",
    "#F28E2B",
    "#E15759",
    "#76B7B2",
    "#EDC948",
    "#B07AA1",
    "#9C755F"
]

def set_publication_style():
    plt.style.use('default')
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "axes.labelsize": 10,
        "font.size": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.dpi": 300,
    })


def load_model_name(session_dir):
    meta_path = os.path.join(session_dir, 'metadata.json')
    try:
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            name = meta.get('config', {}).get('full_config', {}).get('model_config', {}).get('model_name')
            if name: return name
    except:
        pass
    return os.path.basename(session_dir)

def parse_log_continuous(file_path):
    tool_days = {}
    day_pattern = re.compile(r"(?:Day|day|Step)[:\s\[]+(\d+)")
    tool_pattern = re.compile(r"\[Tool Call\]\s+(.*?)\s+with args:\s*")
    current_day = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            day_match = day_pattern.search(line)
            if day_match:
                try: current_day = int(day_match.group(1))
                except: pass
            if "[Tool Call]" in line:
                match = tool_pattern.search(line)
                if match:
                    tool = match.group(1).strip().replace('"', '').replace("'", "")
                    if tool not in tool_days: tool_days[tool] = []
                    tool_days[tool].append(current_day)
        return tool_days
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_top_tools(all_data, top_n=8):
    global_counter = {}
    for session_tools in all_data.values():
        for tool, days in session_tools.items():
            global_counter[tool] = global_counter.get(tool, 0) + len(days)
    sorted_tools = sorted(global_counter.items(), key=lambda x: x[1], reverse=True)
    top_tools_list = [t[0] for t in sorted_tools[:top_n]]
    color_map = {}
    for i, tool in enumerate(top_tools_list):
        color_map[tool] = COLOR_PALETTE[i % len(COLOR_PALETTE)]
    return top_tools_list, color_map


def polygon_spline_counts(days, bins=25, max_day=365):
    if not days:
        return [(0, 0), (max_day, 0)], 0

    counts, edges = np.histogram(days, bins=bins, range=(0, max_day))

    x_bins = (edges[:-1] + edges[1:]) / 2
    y_bins = counts

    x_bins = np.concatenate([[0], x_bins, [max_day]])
    y_bins = np.concatenate([[0], y_bins, [0]])

    try:
        spl = make_interp_spline(x_bins, y_bins, k=3)

        x_smooth = np.linspace(0, max_day, 300)
        y_smooth = spl(x_smooth)

        y_smooth[y_smooth < 0] = 0

        verts = [(0, 0)] + list(zip(x_smooth, y_smooth)) + [(max_day, 0)]

        return verts, y_smooth.max()

    except Exception:
        verts = [(0, 0)] + list(zip(x_bins, y_bins)) + [(max_day, 0)]
        return verts, y_bins.max()

def custom_3d_axis_style(ax):
    ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))

    grid_style = {'color': '#CCCCCC', 'linestyle': ':', 'linewidth': 0.5}
    ax.xaxis._axinfo["grid"].update(grid_style)
    ax.yaxis._axinfo["grid"].update(grid_style)
    ax.zaxis._axinfo["grid"].update(grid_style)

    ax.set_box_aspect((3, 2.5, 1.2))

def plot_spline_count_3d(all_data, titles_map, output_file):
    set_publication_style()
    num_sessions = len(all_data)
    if num_sessions == 0: return

    top_tools, color_map = get_top_tools(all_data, top_n=8)
    display_tools = top_tools[::-1]

    fig = plt.figure(figsize=(5 * num_sessions + 2, 5.5))

    global_z_max = 0
    SPLINE_BINS = 30

    for tool_data in all_data.values():
        for t in display_tools:
            d = tool_data.get(t, [])
            if d:
                _, y_max = polygon_spline_counts(d, bins=SPLINE_BINS)
                if y_max > global_z_max: global_z_max = y_max

    z_limit = int(global_z_max * 1.15) if global_z_max > 0 else 10

    legend_patches = [mpatches.Patch(color=color_map[t], label=t) for t in top_tools]

    for idx, (session_id, tool_data) in enumerate(all_data.items()):
        ax = fig.add_subplot(1, num_sessions, idx + 1, projection='3d')
        custom_3d_axis_style(ax)

        verts = []
        colors = []

        for tool_name in display_tools:
            days = tool_data.get(tool_name, [])

            poly_verts, _ = polygon_spline_counts(days, bins=SPLINE_BINS)
            verts.append(poly_verts)

            colors.append(color_map.get(tool_name, "#999999"))

        poly = PolyCollection(verts, facecolors=colors, edgecolors=colors, linewidths=0.5,alpha=0.7)

        ax.add_collection3d(poly, zs=range(len(display_tools)), zdir='y')

        ax.set_xlim3d(0, 365)
        ax.set_xlabel('Simulation Day', labelpad=5, fontweight='bold')

        ax.set_ylim3d(-0.5, len(display_tools) - 0.5)
        ax.set_yticks(range(len(display_tools)))
        ax.set_yticklabels(display_tools, verticalalignment='center', horizontalalignment='left', fontsize=8, fontweight='medium')
        ax.set_ylabel('', labelpad=0)

        ax.set_zlim3d(0, z_limit)
        ax.set_zlabel('Call Count', labelpad=2, fontsize=9, rotation=90)

        z_ticks = [0, int(z_limit/2), int(z_limit)]
        ax.set_zticks(z_ticks)
        ax.set_zticklabels([str(int(x)) for x in z_ticks], fontsize=8)

        ax.view_init(elev=30, azim=-55)

        title = titles_map.get(session_id, session_id)
        ax.set_title(title, fontsize=12, fontweight='bold', y=0.98)

    plt.subplots_adjust(left=0.25, right=0.92, wspace=0.1)

    fig.legend(
        handles=legend_patches,
        loc='center left',
        bbox_to_anchor=(0.02, 0.5),
        ncol=1,
        frameon=True,
        edgecolor='#cccccc',
        fontsize=10,
        title="Tool Types",
        title_fontsize=11
    )

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"figure is saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sessions', nargs='+', required=True, help='Session IDs')
    parser.add_argument('--logs_dir', type=str, default='logs')
    parser.add_argument('--output', type=str, default='tool_usage.pdf')

    args = parser.parse_args()

    all_data = {}
    titles_map = {}

    for sid in args.sessions:
        session_dir = os.path.join(args.logs_dir, "sessions", sid)
        log_path = os.path.join(session_dir, "detailed.log")
        if not os.path.exists(log_path): continue

        model_name = load_model_name(session_dir)
        titles_map[sid] = model_name

        data = parse_log_continuous(log_path)
        if data: all_data[sid] = data

    if not all_data:
        return

    plot_spline_count_3d(all_data, titles_map, args.output)

if __name__ == "__main__":
    main()