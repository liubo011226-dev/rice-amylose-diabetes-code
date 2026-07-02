from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


PACKAGE_DIR = Path(__file__).resolve().parents[1]
SOURCE_XLSX = PACKAGE_DIR / "data" / "Figure_2_source_data.xlsx"
OUT_BASE = PACKAGE_DIR / "output" / "Figure_2_reproduced_from_source_data"

BLUE = "#155A8A"
BLUE2 = "#0b4aa2"
RED = "#d60000"
TEXT = "#222222"
GREY = "#777777"
LIGHT_GREY = "#d9d9d9"
FONT_SCALE = 1.8


def fs(size: float) -> float:
    return size * FONT_SCALE


def fmt_hr(hr: float, lo: float, hi: float, digits: int = 2) -> str:
    return f"{hr:.{digits}f} ({lo:.{digits}f}, {hi:.{digits}f})"


def axis_fraction_for_x(ax, x: float) -> float:
    xmin, xmax = ax.get_xlim()
    if ax.get_xscale() == "log":
        return (math.log(x) - math.log(xmin)) / (math.log(xmax) - math.log(xmin))
    return (x - xmin) / (xmax - xmin)


def add_risk_arrows(
    ax,
    ref_x: float = 1.0,
    y: float = 1.05,
    gap: float = 0.065,
    blue_len: float = 0.12,
    red_len: float = 0.12,
    fontsize: float = 21,
) -> None:
    ref = axis_fraction_for_x(ax, ref_x)
    blue_end = ref - gap
    blue_start = blue_end - blue_len
    red_start = ref + gap
    red_end = red_start + red_len
    text_y = y + 0.035
    ax.annotate(
        "",
        xy=(blue_start, y),
        xytext=(blue_end, y),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=BLUE2, lw=1.1, shrinkA=0, shrinkB=0),
        clip_on=False,
    )
    ax.annotate(
        "",
        xy=(red_end, y),
        xytext=(red_start, y),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.1, shrinkA=0, shrinkB=0),
        clip_on=False,
    )
    ax.text(
        (blue_start + blue_end) / 2,
        text_y,
        "Lower risk",
        transform=ax.transAxes,
        color=BLUE2,
        ha="center",
        va="bottom",
        fontsize=fontsize,
        clip_on=False,
    )
    ax.text(
        (red_start + red_end) / 2,
        text_y,
        "Higher risk",
        transform=ax.transAxes,
        color=RED,
        ha="center",
        va="bottom",
        fontsize=fontsize,
        clip_on=False,
    )


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sheets = pd.read_excel(SOURCE_XLSX, sheet_name=None, engine="openpyxl")
    return (
        sheets["Figure_2a_crude_incidence"],
        sheets["Figure_2b_quartile_HR"],
        sheets["Figure_2c_increment_HR"],
        sheets["Figure_2d_sensitivity"],
    )


def plot_forest(
    ax,
    df: pd.DataFrame,
    label_col: str,
    color: str,
    marker: str,
    xlim: tuple[float, float],
    xticks: list[float],
    digits: int = 2,
    title: str | None = None,
    show_arrows: bool = True,
    hr_text_x_data: float | None = None,
) -> None:
    y = list(range(len(df)))[::-1]
    ax.set_xscale("log")
    ax.errorbar(
        df["HR"],
        y,
        xerr=[df["HR"] - df["CI_low"], df["CI_high"] - df["HR"]],
        fmt=marker,
        color=color,
        ecolor=color,
        elinewidth=2.2,
        markersize=10.5,
        capsize=6.0,
        capthick=2.0,
        lw=2.0,
    )
    ax.axvline(1, color=GREY, ls="--", lw=0.95, dashes=(3, 3), zorder=0)
    ax.set_xlim(*xlim)
    ax.set_yticks(y)
    ax.set_yticklabels(df[label_col])
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{t:g}" for t in xticks])
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xlabel("Hazard ratio (log scale)", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", width=1.1, length=4.5)
    if show_arrows:
        add_risk_arrows(ax, fontsize=fs(11.5))
    if title:
        ax.set_title(title, loc="left", fontweight="bold", pad=12)
    if hr_text_x_data is None:
        for yi, row in zip(y, df.itertuples(index=False)):
            ax.text(
                1.12,
                yi,
                fmt_hr(row.HR, row.CI_low, row.CI_high, digits=digits),
                transform=ax.get_yaxis_transform(),
                va="center",
                ha="left",
                fontsize=fs(12.8),
                clip_on=False,
            )
        ax.text(
            1.12,
            1.055,
            "HR (95% CI)",
            transform=ax.transAxes,
            ha="left",
            va="center",
            fontsize=fs(13.5),
            fontweight="bold",
            clip_on=False,
        )
    else:
        for yi, row in zip(y, df.itertuples(index=False)):
            ax.text(
                hr_text_x_data,
                yi,
                fmt_hr(row.HR, row.CI_low, row.CI_high, digits=digits),
                va="center",
                ha="left",
                fontsize=fs(12.8),
                clip_on=False,
            )
        ax.text(
            hr_text_x_data,
            max(y) + 0.82,
            "HR (95% CI)",
            ha="left",
            va="center",
            fontsize=fs(13.5),
            fontweight="bold",
            clip_on=False,
        )


def main() -> None:
    crude, quartile, scenario, sens = load_data()

    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.serif": ["Times New Roman"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 1.25,
            "axes.labelsize": fs(14.2),
            "axes.titlesize": fs(15.0),
            "xtick.labelsize": fs(13.0),
            "ytick.labelsize": fs(13.0),
            "text.color": TEXT,
            "axes.labelcolor": TEXT,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
        }
    )

    fig = plt.figure(figsize=(25.5, 17.4), dpi=300)
    gs = fig.add_gridspec(
        2,
        2,
        left=0.085,
        right=0.915,
        bottom=0.09,
        top=0.91,
        wspace=0.88,
        hspace=0.76,
        width_ratios=[1.0, 1.05],
        height_ratios=[1.0, 1.0],
    )

    ax_a = fig.add_subplot(gs[0, 0])
    x = list(range(len(crude)))
    vals = crude["incidence_per_1000_py"].to_numpy()
    lo = crude["incidence_low"].to_numpy()
    hi = crude["incidence_high"].to_numpy()
    yerr = [vals - lo, hi - vals]
    ax_a.set_axisbelow(True)
    ax_a.bar(x, vals, width=0.46, color=BLUE, edgecolor=BLUE, linewidth=1.1, zorder=3)
    ax_a.errorbar(x, vals, yerr=yerr, fmt="none", ecolor="#111111", elinewidth=1.25, capsize=4, capthick=1.25, zorder=4)
    for xi, v, hi_v in zip(x, vals, hi):
        ax_a.text(xi, hi_v + 0.18, f"{v:.1f}", ha="center", va="bottom", fontsize=fs(13.8))
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(crude["quartile"])
    ax_a.set_ylim(0, 8.5)
    ax_a.set_yticks([0, 2, 4, 6, 8])
    ax_a.set_ylabel("Cases per 1,000 person-years", labelpad=12)
    ax_a.set_xlabel("Quartile of cumulative-average rice amylose intake", fontweight="bold")
    ax_a.grid(axis="y", color=LIGHT_GREY, lw=0.8, linestyle=(0, (3, 3)), zorder=0)
    ax_a.spines["top"].set_visible(False)
    ax_a.spines["right"].set_visible(False)
    ax_a.tick_params(axis="both", width=1.1, length=4.5)
    ax_a.set_title("Crude incidence rates", loc="left", fontweight="bold", pad=12)

    plot_forest(
        fig.add_subplot(gs[0, 1]),
        quartile,
        "comparison",
        BLUE2,
        "s",
        (0.34, 1.22),
        [0.4, 0.6, 0.8, 1.0, 1.2],
        digits=2,
        title="Quartile model",
    )

    plot_forest(
        fig.add_subplot(gs[1, 0]),
        scenario,
        "scenario",
        RED,
        "o",
        (0.885, 1.065),
        [0.90, 0.94, 0.98, 1.00],
        digits=3,
        title="Continuous exposure increments",
        show_arrows=False,
        hr_text_x_data=1.018,
    )

    ax_d = fig.add_subplot(gs[1, 1])
    y = list(range(len(sens)))[::-1]
    ax_d.set_xscale("log")
    colors = [BLUE2, "#737373", "#008B8B", "#4F7F2A", "#7A5195"]
    for yi, row, col in zip(y, sens.itertuples(index=False), colors):
        ax_d.errorbar(
            row.HR,
            yi,
            xerr=[[row.HR - row.CI_low], [row.CI_high - row.HR]],
            fmt="s",
            color=col,
            ecolor=col,
            elinewidth=2.2,
            markersize=10.5,
            capsize=6.0,
            capthick=2.0,
            lw=2.0,
        )
    ax_d.axvline(1, color=GREY, ls="--", lw=0.95, dashes=(3, 3), zorder=0)
    ax_d.set_xlim(0.30, 1.25)
    ax_d.set_ylim(-0.55, len(sens) - 0.25)
    ax_d.set_yticks(y)
    ax_d.set_yticklabels(sens["analysis"])
    ax_d.set_xticks([0.4, 0.6, 0.8, 1.0, 1.2])
    ax_d.set_xticklabels(["0.4", "0.6", "0.8", "1", "1.2"])
    ax_d.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax_d.set_xlabel("Hazard ratio (log scale)", fontweight="bold")
    ax_d.set_title("Key sensitivity analyses", loc="left", fontweight="bold", pad=12)
    ax_d.spines["top"].set_visible(False)
    ax_d.spines["right"].set_visible(False)
    ax_d.tick_params(axis="both", width=1.1, length=4.5)
    add_risk_arrows(ax_d, fontsize=fs(11.5))
    for yi, row in zip(y, sens.itertuples(index=False)):
        ax_d.text(
            1.12,
            yi,
            row.HR_95CI,
            transform=ax_d.get_yaxis_transform(),
            va="center",
            ha="left",
            fontsize=fs(12.8),
            clip_on=False,
        )
    ax_d.text(
        1.12,
        1.055,
        "HR (95% CI)",
        transform=ax_d.transAxes,
        ha="left",
        va="center",
        fontsize=fs(13.5),
        fontweight="bold",
        clip_on=False,
    )

    for letter, ax in zip("abcd", fig.axes):
        pos = ax.get_position()
        fig.text(
            pos.x0 - 0.05,
            pos.y1 + 0.02,
            letter,
            fontsize=fs(28),
            fontweight="bold",
            fontfamily="Times New Roman",
        )

    OUT_BASE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_BASE.with_suffix(".png"), dpi=600, bbox_inches="tight")
    fig.savefig(OUT_BASE.with_suffix(".tiff"), dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(OUT_BASE.with_suffix(".pdf"), bbox_inches="tight")
    print(OUT_BASE.with_suffix(".png"))
    print(OUT_BASE.with_suffix(".tiff"))
    print(OUT_BASE.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
