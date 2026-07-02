from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter


PACKAGE_DIR = Path(__file__).resolve().parents[1]
SOURCE_XLSX = PACKAGE_DIR / "data" / "Supplementary_Fig_4_cumulative_average_source_data.xlsx"
OUT_BASE = PACKAGE_DIR / "output" / "Supplementary_Fig_4_cumulative_average_reproduced_from_source_data"

BLUE = "#0B4EA2"
BLUE_LIGHT = "#63A8E8"
RED = "#D40000"
TEXT = "#111111"
GRID = "#C7C7C7"


def fmt_p(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def fmt_hr(hr: float, lo: float, hi: float) -> str:
    return f"{hr:.2f} ({lo:.2f}, {hi:.2f})"


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 14,
            "axes.linewidth": 1.2,
            "xtick.major.width": 1.1,
            "ytick.major.width": 1.1,
            "xtick.major.size": 5,
            "ytick.major.size": 5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def clean_axis(ax, keep_left: bool = True) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if not keep_left:
        ax.spines["left"].set_visible(False)
    ax.tick_params(axis="both", colors=TEXT)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sheets = pd.read_excel(SOURCE_XLSX, sheet_name=None, engine="openpyxl")
    return (
        sheets["Supplementary_Fig4a"],
        sheets["Supplementary_Fig4b"],
        sheets["Supplementary_Fig4c"],
    )


def draw_panel_a(ax, df: pd.DataFrame) -> None:
    plot_df = df.iloc[::-1].reset_index(drop=True)
    y = range(len(plot_df))
    ax.set_xscale("log")
    ax.axvline(1, color=TEXT, lw=1.0, ls=(0, (4, 4)))
    ax.errorbar(
        plot_df["HR"],
        list(y),
        xerr=[plot_df["HR"] - plot_df["CI_low"], plot_df["CI_high"] - plot_df["HR"]],
        fmt="s",
        ms=8,
        color=BLUE,
        ecolor=BLUE,
        elinewidth=1.3,
        capsize=4,
        capthick=1.3,
        zorder=3,
    )
    ax.set_yticks(list(y))
    ax.set_yticklabels(plot_df["term"], fontsize=13)
    ax.set_xlim(0.34, 2.12)
    ax.set_ylim(-0.65, len(plot_df) - 0.35)
    ax.xaxis.set_major_locator(FixedLocator([0.4, 0.6, 1.0, 1.5, 2.0]))
    ax.xaxis.set_major_formatter(FixedFormatter(["0.4", "0.6", "1.0", "1.5", "2.0"]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Hazard ratio (log scale)", fontsize=14, fontweight="bold")
    clean_axis(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=8)

    label_x = 1.24
    for yi, row in zip(y, plot_df.itertuples(index=False)):
        ax.text(label_x, yi, fmt_hr(row.HR, row.CI_low, row.CI_high), ha="left", va="center", fontsize=12.5)
    ax.text(label_x + 0.02, len(plot_df) - 0.25, "Higher risk", color=RED, ha="left", va="bottom", fontsize=14, fontweight="bold")
    ax.text(label_x + 0.02, len(plot_df) - 0.55, f"P for trend {fmt_p(df['p_trend'].iloc[0])}", ha="left", va="bottom", fontsize=12.5)
    ax.text(0.36, len(plot_df) - 0.25, "Lower risk", color=BLUE, ha="left", va="bottom", fontsize=14, fontweight="bold")
    ax.text(-0.09, 1.04, "a", transform=ax.transAxes, fontsize=20, fontweight="bold", clip_on=False)


def draw_panel_b(ax, df: pd.DataFrame) -> None:
    order = ["Non-dependent", "Rice-dependent"]
    plot_df = df.set_index("group").loc[order].reset_index()
    x = list(range(len(plot_df)))
    vals = plot_df["incidence_per_1000_py"]
    yerr = [vals - plot_df["CI_low"], plot_df["CI_high"] - vals]
    ax.bar(x, vals, color=[RED, BLUE], edgecolor=TEXT, linewidth=0.9, width=0.53, zorder=2)
    ax.errorbar(x, vals, yerr=yerr, fmt="none", ecolor=TEXT, elinewidth=1.1, capsize=4, capthick=1.1, zorder=3)
    for xi, val, hi in zip(x, vals, plot_df["CI_high"]):
        ax.text(xi, hi + 0.20, f"{val:.1f}", ha="center", va="bottom", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(order, fontsize=13)
    ax.set_ylabel("Cases per 1,000 person-years", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 8)
    ax.set_yticks([0, 2, 4, 6, 8])
    ax.grid(axis="y", color=GRID, linestyle=":", linewidth=0.8)
    clean_axis(ax)
    ax.text(-0.16, 1.06, "b", transform=ax.transAxes, fontsize=20, fontweight="bold")


def draw_panel_c(ax, df: pd.DataFrame) -> None:
    plot_df = df[(df["group"] == "Rice-dependent") & df["HR"].notna()].copy()
    model_order = ["Model 3 + cumulative average rice amylose intake", "Model 3"]
    plot_df["model"] = pd.Categorical(plot_df["model"], categories=model_order, ordered=True)
    plot_df = plot_df.sort_values("model")
    y = range(len(plot_df))
    labels = ["Model 3 + cumulative\naverage amylose\nintake", "Model 3"]
    colors = [BLUE_LIGHT, BLUE]
    linestyles = [(0, (5, 5)), "solid"]

    ax.set_xscale("log")
    ax.axvline(1, color=TEXT, lw=1.0, ls=(0, (4, 4)))
    for i, row in enumerate(plot_df.itertuples(index=False)):
        ax.errorbar(
            row.HR,
            list(y)[i],
            xerr=[[row.HR - row.CI_low], [row.CI_high - row.HR]],
            fmt="o",
            ms=8,
            color=colors[i],
            ecolor=colors[i],
            elinewidth=1.3,
            capsize=4,
            capthick=1.3,
            linestyle=linestyles[i],
            zorder=3,
        )
        ax.text(1.78, list(y)[i], fmt_hr(row.HR, row.CI_low, row.CI_high), ha="left", va="center", fontsize=14)

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=11.5)
    ax.set_xlim(0.56, 3.0)
    ax.set_ylim(-0.7, len(plot_df) - 0.3)
    ax.xaxis.set_major_locator(FixedLocator([0.6, 0.8, 1.0, 1.25, 1.6]))
    ax.xaxis.set_major_formatter(FixedFormatter(["0.60", "0.80", "1.00", "1.25", "1.60"]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Hazard ratio for incident type 2 diabetes", fontsize=14, fontweight="bold")
    ax.grid(axis="x", color=GRID, linestyle=":", linewidth=0.8)
    clean_axis(ax)
    ax.tick_params(axis="y", length=0, pad=5)
    ax.text(-0.09, 1.05, "c", transform=ax.transAxes, fontsize=20, fontweight="bold", clip_on=False)


def main() -> None:
    setup_style()
    panel_a, panel_b, panel_c = load_data()

    fig = plt.figure(figsize=(11.2, 7.8), dpi=300)
    gs = fig.add_gridspec(
        2,
        2,
        height_ratios=[1.0, 1.0],
        width_ratios=[1.0, 1.0],
        hspace=0.62,
        wspace=0.50,
        left=0.14,
        right=0.97,
        bottom=0.10,
        top=0.93,
    )
    draw_panel_a(fig.add_subplot(gs[0, 0]), panel_a)
    draw_panel_b(fig.add_subplot(gs[0, 1]), panel_b)
    draw_panel_c(fig.add_subplot(gs[1, 0]), panel_c)
    ax_blank = fig.add_subplot(gs[1, 1])
    ax_blank.axis("off")

    OUT_BASE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_BASE.with_suffix(".png"), dpi=600, facecolor="white")
    fig.savefig(OUT_BASE.with_suffix(".tiff"), dpi=600, facecolor="white", pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(OUT_BASE.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)
    print(OUT_BASE.with_suffix(".png"))
    print(OUT_BASE.with_suffix(".tiff"))
    print(OUT_BASE.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
