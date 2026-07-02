from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


sys.dont_write_bytecode = True

PACKAGE_DIR = Path(__file__).resolve().parents[1]
SOURCE_XLSX = PACKAGE_DIR / "data" / "Supplementary_Fig_3_source_data.xlsx"
OUT_BASE = PACKAGE_DIR / "output" / "Supplementary_Fig_3_reproduced_from_source_data"

W, H = 1774, 887
DPI = 300

INK = (20, 20, 20)
GRID = (205, 210, 216)
BLUE_EDGE = (64, 137, 214)
BLUE_FILL = (222, 235, 247)
RED = (255, 0, 0)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


F_TAG = font(38, True)
F_AXIS = font(27, True)
F_TICK = font(25)
F_TEXT = font(23)
F_SMALL = font(21)


def dashed_line(draw: ImageDraw.ImageDraw, xy, fill=GRID, width: int = 1, dash: int = 8, gap: int = 8) -> None:
    x0, y0, x1, y1 = xy
    if abs(x1 - x0) >= abs(y1 - y0):
        x = x0
        step = dash + gap
        while x < x1:
            draw.line((x, y0, min(x + dash, x1), y1), fill=fill, width=width)
            x += step
    else:
        y = y0
        step = dash + gap
        while y < y1:
            draw.line((x0, y, x1, min(y + dash, y1)), fill=fill, width=width)
            y += step


def rotated_text(base: Image.Image, xy, text: str, fnt, angle: int = 90) -> None:
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bbox = probe.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0] + 24, bbox[3] - bbox[1] + 24
    patch = Image.new("RGBA", (tw, th), (255, 255, 255, 0))
    d = ImageDraw.Draw(patch)
    d.text((tw / 2, th / 2), text, font=fnt, fill=INK + (255,), anchor="mm")
    rot = patch.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    base.paste(rot, (int(xy[0] - rot.width / 2), int(xy[1] - rot.height / 2)), rot)


def heat_color(z: float) -> tuple[int, int, int]:
    z = max(-2.0, min(2.0, float(z)))
    if z < 0:
        t = (z + 2.0) / 2.0
        a, b = np.array((5, 97, 158)), np.array((248, 248, 248))
    else:
        t = z / 2.0
        a, b = np.array((248, 248, 248)), np.array((226, 55, 55))
    color = np.round(a * (1 - t) + b * t).astype(int)
    return int(color[0]), int(color[1]), int(color[2])


def readable_on(fill: tuple[int, int, int]) -> tuple[int, int, int]:
    lum = 0.2126 * fill[0] + 0.7152 * fill[1] + 0.0722 * fill[2]
    return (255, 255, 255) if lum < 125 else (0, 0, 0)


def draw_panel_a(draw: ImageDraw.ImageDraw, image: Image.Image, hist: pd.DataFrame, meta: dict[str, object]) -> None:
    draw.text((18, 20), "a", font=F_TAG, fill=INK, anchor="la")
    frame = (110, 92, 850, 737)
    x0, y0, x1, y1 = frame
    x_max = 160.0
    y_max = 2750.0

    draw.line((x0, y1, x1, y1), fill=INK, width=2)
    draw.line((x0, y0, x0, y1), fill=INK, width=2)

    for yv in [0, 1375, 2750]:
        yy = y1 - yv / y_max * (y1 - y0)
        draw.line((x0 - 10, yy, x0, yy), fill=INK, width=2)
        draw.text((x0 - 17, yy), f"{int(yv)}", font=F_TICK, fill=INK, anchor="rm")
        dashed_line(draw, (x0, yy, x1, yy), fill=(190, 194, 199), width=1, dash=7, gap=7)
    for xv in [0, 40, 80, 120, 160]:
        xx = x0 + xv / x_max * (x1 - x0)
        draw.line((xx, y1, xx, y1 + 11), fill=INK, width=2)
        draw.text((xx, y1 + 35), f"{xv}", font=F_TICK, fill=INK, anchor="mm")
        if xv > 0:
            dashed_line(draw, (xx, y0, xx, y1), fill=(190, 194, 199), width=1, dash=7, gap=7)

    for row in hist.itertuples(index=False):
        left = float(row.bin_start_g_day)
        right = float(row.bin_end_g_day)
        count = float(row.participants)
        xx0 = x0 + left / x_max * (x1 - x0)
        xx1 = x0 + right / x_max * (x1 - x0)
        yy = y1 - count / y_max * (y1 - y0)
        draw.rectangle((xx0 + 2, yy, xx1 - 2, y1), fill=BLUE_FILL, outline=BLUE_EDGE, width=1)

    median = float(meta["panel_a_display_median_g_day"])
    q1 = float(meta["panel_a_display_iqr_low_g_day"])
    q3 = float(meta["panel_a_display_iqr_high_g_day"])
    mx = x0 + median / x_max * (x1 - x0)
    draw.line((mx, y0, mx, y1), fill=RED, width=3)
    draw.text((mx + 14, y0 + 44), f"Median {median:.1f} g/day", font=F_SMALL, fill=RED, anchor="la")
    draw.text((x1 - 18, y0 + 44), f"IQR {q1:.1f}-{q3:.1f}", font=F_SMALL, fill=INK, anchor="ra")

    draw.text(((x0 + x1) / 2, y1 + 85), "Baseline rice amylose intake (g/day)", font=F_AXIS, fill=INK, anchor="mm")
    rotated_text(image, (24, (y0 + y1) / 2), "Participants", F_AXIS, 90)


def draw_panel_b(draw: ImageDraw.ImageDraw, heat: pd.DataFrame) -> None:
    draw.text((925, 20), "b", font=F_TAG, fill=INK, anchor="la")
    left, top = 1150, 102
    cell_w, cell_h = 125, 56
    q_cols = ["Q1", "Q2", "Q3", "Q4"]
    z_cols = ["Q1_row_z", "Q2_row_z", "Q3_row_z", "Q4_row_z"]
    rows = heat["variable"].tolist()

    for j, q in enumerate(q_cols):
        draw.text((left + j * cell_w + cell_w / 2, top - 24), q, font=F_TEXT, fill=INK, anchor="mm")

    for i, row in heat.iterrows():
        cy = top + i * cell_h + cell_h / 2
        draw.text((left - 18, cy), row["variable"], font=F_TEXT, fill=INK, anchor="rm")
        for j, (q, zc) in enumerate(zip(q_cols, z_cols)):
            x0, y0 = left + j * cell_w, top + i * cell_h
            fill = heat_color(row[zc])
            draw.rectangle((x0, y0, x0 + cell_w, y0 + cell_h), fill=fill, outline=(255, 255, 255), width=2)
            val = float(row[q])
            label = f"{val:.0f}" if row["variable"] in {"Rice intake (g/day)", "Energy (kcal/day)"} else f"{val:.1f}"
            draw.text((x0 + cell_w / 2, y0 + cell_h / 2), label, font=F_TEXT, fill=readable_on(fill), anchor="mm")
    draw.rectangle((left, top, left + len(q_cols) * cell_w, top + len(rows) * cell_h), outline=INK, width=1)
    draw.text((left + len(q_cols) * cell_w / 2, top + len(rows) * cell_h + 54), "Quartile of baseline rice amylose intake", font=F_AXIS, fill=INK, anchor="mm")

    lx, ly = left + len(q_cols) * cell_w + 48, top + 28
    draw.text((lx + 18, ly - 34), "Row z", font=F_SMALL, fill=INK, anchor="mm")
    grad_h = 330
    for k in range(grad_h):
        z = 2 - 4 * k / (grad_h - 1)
        draw.rectangle((lx, ly + k, lx + 24, ly + k + 1), fill=heat_color(z))
    draw.rectangle((lx, ly, lx + 24, ly + grad_h), outline=INK, width=1)
    for z, label in [(2, "2"), (0, "0"), (-2, "-2")]:
        yy = ly + (2 - z) / 4 * grad_h
        draw.line((lx - 5, yy, lx, yy), fill=INK, width=1)
        draw.text((lx - 11, yy), label, font=F_SMALL, fill=INK, anchor="rm")
    draw.text((lx + 36, ly), "High", font=F_SMALL, fill=INK, anchor="la")
    draw.text((lx + 36, ly + grad_h), "Low", font=F_SMALL, fill=INK, anchor="la")


def save_outputs(image: Image.Image, out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    png = out_base.with_suffix(".png")
    tiff = out_base.with_suffix(".tiff")
    pdf = out_base.with_suffix(".pdf")
    image.save(png)
    image.save(tiff, compression="tiff_lzw", dpi=(DPI, DPI))
    page_w = image.width / DPI * 72
    page_h = image.height / DPI * 72
    c = canvas.Canvas(str(pdf), pagesize=(page_w, page_h))
    c.drawImage(ImageReader(image), 0, 0, width=page_w, height=page_h)
    c.showPage()
    c.save()
    print(png)
    print(tiff)
    print(pdf)


def main() -> None:
    sheets = pd.read_excel(SOURCE_XLSX, sheet_name=None, engine="openpyxl")
    hist = sheets["Supplementary_Fig_3a"]
    heat = sheets["Supplementary_Fig_3b"]
    meta = dict(zip(sheets["Metadata"]["field"], sheets["Metadata"]["value"]))
    image = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(image, "RGBA")
    draw_panel_a(draw, image, hist, meta)
    draw_panel_b(draw, heat)
    save_outputs(image, OUT_BASE)


if __name__ == "__main__":
    main()
