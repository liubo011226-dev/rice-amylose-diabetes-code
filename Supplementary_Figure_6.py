from __future__ import annotations

import math
import sys
import textwrap
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


sys.dont_write_bytecode = True

PACKAGE_DIR = Path(__file__).resolve().parents[1]
SOURCE_XLSX = PACKAGE_DIR / "data" / "Supplementary_Figure_rice_quantity_confounding_sensitivity_cumulative_average_source_data.xlsx"
OUT_BASE = PACKAGE_DIR / "output" / "Supplementary_Figure_rice_quantity_confounding_sensitivity_cumulative_average_reproduced_from_source_data"

DPI = 300
W, H = 2600, 1450

BLUE = (46, 71, 128)
TEAL = (0, 121, 107)
OLIVE = (56, 100, 17)
RED = (176, 55, 48)
STEEL = (91, 119, 135)
WHITE = (255, 255, 255)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


F_TITLE = font(70, True)
F_SUB = font(34)
F_HEAD = font(34, True)
F_BODY = font(31)
F_BODY_BOLD = font(31, True)
F_SMALL = font(25)
F_TICK = font(25)


def log_mapper(xmin: float, xmax: float, left: int, right: int):
    log_min = math.log(xmin)
    log_max = math.log(xmax)

    def map_x(value: float) -> int:
        return int(round(left + (math.log(float(value)) - log_min) / (log_max - log_min) * (right - left)))

    return map_x


def draw_wrapped(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt, fill, width: int, gap: int = 5) -> int:
    for line in textwrap.wrap(str(text), width=width, break_long_words=False):
        draw.text((x, y), line, font=fnt, fill=fill, anchor="la")
        y += fnt.size + gap
    return y


def draw_errorbar(draw: ImageDraw.ImageDraw, x: int, lo: int, hi: int, y: int, color) -> None:
    draw.line((lo, y, hi, y), fill=color, width=6)
    draw.line((lo, y - 16, lo, y + 16), fill=color, width=5)
    draw.line((hi, y - 16, hi, y + 16), fill=color, width=5)
    r = 21
    draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def dotted_line(draw: ImageDraw.ImageDraw, xy, fill, width: int = 2, dot: int = 2, gap: int = 13) -> None:
    x0, y0, x1, y1 = xy
    if abs(x1 - x0) >= abs(y1 - y0):
        x = min(x0, x1)
        x_end = max(x0, x1)
        while x < x_end:
            draw.line((x, y0, min(x + dot, x_end), y1), fill=fill, width=width)
            x += dot + gap
    else:
        y = min(y0, y1)
        y_end = max(y0, y1)
        while y < y_end:
            draw.line((x0, y, x1, min(y + dot, y_end)), fill=fill, width=width)
            y += dot + gap


def dashed_line(draw: ImageDraw.ImageDraw, xy, fill, width: int = 2, dash: int = 18, gap: int = 14) -> None:
    x0, y0, x1, y1 = xy
    if abs(x1 - x0) >= abs(y1 - y0):
        x = min(x0, x1)
        x_end = max(x0, x1)
        while x < x_end:
            draw.line((x, y0, min(x + dash, x_end), y1), fill=fill, width=width)
            x += dash + gap
    else:
        y = min(y0, y1)
        y_end = max(y0, y1)
        while y < y_end:
            draw.line((x0, y, x1, min(y + dash, y_end)), fill=fill, width=width)
            y += dash + gap


def p_label(value: str) -> str:
    if not isinstance(value, str) or not value:
        return ""
    return f"P{value}" if value.startswith("<") else f"P={value}"


def plot_summary(summary: pd.DataFrame) -> Image.Image:
    colors = {
        "Main model": BLUE,
        "Quantity-adjusted model": STEEL,
        "Rice consumers only": TEAL,
        "Amylose density/content": OLIVE,
    }
    image = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(image, "RGBA")

    draw.text((50, 36), "Sensitivity analyses addressing rice quantity confounding", font=F_TITLE, fill=(0, 0, 0), anchor="la")
    draw.text(
        (52, 126),
        "Q4 versus Q1 hazard ratios from Cox models for cumulative average rice amylose exposure and incident type 2 diabetes.",
        font=F_SUB,
        fill=(0, 0, 0),
        anchor="la",
    )

    label_left = 55
    plot_left, plot_right = 760, 1950
    value_x, p_x = 2040, 2400
    y_top, y_gap = 360, 215
    y_positions = [y_top + i * y_gap for i in range(4)]
    axis_y = y_positions[-1] + 116
    plot_top = y_top - 86
    map_x = log_mapper(0.005, 3.25, plot_left, plot_right)
    ticks = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 3.0]

    draw.line((plot_left, axis_y, plot_right, axis_y), fill=(0, 0, 0), width=3)
    draw.line((plot_left, plot_top, plot_left, axis_y), fill=(0, 0, 0), width=2)
    for tick in ticks:
        x = map_x(tick)
        draw.line((x, axis_y, x, axis_y + 13), fill=(0, 0, 0), width=2)
        draw.text((x, axis_y + 42), f"{tick:g}", font=F_TICK, fill=(0, 0, 0), anchor="mm")
        if tick != 1.0:
            dotted_line(draw, (x, plot_top, x, axis_y), fill=(165, 165, 165), width=2, dot=2, gap=11)

    ref_x = map_x(1.0)
    dashed_line(draw, (ref_x, plot_top, ref_x, axis_y), fill=(0, 0, 0), width=2, dash=16, gap=14)
    draw.text(((plot_left + plot_right) / 2, axis_y + 78), "Hazard ratio (log scale)", font=F_HEAD, fill=(0, 0, 0), anchor="mm")
    draw.text((map_x(0.15), plot_top - 32), "Lower risk", font=F_BODY, fill=BLUE, anchor="mm")
    draw.text((map_x(1.8), plot_top - 32), "Higher risk", font=F_BODY, fill=RED, anchor="mm")

    for y in [(y_positions[i] + y_positions[i + 1]) / 2 for i in range(3)]:
        dotted_line(draw, (50, int(y), W - 55, int(y)), fill=(160, 160, 160), width=2, dot=2, gap=12)

    ordered = summary.copy().reset_index(drop=True)
    for idx, row in ordered.iterrows():
        y = y_positions[idx]
        color = colors[row["analysis"]]
        draw.text((label_left, y - 68), row["analysis"], font=F_HEAD, fill=(0, 0, 0), anchor="la")
        draw.text((label_left, y - 22), row["exposure_metric"], font=F_BODY, fill=(0, 0, 0), anchor="la")
        draw.text((label_left, y + 26), row["interpretation"], font=F_BODY, fill=(0, 0, 0), anchor="la")
        draw_errorbar(draw, map_x(row["HR"]), map_x(row["CI_low"]), map_x(row["CI_high"]), y, color)
        draw.text((value_x, y - 33), row["HR_95CI"], font=F_BODY_BOLD, fill=(0, 0, 0), anchor="la")
        draw.text((p_x, y - 33), p_label(str(row["p_display"])), font=F_BODY, fill=(0, 0, 0), anchor="la")
        draw_wrapped(draw, value_x, y + 30, row["adjustment"], F_SMALL, (0, 0, 0), width=42, gap=5)

    note = (
        "Main covariates included age group, sex, education, household income, urban/rural residence, BMI category, "
        "physical activity, smoking, alcohol drinking and total energy intake. The rice-intake adjusted model is shown "
        "as a quantity-conditional sensitivity analysis because rice intake is embedded in rice amylose intake."
    )
    draw_wrapped(draw, 55, 1310, note, F_SMALL, (0, 0, 0), width=170, gap=5)
    return image


def main() -> None:
    summary = pd.read_excel(SOURCE_XLSX, sheet_name="Q4 plot data", engine="openpyxl")
    image = plot_summary(summary)
    OUT_BASE.parent.mkdir(parents=True, exist_ok=True)
    png = OUT_BASE.with_suffix(".png")
    tiff = OUT_BASE.with_suffix(".tiff")
    pdf = OUT_BASE.with_suffix(".pdf")
    image.save(png, dpi=(DPI, DPI))
    image.save(tiff, dpi=(DPI, DPI), compression="tiff_lzw")
    image.save(pdf, "PDF", resolution=DPI)
    print(png)
    print(tiff)
    print(pdf)
    print(SOURCE_XLSX)


if __name__ == "__main__":
    main()
