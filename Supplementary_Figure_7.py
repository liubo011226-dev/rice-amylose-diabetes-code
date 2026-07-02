from __future__ import annotations

import math
import sys
import textwrap
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


sys.dont_write_bytecode = True

PACKAGE_DIR = Path(__file__).resolve().parent
SOURCE_XLSX = PACKAGE_DIR / "Source_data.xlsx"
OUT_DIR = PACKAGE_DIR / "output"
OUT_BASE = OUT_DIR / "Reproduced_figure"

DPI = 300
W, H = 2400, 1350

INK = (25, 25, 25)
GREY = (95, 100, 108)
GRID = (222, 226, 232)
BLUE = (11, 79, 156)
TEAL = (0, 121, 107)
RED = (190, 40, 45)
WHITE = (255, 255, 255)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


F_TITLE = font(52, True)
F_SUBTITLE = font(31)
F_PANEL = font(42, True)
F_AXIS = font(33, True)
F_TEXT = font(30)
F_SMALL = font(26)
F_TICK = font(25)


def dashed_line(draw: ImageDraw.ImageDraw, xy, fill=GREY, width: int = 3, dash: int = 14, gap: int = 12) -> None:
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


def log_mapper(xmin: float, xmax: float, left: int, right: int):
    log_min = math.log(xmin)
    log_max = math.log(xmax)

    def map_x(value: float) -> int:
        return int(round(left + (math.log(float(value)) - log_min) / (log_max - log_min) * (right - left)))

    return map_x


def draw_errorbar(draw: ImageDraw.ImageDraw, x: int, x_low: int, x_high: int, y: int, color, marker: str) -> None:
    draw.line((x_low, y, x_high, y), fill=color, width=5)
    cap = 15
    draw.line((x_low, y - cap, x_low, y + cap), fill=color, width=5)
    draw.line((x_high, y - cap, x_high, y + cap), fill=color, width=5)
    if marker == "square":
        s = 19
        draw.rectangle((x - s, y - s, x + s, y + s), fill=color)
    else:
        r = 20
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def draw_wrapped(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt, fill, width: int, gap: int = 5) -> None:
    for line in textwrap.wrap(text, width=width, break_long_words=False):
        draw.text((x, y), line, font=fnt, fill=fill, anchor="la")
        y += fnt.size + gap


def draw_panel(
    draw: ImageDraw.ImageDraw,
    panel_tag: str,
    title: str,
    df: pd.DataFrame,
    frame: tuple[int, int, int, int],
    xmin: float,
    xmax: float,
    ticks: list[float],
    color,
    marker: str,
    lower_risk_x: float,
) -> None:
    left, top, right, bottom = frame
    model_order = [
        "Main Model 3",
        "Model 3 + baseline survey year FE",
        "Model 3 + baseline province FE",
        "Model 3 + baseline year + province FE",
    ]
    labels = {
        "Main Model 3": "Main Model 3",
        "Model 3 + baseline survey year FE": "+ baseline year FE",
        "Model 3 + baseline province FE": "+ baseline province FE",
        "Model 3 + baseline year + province FE": "+ year + province FE",
    }
    y_positions = {model: top + 120 + idx * 130 for idx, model in enumerate(model_order)}
    map_x = log_mapper(xmin, xmax, left + 330, right - 260)

    draw.text((left, top - 60), panel_tag, font=F_PANEL, fill=INK, anchor="la")
    draw.text((left + 58, top - 53), title, font=F_AXIS, fill=INK, anchor="la")
    axis_left = left + 330
    axis_right = right - 260
    axis_y = bottom - 65
    draw.line((axis_left, axis_y, axis_right, axis_y), fill=INK, width=4)
    draw.line((axis_left, top + 40, axis_left, axis_y), fill=INK, width=3)
    dashed_line(draw, (map_x(1.0), top + 40, map_x(1.0), axis_y), fill=GREY, width=3)

    for tick in ticks:
        tx = map_x(tick)
        draw.line((tx, axis_y, tx, axis_y + 13), fill=INK, width=3)
        draw.text((tx, axis_y + 48), f"{tick:g}", font=F_TICK, fill=INK, anchor="mm")
        if tick != 1.0:
            draw.line((tx, top + 40, tx, axis_y), fill=GRID, width=2)

    draw.text(((axis_left + axis_right) / 2, bottom + 35), "Hazard ratio (log scale)", font=F_AXIS, fill=INK, anchor="mm")
    draw.text((map_x(lower_risk_x), top + 22), "Lower risk", font=F_SMALL, fill=BLUE, anchor="ma")
    draw.text((map_x(1.0) + 14, top + 22), "Higher risk", font=F_SMALL, fill=RED, anchor="la")

    for _, row in df.iterrows():
        model = row["model"]
        y = y_positions[model]
        draw.text((left + 285, y), labels[model], font=F_TEXT, fill=INK, anchor="rm")
        draw_errorbar(
            draw,
            map_x(row["HR"]),
            map_x(row["CI_low"]),
            map_x(row["CI_high"]),
            y,
            color=color,
            marker=marker,
        )
        p_value = row["p_display"] if row["exposure_form"] == "Continuous per 10 g/day" else row["p_trend_display"]
        label = f'{row["HR_95CI"]}; P={p_value}'.replace("P=<", "P<")
        draw.text((right - 230, y), label, font=F_SMALL, fill=INK, anchor="lm")


def main() -> None:
    plot_df = pd.read_excel(SOURCE_XLSX, sheet_name="Plot data", engine="openpyxl")

    image = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((120, 72), "Sensitivity to survey year and province fixed effects", font=F_TITLE, fill=INK, anchor="la")
    draw.text(
        (120, 128),
        "Cox models for cumulative average rice amylose intake and incident type 2 diabetes; robust standard errors clustered by participant ID.",
        font=F_SUBTITLE,
        fill=GREY,
        anchor="la",
    )

    q4 = plot_df[plot_df["contrast"] == "Q4 vs Q1"]
    continuous = plot_df[plot_df["contrast"] == "Per 10 g/day"]
    draw_panel(
        draw,
        "a",
        "Highest versus lowest quartile",
        q4,
        frame=(100, 270, 1180, 1060),
        xmin=0.35,
        xmax=1.15,
        ticks=[0.4, 0.6, 0.8, 1.0],
        color=BLUE,
        marker="square",
        lower_risk_x=0.6,
    )
    draw_panel(
        draw,
        "b",
        "Continuous exposure",
        continuous,
        frame=(1240, 270, 2320, 1060),
        xmin=0.82,
        xmax=1.04,
        ticks=[0.84, 0.88, 0.92, 0.96, 1.0],
        color=TEAL,
        marker="circle",
        lower_risk_x=0.92,
    )

    note = (
        "FE, fixed effects. Year and province fixed effects refer to baseline survey year and baseline province. "
        "Main Model 3 adjusted for age group, sex, education, household income, urban/rural residence, BMI category, "
        "physical activity, smoking, alcohol drinking and total energy intake."
    )
    draw_wrapped(draw, 120, 1218, note, F_SMALL, GREY, width=168, gap=5)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png = OUT_BASE.with_suffix(".png")
    tiff = OUT_BASE.with_suffix(".tiff")
    pdf = OUT_BASE.with_suffix(".pdf")
    image.save(png, dpi=(DPI, DPI))
    image.save(tiff, dpi=(DPI, DPI), compression="tiff_lzw")
    image.save(pdf, "PDF", resolution=DPI)
    print(SOURCE_XLSX)
    print(png)
    print(tiff)
    print(pdf)


if __name__ == "__main__":
    main()
