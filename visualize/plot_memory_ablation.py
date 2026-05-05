import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick
import warnings

warnings.filterwarnings('ignore')

TEST_DATA = {
    "A1": {"No Memory": (0.32, 0.02), "Pure Working": (0.41, 0.03), "Pure Symbolic": (0.48, 0.02), "Mem0": (0.55, 0.03)},
    "A2": {"No Memory": (0.45, 0.02), "Pure Working": (0.58, 0.02), "Pure Symbolic": (0.62, 0.03), "Mem0": (0.69, 0.02)},
    "A3": {"No Memory": (0.38, 0.03), "Pure Working": (0.50, 0.04), "Pure Symbolic": (0.54, 0.03), "Mem0": (0.62, 0.03)},
    "A4": {"No Memory": (0.35, 0.02), "Pure Working": (0.48, 0.03), "Pure Symbolic": (0.51, 0.02), "Mem0": (0.60, 0.03)},
    "A5": {"No Memory": (0.55, 0.02), "Pure Working": (0.68, 0.02), "Pure Symbolic": (0.72, 0.02), "Mem0": (0.79, 0.01)},
    "A6": {"No Memory": (0.36, 0.03), "Pure Working": (0.49, 0.03), "Pure Symbolic": (0.53, 0.02), "Mem0": (0.61, 0.03)},
    "A7": {"No Memory": (0.36, 0.03), "Pure Working": (0.49, 0.03), "Pure Symbolic": (0.53, 0.02), "Mem0": (0.61, 0.03)},
    "A8": {"No Memory": (0.36, 0.03), "Pure Working": (0.49, 0.03), "Pure Symbolic": (0.53, 0.02), "Mem0": (0.61, 0.03)},
    "A9": {"No Memory": (0.36, 0.03), "Pure Working": (0.49, 0.03), "Pure Symbolic": (0.53, 0.02), "Mem0": (0.61, 0.03)},
}

VENDING_DATA = {
}
PARTJOB_DATA = {
}
OPERATION_DATA = {
}

COLOR_PALETTE = [
    "#c85d6b",
    "#b2d6e7",
    "#a798bd",
    "#e18e4d",
    "#0e6232",
    "#404040",
]

def process_data(raw_data):
    means = {}
    errors = {}

    for model, methods in raw_data.items():
        means[model] = {}
        errors[model] = {}
        for method, value in methods.items():
            if isinstance(value, (list, tuple)):
                means[model][method] = value[0]
                errors[model][method] = value[1]
            else:
                means[model][method] = value
                errors[model][method] = 0.0

    df_mean = pd.DataFrame(means).T
    df_err = pd.DataFrame(errors).T

    return df_mean, df_err

def setstyle():
    sns.set_theme(style="whitegrid", rc={"axes.axisbelow": True, "grid.linestyle": "--", "grid.alpha": 0.5})
    try:
        plt.rcParams.update({
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "axes.labelsize": 14,
            "font.size": 12,
            "legend.fontsize": 11,
            "xtick.labelsize": 11,
            "ytick.labelsize": 12,
            "figure.figsize": (15, 6)
        })
    except:
        pass

def plot_results(plot_data, output_file):
    setstyle()

    df_mean, df_err = process_data(plot_data)
    num_methods = len(df_mean.columns)

    colors = sns.color_palette("deep", n_colors=num_methods)

    ax = df_mean.plot(
        kind='bar',
        yerr=df_err,
        width=0.8,
        alpha=0.7,
        color=COLOR_PALETTE,
        edgecolor='black',
        linewidth=0.5,
        capsize=3,
        rot=0,
        figsize=(15, 6),
        error_kw=dict(ecolor='black', elinewidth=1.5, capsize=4, capthick=1.5),
    )

    ax.set_ylabel("Y Label", fontweight='bold')

    plt.legend(
        bbox_to_anchor=(0.5, 1.12),
        loc='upper center',
        ncol=num_methods,
        frameon=False,
        columnspacing=1.5
    )

    sns.despine()
    plt.tight_layout()

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"figure is saved to: {output_file}")
    plt.show()

if __name__ == "__main__":
    output_file = "fig_memory_ablation.pdf"
    plot_results(TEST_DATA, output_file)