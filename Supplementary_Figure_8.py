from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


PACKAGE_DIR = Path(__file__).resolve().parent
SOURCE_XLSX = PACKAGE_DIR / "Source_data.xlsx"
OUTPUT_DIR = PACKAGE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_STEM = "Reproduced_amylose_energy_contribution"


def fmt_p(value):
    if pd.isna(value):
        return ""
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def fmt_hr(hr, lo, hi):
    return f"{hr:.2f} ({lo:.2f}, {hi:.2f})"


def clean_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.15)
    ax.spines["bottom"].set_linewidth(1.15)
    ax.tick_params(width=1.0, length=5, labelsize=11)


def log_tick_formatter(x, _pos):
    if x >= 1:
        return f"{x:.1f}".rstrip("0").rstrip(".")
    return f"{x:.2f}".rstrip("0").rstrip(".")


quartile = pd.read_excel(SOURCE_XLSX, sheet_name="Figure_5.a")
increments = pd.read_excel(SOURCE_XLSX, sheet_name="Figure_5.b")
rcs = pd.read_excel(SOURCE_XLSX, sheet_name="Figure_5.c")
tests = pd.read_excel(SOURCE_XLSX, sheet_name="Figure_5.tests")

plt.rcParams.update(
    {
        "font.family": "Times New Roman",
        "font.size": 11,
        "axes.labelsize": 15,
        "axes.labelweight": "bold",
        "xtick.labelsize": 11,
        "ytick.labelsize": 12,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

blue = "#0b4ea2"
red = "#d90000"

fig = plt.figure(figsize=(12.8, 8.6), dpi=300)
gs = fig.add_gridspec(
    2,
    2,
    height_ratios=[1.0, 1.35],
    width_ratios=[1.18, 1.0],
    hspace=0.62,
    wspace=0.60,
)

# Panel a: cumulative-average amylose-energy quartiles.
ax_a = fig.add_subplot(gs[0, 0])
panel_a = quartile[quartile["quartile"].isin(["Q2", "Q3", "Q4"])].copy()
panel_a["y"] = [3, 2, 1]
ax_a.axvline(1, color="black", lw=1.0, ls=(0, (4, 4)), zorder=0)
ax_a.errorbar(
    panel_a["HR"],
    panel_a["y"],
    xerr=[panel_a["HR"] - panel_a["CI_low"], panel_a["CI_high"] - panel_a["HR"]],
    fmt="s",
    color=blue,
    ecolor=blue,
    elinewidth=1.6,
    capsize=4,
    markersize=8,
    markerfacecolor=blue,
    markeredgecolor=blue,
    zorder=3,
)
ax_a.set_xscale("log")
ax_a.set_xlim(0.35, 2.10)
ax_a.set_ylim(0.45, 3.65)
ax_a.set_yticks([3, 2, 1])
ax_a.set_yticklabels(["Q2 vs Q1", "Q3 vs Q1", "Q4 vs Q1"])
ax_a.set_xticks([0.4, 0.6, 1.0, 1.5, 2.0])
ax_a.xaxis.set_major_formatter(FuncFormatter(log_tick_formatter))
ax_a.set_xlabel("Hazard ratio (log scale)", labelpad=8)
clean_axis(ax_a)
ax_a.tick_params(axis="y", pad=8)
ax_a.text(-0.16, 1.16, "a", transform=ax_a.transAxes, fontsize=22, fontweight="bold")
ax_a.text(1.18, 3.48, "P for trend <0.001", fontsize=12)
ax_a.text(1.18, 3.73, "HR (95% CI)", fontsize=12, fontweight="bold")
for _, row in panel_a.iterrows():
    ax_a.text(1.18, row["y"], fmt_hr(row["HR"], row["CI_low"], row["CI_high"]), va="center", fontsize=12)

# Panel b: predefined energy-contribution increments.
ax_b = fig.add_subplot(gs[0, 1])
ax_b.axvline(1, color="black", lw=1.0, ls=(0, (4, 4)), zorder=0)
ax_b.errorbar(
    increments["HR"],
    increments["y"],
    xerr=[increments["HR"] - increments["CI_low"], increments["CI_high"] - increments["HR"]],
    fmt="s",
    color=blue,
    ecolor=blue,
    elinewidth=1.6,
    capsize=4,
    markersize=7,
    markerfacecolor=blue,
    markeredgecolor=blue,
    zorder=3,
)
ax_b.set_xscale("log")
ax_b.set_xlim(0.80, 1.15)
ax_b.set_ylim(0.45, 3.65)
ax_b.set_yticks([3, 2, 1])
ax_b.set_yticklabels(increments["label"])
ax_b.set_xticks([0.8, 0.9, 1.0])
ax_b.xaxis.set_major_formatter(FuncFormatter(log_tick_formatter))
ax_b.set_xlabel("Hazard ratio (log scale)", labelpad=8)
clean_axis(ax_b)
ax_b.tick_params(axis="y", pad=8)
ax_b.text(-0.17, 1.16, "b", transform=ax_b.transAxes, fontsize=22, fontweight="bold")
ax_b.text(1.055, 3.52, "HR (95% CI)", fontsize=12, fontweight="bold")
for _, row in increments.iterrows():
    ax_b.text(1.055, row["y"], row["HR_95CI"], va="center", fontsize=12)

# Panel c: restricted cubic spline.
ax_c = fig.add_subplot(gs[1, 0])
ax_note = fig.add_subplot(gs[1, 1])
ax_note.axis("off")
x = rcs["cumulative_amylose_energy_pct"]
ax_c.fill_between(x, rcs["CI_low"], rcs["CI_high"], color="#f4b4b4", alpha=0.42, linewidth=0)
ax_c.plot(x, rcs["HR"], color=red, lw=2.6, solid_capstyle="round")
ax_c.axhline(1.0, color="#444444", lw=0.9)

ref = float(tests.loc[0, "reference_pct"])
upper_marker = float(tests.loc[0, "boundary_99th_pct"])
for xpos in [ref, upper_marker]:
    ypos = np.interp(xpos, x, rcs["HR"])
    ax_c.axvline(xpos, color="black", lw=0.9, ls=(0, (4, 3)))
    ax_c.scatter([xpos], [ypos], s=42, color="black", zorder=5)
    ax_c.text(xpos, ypos + 0.08, f"{xpos:.1f}%", ha="center", va="bottom", fontsize=11)

ax_c.set_xlim(0, max(21.0, upper_marker + 0.4))
ax_c.set_ylim(0.45, 2.05)
ax_c.set_xticks([0, 5, 10, 15, 20])
ax_c.set_yticks([0.5, 1.0, 1.5, 2.0])
ax_c.set_xlabel("Cumulative average rice amylose energy\ncontribution (% energy)", labelpad=8)
ax_c.set_ylabel("Hazard ratio", labelpad=10)
clean_axis(ax_c)
ax_c.text(-0.055, 1.08, "c", transform=ax_c.transAxes, fontsize=22, fontweight="bold")

box_text = (
    f"P overall = {fmt_p(float(tests.loc[0, 'p_overall']))}\n\n"
    f"P nonlinear = {fmt_p(float(tests.loc[0, 'p_nonlinear']))}\n\n"
    f"Reference = {ref:.1f}% energy"
)
ax_note.text(
    0.04,
    0.72,
    box_text,
    transform=ax_note.transAxes,
    fontsize=13,
    va="top",
    bbox=dict(
        boxstyle="round,pad=0.55,rounding_size=0.05",
        facecolor="white",
        edgecolor="#aeb6c2",
        linewidth=0.8,
    ),
)

fig.subplots_adjust(left=0.08, right=0.96, top=0.94, bottom=0.10)

for ext in ("png", "pdf", "tiff"):
    out = OUTPUT_DIR / f"{OUT_STEM}.{ext}"
    if ext == "png":
        fig.savefig(out, dpi=600, facecolor="white")
    elif ext == "tiff":
        fig.savefig(out, dpi=600, facecolor="white", pil_kwargs={"compression": "tiff_lzw"})
    else:
        fig.savefig(out, facecolor="white")

print(f"Saved outputs to: {OUTPUT_DIR}")
