import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import warnings

warnings.filterwarnings('ignore')

TEST_DATA = {
    "A1": {32: (0.42, 0.05), 64: (0.68, 0.04), 128: (0.89, 0.02), 256: (0.76, 0.06)},
    "A2": {32: (0.50, 0.04), 64: (0.60, 0.05), 128: (0.65, 0.03), 256: (0.62, 0.04)},
    "A3": {32: (0.48, 0.03), 64: (0.58, 0.04), 128: (0.68, 0.05), 256: (0.66, 0.03)},
    "A5": {32: (0.35, 0.02), 64: (0.50, 0.03), 128: (0.55, 0.04), 256: (0.52, 0.03)},
    "A6": {32: (0.25, 0.01), 64: (0.35, 0.02), 128: (0.40, 0.03), 256: (0.38, 0.02)},
}

VENDING_DATA = {
}
PARTJOB_DATA = {
}
OPERATION_DATA = {
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

def plot_results(plot_data, output_file):
    setstyle()

    records = []
    for model_name, data in plot_data.items():
        for window, val in data.items():
            if isinstance(val, (tuple, list)):
                mean_val = val[0]
                std_val = val[1]
            else:
                mean_val = val
                std_val = 0.0

            records.append({
                "Context Window": window,
                "Score": mean_val,
                "Std": std_val,
                "Model": model_name
            })

    df = pd.DataFrame(records)
    df = df.sort_values(by=["Model", "Context Window"])

    unique_models = list(plot_data.keys())
    num_models = len(unique_models)

    palette = sns.color_palette("tab20", n_colors=num_models)
    markers_list = ['o', 's', '^', 'v', 'D', 'X', 'P', '*', 'h', 'p', '<', '>', '8', 'd']
    if num_models > len(markers_list):
        markers_list = markers_list * (num_models // len(markers_list) + 1)

    plt.figure()
    ax = sns.lineplot(
        data=df,
        x="Context Window",
        y="Score",
        alpha=0.9,
        hue="Model",
        style="Model",
        markers=markers_list[:num_models],
        dashes=False,
        linewidth=2,
        markersize=8,
        palette=palette,
        hue_order=unique_models,
        style_order=unique_models,
        zorder=10
    )

    for i, model_name in enumerate(unique_models):
        subset = df[df["Model"] == model_name]

        ax.fill_between(
            subset["Context Window"],
            subset["Score"] - subset["Std"],
            subset["Score"] + subset["Std"],
            color=palette[i],
            alpha=0.2,
            linewidth=0,
            zorder=1
        )

    ax.set_xscale('log', base=2)
    ax.set_xticks([32, 64, 128, 256])
    ax.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, _: str(int(x))))

    plt.xlabel(r"Context Window Size ($N$ turns)", fontweight='bold')
    plt.ylabel("Y Label", fontweight='bold')

    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, frameon=False)

    sns.despine()
    plt.tight_layout()

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"figure is saved to: {output_file}")
    plt.show()

if __name__ == "__main__":
    output_file = "fig_context_window.pdf"
    plot_results(TEST_DATA, output_file)