from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


PACKAGE_DIR = Path(__file__).resolve().parents[1]
SOURCE_XLSX = PACKAGE_DIR / "data" / "Figure_3_source_data.xlsx"
OUT_BASE = PACKAGE_DIR / "output" / "Figure_3_reproduced_from_source_data"

BLUE = "#0b4aa2"
RED = "#d60000"
INK = "#222222"
GREY = "#777777"


def load_data() -> pd.DataFrame:
    return pd.read_excel(SOURCE_XLSX, sheet_name="Figure_3_full_source_data", engine="openpyxl")


def add_risk_arrows(ax, ref_x=1.0, y=1.09, gap=0.025, blue_len=0.19, red_len=0.16) -> None:
    xmin, xmax = ax.get_xlim()
    ref = (math.log(ref_x) - math.log(xmin)) / (math.log(xmax) - math.log(xmin))
    blue_end = ref - gap
    blue_start = blue_end - blue_len
    red_start = ref + gap
    red_end = red_start + red_len
    ax.annotate(
        "",
        xy=(blue_start, y),
        xytext=(blue_end, y),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.2, shrinkA=0, shrinkB=0),
        clip_on=False,
    )
    ax.annotate(
        "",
        xy=(red_end, y),
        xytext=(red_start, y),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.2, shrinkA=0, shrinkB=0),
        clip_on=False,
    )
    ax.text((blue_start + blue_end) / 2, y + 0.05, "Lower risk", transform=ax.transAxes, color=BLUE, ha="center", va="bottom", fontsize=14, clip_on=False)
    ax.text(red_start + red_len * 0.85, y + 0.05, "Higher risk", transform=ax.transAxes, color=RED, ha="center", va="bottom", fontsize=14, clip_on=False)


def make_figure(df: pd.DataFrame):
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.serif": ["Times New Roman"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 1.4,
            "axes.labelsize": 16,
            "xtick.labelsize": 13,
            "ytick.labelsize": 13,
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
        }
    )

    y = np.arange(len(df))[::-1]
    fig = plt.figure(figsize=(13.2, 5.2), dpi=300)
    ax_a = fig.add_axes([0.14, 0.20, 0.27, 0.55])
    ax_cases = fig.add_axes([0.58, 0.20, 0.13, 0.55])
    ax_savings = fig.add_axes([0.76, 0.20, 0.20, 0.55])

    ax_a.set_xscale("log")
    ax_a.errorbar(
        df["HR"],
        y,
        xerr=[df["HR"] - df["CI_low"], df["CI_high"] - df["HR"]],
        fmt="o",
        color=RED,
        ecolor=RED,
        markersize=8,
        elinewidth=1.35,
        capsize=4,
        capthick=1.35,
        lw=1.35,
    )
    ax_a.axvline(1, color=GREY, ls="--", lw=1.0, dashes=(3, 3), zorder=0)
    ax_a.set_xlim(0.88, 1.10)
    ax_a.set_ylim(-0.5, 2.5)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels(df["scenario_label"])
    ax_a.xaxis.set_major_locator(mticker.FixedLocator([0.90, 0.95, 1.00, 1.05, 1.10]))
    ax_a.xaxis.set_major_formatter(mticker.FixedFormatter(["0.90", "0.95", "1.00", "1.05", "1.10"]))
    ax_a.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax_a.set_xlabel("Hazard ratio (log scale)", fontweight="bold")
    for sp in ["top", "right"]:
        ax_a.spines[sp].set_visible(False)
    ax_a.tick_params(axis="both", width=1.2, length=5)
    add_risk_arrows(ax_a)
    ax_a.text(1.045, 2.28, "HR (95% CI)", ha="left", va="center", fontsize=13.5, fontweight="bold")
    for yy, row in zip(y, df.itertuples(index=False)):
        ax_a.text(1.045, yy, f"{row.HR:.3f}\n({row.CI_low:.3f}, {row.CI_high:.3f})", ha="left", va="center", fontsize=13)

    def draw_bar_panel(ax, value_col, low_col, high_col, color, xlim, xlabel, label_color):
        values = df[value_col].to_numpy()
        lows = df[low_col].to_numpy()
        highs = df[high_col].to_numpy()
        ax.barh(y, values, color=color, height=0.32)
        ax.errorbar(
            values,
            y,
            xerr=[values - lows, highs - values],
            fmt="none",
            ecolor=INK,
            elinewidth=1.2,
            capsize=5,
            capthick=1.2,
        )
        ax.set_xlim(*xlim)
        ax.set_ylim(-0.5, 2.5)
        ax.set_yticks(y)
        ax.set_yticklabels(df["scenario_label"])
        ax.set_xlabel(xlabel, fontweight="bold")
        for sp in ["top", "right"]:
            ax.spines[sp].set_visible(False)
        ax.tick_params(axis="both", width=1.2, length=5)
        for yy, val, high in zip(y, values, highs):
            label_x = high + (xlim[1] - xlim[0]) * 0.035
            ax.text(label_x, yy, f"{val:.1f}", color=label_color, va="center", ha="left", fontsize=13.5)

    draw_bar_panel(
        ax_cases,
        "cases_reduced_per_10000_at_risk",
        "cases_reduced_per_10000_low",
        "cases_reduced_per_10000_high",
        BLUE,
        (0, 42),
        "Cases reduced\nper 10,000 at risk",
        BLUE,
    )
    draw_bar_panel(
        ax_savings,
        "annual_medical_savings_cny_billion",
        "annual_medical_savings_cny_billion_low",
        "annual_medical_savings_cny_billion_high",
        RED,
        (0, 160),
        "Savings\n(billion CNY/year)",
        RED,
    )
    ax_savings.set_yticklabels([])
    ax_savings.tick_params(axis="y", length=0)

    fig.text(0.035, 0.87, "a", fontsize=28, fontweight="bold", fontfamily="Times New Roman")
    fig.text(0.48, 0.87, "b", fontsize=28, fontweight="bold", fontfamily="Times New Roman")
    return fig


def main() -> None:
    df = load_data()
    fig = make_figure(df)
    OUT_BASE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_BASE.with_suffix(".png"), dpi=600, bbox_inches="tight")
    fig.savefig(OUT_BASE.with_suffix(".tiff"), dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(OUT_BASE.with_suffix(".pdf"), bbox_inches="tight")
    print(OUT_BASE.with_suffix(".png"))
    print(OUT_BASE.with_suffix(".tiff"))
    print(OUT_BASE.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
