import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import matplotlib.ticker as ticker
import warnings

warnings.filterwarnings('ignore')

COMPLEXITY_DATA = {
    "A": {
        10: (0.92, 0.02),
        50: (0.80, 0.04),
        100: (0.65, 0.05),
        500: (0.30, 0.06),
        1000: (0.15, 0.03),
        5000: (0.10, 0.02)
    },
    "B": {
        10: (0.85, 0.03),
        50: (0.70, 0.05),
        100: (0.50, 0.06),
        500: (0.20, 0.04),
        1000: (0.10, 0.02),
        5000: (0.05, 0.01)
    },
    "C": {
        10: (0.88, 0.03),
        50: (0.75, 0.04),
        100: (0.60, 0.05),
        500: (0.35, 0.06),
        1000: (0.25, 0.04),
        5000: (0.20, 0.03)
    }
}

def setstyle():
    sns.set_theme(style="whitegrid", rc={"axes.axisbelow": True, "grid.linestyle": "--", "grid.alpha": 0.5})

    try:
        plt.rcParams.update({
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "axes.labelsize": 14,
            "font.size": 12,
            "legend.fontsize": 10,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "figure.figsize": (8, 5)
        })
    except:
        pass

def plot_complexity_results(plot_data, output_file):
    setstyle()

    records = []
    for model_name, data in plot_data.items():
        for sku_count, val in data.items():
            if isinstance(val, (tuple, list)):
                mean_val = val[0]
                std_val = val[1]
            else:
                mean_val = val
                std_val = 0.0

            records.append({
                "SKU Count": sku_count,
                "Score": mean_val,
                "Std": std_val,
                "Model": model_name
            })

    df = pd.DataFrame(records)
    df = df.sort_values(by=["Model", "SKU Count"])

    unique_models = list(plot_data.keys())
    num_models = len(unique_models)

    palette = sns.color_palette("tab10" if num_models <= 10 else "tab20", n_colors=num_models)
    markers_list = ['o', 's', '^', 'v', 'D', 'X', 'P', '*', 'h', 'p', '<', '>', '8', 'd']

    if num_models > len(markers_list):
        markers_list = markers_list * (num_models // len(markers_list) + 1)

    plt.figure()

    ax = sns.lineplot(
        data=df,
        x="SKU Count",
        y="Score",
        alpha=0.9,
        hue="Model",
        style="Model",
        markers=markers_list[:num_models],
        dashes=False,
        linewidth=2.5,
        markersize=9,
        palette=palette,
        hue_order=unique_models,
        style_order=unique_models,
        zorder=10
    )

    for i, model_name in enumerate(unique_models):
        subset = df[df["Model"] == model_name]

        ax.fill_between(
            subset["SKU Count"],
            subset["Score"] - subset["Std"],
            subset["Score"] + subset["Std"],
            color=palette[i],
            alpha=0.15,
            linewidth=0,
            zorder=1
        )

    ax.set_xscale('log', base=10)

    major_ticks = [10, 100, 1000, 5000]
    ax.set_xticks(major_ticks)

    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())

    plt.xlabel(r"Number of Stock Keeping Units (SKUs)", fontweight='bold')
    plt.ylabel("Y Label", fontweight='bold')

    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, frameon=False)

    sns.despine()
    plt.grid(True, which="minor", ls=":", alpha=0.3)
    plt.tight_layout()

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Figure is saved to: {output_file}")
    plt.show()

if __name__ == "__main__":
    output_file = "fig_complexity.pdf"
    plot_complexity_results(COMPLEXITY_DATA, output_file)