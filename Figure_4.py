from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


PACKAGE_DIR = Path(__file__).resolve().parents[1]
SOURCE_XLSX = PACKAGE_DIR / "data" / "Figure_4_source_data.xlsx"
OUT_BASE = PACKAGE_DIR / "output" / "Figure_4_reproduced_from_source_data"

BLUE = "#08529B"
RED = "#D30000"
GREY = "#777777"
LIGHT_GREY = "#DCE3EA"

DOMAIN_COLORS = {
    "Age": "#0072B2",
    "Sex": "#009E73",
    "Residence": "#D55E00",
    "Education": "#CC79A7",
    "BMI": "#6A994E",
    "Income": "#56B4E9",
    "Physical activity": "#7A5195",
    "Smoking": "#8C564B",
    "Alcohol": "#E69F00",
}

DOMAIN_ORDER = [
    "Age",
    "Sex",
    "Residence",
    "Education",
    "BMI",
    "Income",
    "Physical activity",
    "Smoking",
    "Alcohol",
]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sheets = pd.read_excel(SOURCE_XLSX, sheet_name=None, engine="openpyxl")
    return (
        sheets["Figure_4a_subgroup_HR"],
        sheets["Figure_4b_absolute_cases"],
        sheets["Figure_4c_scatter"],
        sheets["Figure_4d_contribution"],
    )


def fmt_hr(hr: float, lo: float, hi: float) -> str:
    if not np.isfinite(hr) or not np.isfinite(lo) or not np.isfinite(hi):
        return ""
    return f"{hr:.2f} ({lo:.2f}, {hi:.2f})"


def add_risk_arrows(ax, y: float = 1.04) -> None:
    ax.annotate(
        "",
        xy=(0.31, y),
        xytext=(0.42, y),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.4),
        clip_on=False,
    )
    ax.annotate(
        "",
        xy=(0.70, y),
        xytext=(0.57, y),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.4),
        clip_on=False,
    )
    ax.text(0.365, y + 0.025, "Lower risk", transform=ax.transAxes, ha="center", va="bottom", color=BLUE, fontweight="bold")
    ax.text(0.635, y + 0.025, "Higher risk", transform=ax.transAxes, ha="center", va="bottom", color=RED, fontweight="bold")


def panel_a(ax, data: pd.DataFrame) -> None:
    rows = data.copy().reset_index(drop=True)
    y = np.arange(len(rows))[::-1]
    ax.set_xscale("log")
    ax.set_xlim(0.45, 2.2)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.axvline(1, color=GREY, linestyle="--", lw=1.0, dashes=(3, 3), zorder=0)
    ax.grid(axis="x", color=LIGHT_GREY, lw=0.7, zorder=0)

    finite = rows["scenario_HR"].notna()
    ax.errorbar(
        rows.loc[finite, "scenario_HR"],
        y[finite],
        xerr=[
            rows.loc[finite, "scenario_HR"] - rows.loc[finite, "scenario_CI_low"],
            rows.loc[finite, "scenario_CI_high"] - rows.loc[finite, "scenario_HR"],
        ],
        fmt="s",
        color=BLUE,
        ecolor=BLUE,
        markersize=4.5,
        elinewidth=1.4,
        capsize=2.5,
        capthick=1.1,
        zorder=3,
    )

    labels = []
    previous_domain = None
    for _, row in rows.iterrows():
        domain = row["domain"]
        level = row["subgroup"]
        prefix = domain if domain != previous_domain else ""
        labels.append(f"{prefix:<18}  {level}")
        previous_domain = domain
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontfamily="Times New Roman")
    ax.set_xticks([0.5, 1.0, 2.0])
    ax.set_xticklabels(["0.5", "1", "2"])
    ax.set_xlabel("Hazard ratio (log scale)", fontweight="bold")
    ax.set_title("Subgroup HR (forest plot for +4 pp scenario)", loc="left", fontweight="bold")
    add_risk_arrows(ax)

    for yy, row in zip(y, rows.itertuples(index=False)):
        ax.text(2.52, yy, fmt_hr(row.scenario_HR, row.scenario_CI_low, row.scenario_CI_high),
                ha="left", va="center", clip_on=False, fontweight="bold" if np.isfinite(row.scenario_HR) else "normal")
    ax.text(2.52, len(rows) - 0.15, "HR (95% CI)", ha="left", va="bottom", clip_on=False, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)


def panel_b(ax, data: pd.DataFrame) -> None:
    rows = data.copy().reset_index(drop=True)
    scenarios = ["+1 pp", "+2 pp", "+4 pp"]
    vals = rows[scenarios].to_numpy(dtype=float)
    cmap = LinearSegmentedColormap.from_list("blue_white_red", ["#08529B", "#F8F8F8", "#D30000"])
    im = ax.imshow(vals, cmap=cmap, vmin=0, vmax=10, aspect="auto")
    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels(scenarios, fontweight="bold")
    labels = []
    previous_domain = None
    for _, row in rows.iterrows():
        domain = row["domain"]
        level = row["subgroup"]
        prefix = domain if domain != previous_domain else ""
        labels.append(f"{prefix:<18}  {level}")
        previous_domain = domain
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels, fontfamily="Times New Roman")
    ax.set_title("Absolute cases fewer per 10,000 person-years", loc="left", fontweight="bold")

    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            if np.isfinite(vals[i, j]):
                color = "white" if vals[i, j] <= 1.2 or vals[i, j] >= 7 else "#111111"
                ax.text(j, i, f"{vals[i, j]:.1f}", ha="center", va="center", color=color, fontweight="bold", fontsize=8)
    ax.set_xticks(np.arange(-0.5, len(scenarios), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.spines[:].set_visible(False)
    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.10)
    cbar.ax.set_title("Cases fewer\nper 10,000 PY", fontsize=8, pad=8)


def panel_c(ax, data: pd.DataFrame) -> None:
    rows = data.copy()
    for domain in DOMAIN_ORDER:
        sub = rows[rows["domain"].eq(domain)]
        if sub.empty:
            continue
        sizes = 25 + 180 * np.sqrt(sub["n"].astype(float) / rows["n"].max())
        ax.scatter(
            sub["baseline_incidence_per_1000_py"],
            sub["cases_fewer_per_10000_py"],
            s=sizes,
            color=DOMAIN_COLORS[domain],
            edgecolor="white",
            linewidth=1.2,
            alpha=0.95,
            label=domain,
        )
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.grid(True, linestyle="--", color="#CFD8E3", linewidth=0.8, alpha=0.85)
    ax.set_xlabel("Baseline incidence rate (cases per 1,000 PY)", fontweight="bold")
    ax.set_ylabel("Absolute cases fewer per 10,000 PY (+4 pp scenario)", fontweight="bold")
    ax.set_title("Baseline incidence and projected absolute reduction", loc="left", fontweight="bold")
    ax.legend(title="Domain", frameon=False, bbox_to_anchor=(1.03, 1.0), loc="upper left", fontsize=8, title_fontsize=9)
    for size, lab in zip([1000, 3000, 6000], ["1,000", "3,000", "6,000"]):
        ax.scatter([], [], s=25 + 180 * np.sqrt(size / rows["n"].max()), facecolors="none", edgecolors="black", label=lab)
    ax.spines[["top", "right"]].set_visible(False)


def panel_d(ax, data: pd.DataFrame) -> None:
    domains = ["Age", "Residence", "Education", "BMI"]
    colors = ["#0D47A1", "#D30000", "#666666"]
    y = np.arange(len(domains))[::-1]
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.8, len(domains) - 0.2)
    for yi, domain in zip(y, domains):
        sub = data[data["domain"].eq(domain)].copy()
        left = 0
        for j, row in enumerate(sub.itertuples(index=False)):
            width = row.contribution_percent
            ax.barh(yi, width, left=left, color=colors[j % len(colors)], height=0.35)
            if width >= 4:
                ax.text(left + width / 2, yi, f"{width:.0f}%", ha="center", va="center", color="white", fontweight="bold")
            left += width
    ax.set_yticks(y)
    ax.set_yticklabels(domains, fontweight="bold")
    ax.set_xlabel("Share of total modelled cases fewer", fontweight="bold")
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xticklabels([f"{i}%" for i in [0, 20, 40, 60, 80, 100]])
    ax.set_title("Population-weighted contribution to modelled cases fewer", loc="left", fontweight="bold")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

    legend_rows = [
        ("Age", ["18-45 years", ">45 years"]),
        ("Residence", ["Rural", "Urban"]),
        ("Education", ["Low", "Middle", "High"]),
        ("BMI", ["Normal", "Overweight", "Obese"]),
    ]
    handles, labels = [], []
    for _, levels in legend_rows:
        for j, level in enumerate(levels):
            handles.append(mpl.patches.Patch(color=colors[j % len(colors)]))
            labels.append(level)
    ax.legend(handles, labels, frameon=False, bbox_to_anchor=(1.03, 1.0), loc="upper left", fontsize=8)


def main() -> None:
    a, b, c, d = load_data()
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.serif": ["Times New Roman"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
        }
    )
    fig = plt.figure(figsize=(16, 11), dpi=300)
    gs = fig.add_gridspec(2, 2, left=0.06, right=0.92, top=0.94, bottom=0.12, wspace=0.65, hspace=0.42)
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
    ]
    panel_a(axes[0], a)
    panel_b(axes[1], b)
    panel_c(axes[2], c)
    panel_d(axes[3], d)
    for letter, ax in zip("abcd", axes):
        ax.text(-0.12, 1.08, letter, transform=ax.transAxes, fontsize=20, fontweight="bold", va="top")
    fig.text(
        0.06,
        0.035,
        "HR, hazard ratio; CI, confidence interval; BMI, body mass index; PY, person-years. "
        "Absolute cases fewer were modelled from subgroup crude incidence rates and scenario HRs; "
        "they should be interpreted as projected impacts rather than observed intervention effects.",
        fontsize=8,
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
