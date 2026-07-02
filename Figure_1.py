from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageChops, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


sys.dont_write_bytecode = True

PACKAGE_DIR = Path(__file__).resolve().parents[1]
SOURCE_XLSX = PACKAGE_DIR / "data" / "Figure_1_source_data.xlsx"
OUT_BASE = PACKAGE_DIR / "output" / "Figure_1_reproduced_from_source_data"

DPI = 300
A_W, A_H = 2048, 1050
PANEL_H = 1220
LABEL_W = 80
ROW_GAP = 45
COLUMN_GAP_ADD = 170
A_SPLIT_X = 1120
TOP_MARGIN = 30
BOTTOM_MARGIN = 60
CANVAS_W = A_W + LABEL_W + 90 + COLUMN_GAP_ADD
CANVAS_H = TOP_MARGIN + A_H + ROW_GAP + PANEL_H + BOTTOM_MARGIN

TIMES = "\u00d7"
DELTA = "\u0394"
MIDDOT = "\u00b7"
SUP_MINUS_ONE = "\u207b\u00b9"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


F_AXIS = font(54)
F_TICK = font(42)
F_NOTE = font(34)
F_EQ = font(36)
F_PERIOD = font(28)


class Panel:
    def __init__(self, x0: int, y0: int, w: int, h: int, xmin: float, xmax: float, ymin: float, ymax: float):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax

    def px(self, x):
        return self.x0 + (np.asarray(x) - self.xmin) / (self.xmax - self.xmin) * self.w

    def py(self, y):
        return self.y0 + self.h - (np.asarray(y) - self.ymin) / (self.ymax - self.ymin) * self.h


def text_center(draw: ImageDraw.ImageDraw, xy, text: str, font_obj, fill) -> None:
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    draw.text((xy[0] - (bbox[2] - bbox[0]) / 2, xy[1] - (bbox[3] - bbox[1]) / 2), text, font=font_obj, fill=fill)


def draw_rotated_text(base: Image.Image, *args) -> None:
    if isinstance(args[0], tuple):
        xy, text, fnt = args[0], args[1], args[2]
        angle = args[3] if len(args) > 3 else 90
        fill = (0, 0, 0, 255)
    else:
        text, xy, angle, fnt, fill = args
    bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tmp = Image.new("RGBA", (tw + 20, th + 20), (255, 255, 255, 0))
    dtmp = ImageDraw.Draw(tmp)
    dtmp.text((10, 10), text, font=fnt, fill=fill)
    rot = tmp.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    if base.mode == "RGBA":
        base.alpha_composite(rot, (int(xy[0] - rot.width / 2), int(xy[1] - rot.height / 2)))
    else:
        base.paste(rot, (int(xy[0] - rot.width / 2), int(xy[1] - rot.height / 2)), rot)


def trim_white(image: Image.Image, padding: int = 0) -> Image.Image:
    rgb = image.convert("RGB")
    bg = Image.new("RGB", rgb.size, "white")
    diff = ImageChops.difference(rgb, bg).convert("L").point(lambda p: 255 if p > 10 else 0)
    bbox = diff.getbbox()
    if bbox is None:
        return rgb
    x0, y0, x1, y1 = bbox
    return rgb.crop((max(0, x0 - padding), max(0, y0 - padding), min(rgb.width, x1 + padding), min(rgb.height, y1 + padding)))


def draw_frame(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], width: int = 5) -> None:
    draw.rectangle(box, outline=(0, 0, 0), width=width)


def draw_panel_axes_5yr(draw: ImageDraw.ImageDraw, panel: Panel, y_ticks, y_tick_labels) -> None:
    x0, y0, w, h = panel.x0, panel.y0, panel.w, panel.h
    draw.rectangle([x0, y0, x0 + w, y0 + h], outline=(0, 0, 0, 255), width=6)
    tick_len = 28
    for start in range(1980, 2025, 5):
        mid = start + 2
        x = panel.px(mid)
        draw.line([(x, y0 + h), (x, y0 + h - tick_len)], fill=(0, 0, 0, 255), width=5)
        text_center(draw, (x, y0 + h + 49), str(start), F_PERIOD, (0, 0, 0, 255))
    for yt, label in zip(y_ticks, y_tick_labels):
        y = panel.py(yt)
        draw.line([(x0, y), (x0 + tick_len, y)], fill=(0, 0, 0, 255), width=5)
        bbox = draw.textbbox((0, 0), label, font=F_TICK)
        draw.text((x0 - 30 - (bbox[2] - bbox[0]), y - (bbox[3] - bbox[1]) / 2), label, font=F_TICK, fill=(0, 0, 0, 255))
    text_center(draw, (x0 + w / 2, y0 + h + 105), "Year", F_AXIS, (0, 0, 0, 255))


def draw_ticks(draw, frame, x_ticks, y_ticks, x_scale, y_scale, f_tick, y_right_ticks=None, y_right_scale=None) -> None:
    x0, y0, x1, y1 = frame
    tick_len = 28
    for value, label in x_ticks:
        xx = x_scale(value)
        draw.line((xx, y1, xx, y1 - tick_len), fill=(0, 0, 0), width=5)
        draw.text((xx, y1 + 62), label, font=f_tick, fill=(0, 0, 0), anchor="mm")
    for value, label in y_ticks:
        yy = y_scale(value)
        draw.line((x0, yy, x0 + tick_len, yy), fill=(0, 0, 0), width=5)
        draw.text((x0 - 32, yy), label, font=f_tick, fill=(0, 0, 0), anchor="rm")
    if y_right_ticks and y_right_scale:
        for value, label in y_right_ticks:
            yy = y_right_scale(value)
            draw.line((x1, yy, x1 - tick_len, yy), fill=(0, 0, 0), width=5)
            draw.text((x1 + 34, yy), label, font=f_tick, fill=(0, 0, 0), anchor="lm")


def box_stats(values: np.ndarray) -> dict[str, float | np.ndarray] | None:
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return None
    q1, median, q3 = np.percentile(vals, [25, 50, 75])
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    inlier = vals[(vals >= lower_fence) & (vals <= upper_fence)]
    whisker_low = float(inlier.min()) if inlier.size else float(vals.min())
    whisker_high = float(inlier.max()) if inlier.size else float(vals.max())
    outliers = vals[(vals < whisker_low) | (vals > whisker_high)]
    return {
        "q1": float(q1),
        "median": float(median),
        "q3": float(q3),
        "whisker_low": whisker_low,
        "whisker_high": whisker_high,
        "outliers": outliers,
    }


def median_trend(period_data: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    med = (
        period_data.groupby(["period_start", "period_mid"], as_index=False)["value"]
        .median()
        .sort_values("period_mid")
    )
    slope, intercept = np.polyfit(med["period_mid"].to_numpy(float) - 1980, med["value"].to_numpy(float), 1)
    return med, float(slope), float(intercept)


def draw_median_trend(draw: ImageDraw.ImageDraw, panel: Panel, period_data: pd.DataFrame, color) -> tuple[float, float]:
    med, slope, intercept = median_trend(period_data)
    xvals = med["period_mid"].to_numpy(float)
    yvals = intercept + slope * (xvals - 1980)
    draw.line(list(zip(panel.px(xvals), panel.py(yvals))), fill=color, width=8)
    return slope, intercept


def annotate_median_trend(draw: ImageDraw.ImageDraw, panel: Panel, slope: float, intercept: float, metric: str) -> None:
    x0, y0 = panel.x0, panel.y0
    if metric == "yield":
        eq = f"Median trend: y = {intercept:.1f} {'+' if slope >= 0 else '-'} {abs(slope):.1f} {TIMES} (x - 1980)"
        delta_text = f"{DELTA}Median yield = {slope * 10:+.1f} kg ha{SUP_MINUS_ONE} / 10 yr"
    else:
        eq = f"Median trend: y = {intercept:.1f} {'+' if slope >= 0 else '-'} {abs(slope):.4g} {TIMES} (x - 1980)"
        delta_text = f"{DELTA}Median amylose = {slope * 10:+.2f}% / 10 yr"
    draw.text((x0 + 70, y0 + 28), eq, font=F_EQ, fill=(0, 0, 0, 255))
    draw.text((x0 + 70, y0 + 72), delta_text, font=F_NOTE, fill=(0, 0, 0, 255))


def draw_boxplots_variant(base: Image.Image, panel: Panel, data: pd.DataFrame, fill, edge) -> None:
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    box_width = 44
    cap_width = 28
    for start, group in data.groupby("period_start", sort=True):
        stats = box_stats(group["value"].to_numpy(float))
        if not stats:
            continue
        x = float(panel.px(float(start) + 2))
        y_q1 = float(panel.py(stats["q1"]))
        y_med = float(panel.py(stats["median"]))
        y_q3 = float(panel.py(stats["q3"]))
        y_low = float(panel.py(stats["whisker_low"]))
        y_high = float(panel.py(stats["whisker_high"]))
        draw.line([(x, y_high), (x, y_low)], fill=edge, width=4)
        draw.line([(x - cap_width / 2, y_high), (x + cap_width / 2, y_high)], fill=edge, width=4)
        draw.line([(x - cap_width / 2, y_low), (x + cap_width / 2, y_low)], fill=edge, width=4)
        draw.rectangle([x - box_width / 2, y_q3, x + box_width / 2, y_q1], fill=fill, outline=edge, width=4)
        draw.line([(x - box_width / 2, y_med), (x + box_width / 2, y_med)], fill=edge, width=5)
        faint_fill = (fill[0], fill[1], fill[2], 25)
        faint_edge = (edge[0], edge[1], edge[2], 45)
        for value in stats["outliers"]:
            y = float(panel.py(value))
            draw.ellipse([x - 4, y - 4, x + 4, y + 4], outline=faint_edge, fill=faint_fill, width=2)
    base.alpha_composite(overlay)


def draw_panel_a(sheet_a: pd.DataFrame, sheet_b: pd.DataFrame) -> Image.Image:
    image = Image.new("RGBA", (2048, 1050), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    left = Panel(250, 80, 780, 760, 1977.5, 2026.5, -1500, 22200)
    right = Panel(1210, 80, 780, 760, 1977.5, 2026.5, -2, 40.5)
    draw_panel_axes_5yr(draw, left, [0, 5000, 10000, 15000, 20000], ["0", "5,000", "10,000", "15,000", "20,000"])
    draw_panel_axes_5yr(draw, right, [0, 10, 20, 30, 40], ["0", "10", "20", "30", "40"])
    draw_rotated_text(image, f"Yield (kg{MIDDOT}ha{SUP_MINUS_ONE})", (55, 460), 90, F_AXIS, (0, 0, 0, 255))
    draw_rotated_text(image, "Amylose (%)", (1070, 460), 90, F_AXIS, (0, 0, 0, 255))

    red_fill = (226, 21, 21, 90)
    red_edge = (165, 0, 0, 230)
    blue_fill = (24, 101, 162, 90)
    blue_edge = (0, 70, 122, 230)
    red = (205, 15, 20, 190)
    blue = (0, 82, 145, 190)

    draw = ImageDraw.Draw(image)
    yield_slope, yield_intercept = draw_median_trend(draw, left, sheet_a, red)
    amylose_slope, amylose_intercept = draw_median_trend(draw, right, sheet_b, blue)
    draw_boxplots_variant(image, left, sheet_a, red_fill, red_edge)
    draw_boxplots_variant(image, right, sheet_b, blue_fill, blue_edge)
    draw = ImageDraw.Draw(image)
    annotate_median_trend(draw, left, yield_slope, yield_intercept, "yield")
    annotate_median_trend(draw, right, amylose_slope, amylose_intercept, "amylose")
    return image.convert("RGB")


def draw_bottom_row(sheet_c: pd.DataFrame, sheet_d: pd.DataFrame) -> Image.Image:
    row = Image.new("RGB", (CANVAS_W, PANEL_H), "white")
    draw = ImageDraw.Draw(row, "RGBA")
    f_tick = font(44)
    f_axis = font(64)
    f_axis_small = font(56)
    f_legend = font(34)
    f_value = font(44)
    b_frame = (300, 110, 1118, 1000)
    c_frame = (1308 + COLUMN_GAP_ADD, 110, 2127 + COLUMN_GAP_ADD, 1000)

    years = sheet_c["survey_year"].astype(float).tolist()
    rice = sheet_c["amylose_median_g_day"].astype(float).tolist()
    energy = sheet_c["energy_pct_median"].astype(float).tolist()
    x_min, x_max = 1996.5, 2011.5
    y_min, y_max = 0.0, 65.0
    r_min, r_max = 0.0, 13.0

    def bx(v: float) -> float:
        return b_frame[0] + (v - x_min) / (x_max - x_min) * (b_frame[2] - b_frame[0])

    def by(v: float) -> float:
        return b_frame[3] - (v - y_min) / (y_max - y_min) * (b_frame[3] - b_frame[1])

    def by_r(v: float) -> float:
        return b_frame[3] - (v - r_min) / (r_max - r_min) * (b_frame[3] - b_frame[1])

    draw_frame(draw, b_frame)
    draw_ticks(
        draw,
        b_frame,
        [(1997, "1997"), (2000, "2000"), (2004, "2004"), (2006, "2006"), (2009, "2009"), (2011, "2011")],
        [(0, "0"), (20, "20"), (40, "40"), (60, "60")],
        bx,
        by,
        f_tick,
        y_right_ticks=[(0, "0"), (4, "4"), (8, "8"), (12, "12")],
        y_right_scale=by_r,
    )

    red = (205, 22, 28)
    blue = (32, 93, 190)
    rice_pts = [(bx(x), by(y)) for x, y in zip(years, rice)]
    energy_pts = [(bx(x), by_r(y)) for x, y in zip(years, energy)]
    draw.line(rice_pts, fill=red, width=4)
    draw.line(energy_pts, fill=blue, width=4)
    for xx, yy in rice_pts:
        draw.ellipse((xx - 15, yy - 15, xx + 15, yy + 15), fill=(255, 255, 255), outline=red, width=5)
    for xx, yy in energy_pts:
        draw.polygon([(xx, yy - 19), (xx - 18, yy + 16), (xx + 18, yy + 16)], fill=(255, 255, 255), outline=blue)
        draw.line([(xx, yy - 19), (xx - 18, yy + 16), (xx + 18, yy + 16), (xx, yy - 19)], fill=blue, width=5)

    for i, (x, yv) in enumerate(zip(years, rice)):
        x_offset = 58 if i == 0 else (-58 if i == len(years) - 1 else 0)
        draw.text((bx(x) + x_offset, by(yv) + 42), f"{yv:.1f}", font=f_value, fill=red, anchor="mm")
    for i, (x, yv) in enumerate(zip(years, energy)):
        x_offset = 58 if i == 0 else (-58 if i == len(years) - 1 else 0)
        draw.text((bx(x) + x_offset, by_r(yv) - 34), f"{yv:.1f}", font=f_value, fill=blue, anchor="mm")

    lx, ly = 410, 155
    draw.line((lx, ly, lx + 52, ly), fill=red, width=4)
    draw.ellipse((lx + 18, ly - 12, lx + 42, ly + 12), fill=(255, 255, 255), outline=red, width=4)
    draw.text((lx + 86, ly), "Rice amylose intake", font=f_legend, fill=(0, 0, 0), anchor="lm")
    ly2 = ly + 56
    draw.line((lx, ly2, lx + 58, ly2), fill=blue, width=4)
    draw.polygon([(lx + 29, ly2 - 17), (lx + 12, ly2 + 15), (lx + 46, ly2 + 15)], fill=(255, 255, 255), outline=blue)
    draw.line([(lx + 29, ly2 - 17), (lx + 12, ly2 + 15), (lx + 46, ly2 + 15), (lx + 29, ly2 - 17)], fill=blue, width=4)
    draw.text((lx + 84, ly2), "Energy contribution", font=f_legend, fill=(0, 0, 0), anchor="lm")
    draw.text(((b_frame[0] + b_frame[2]) / 2, 1136), "Year", font=f_axis, fill=(0, 0, 0), anchor="mm")
    draw_rotated_text(row, (190, (b_frame[1] + b_frame[3]) // 2), "Rice amylose intake (g/day)", f_axis, 90)
    draw_rotated_text(row, (1218, (b_frame[1] + b_frame[3]) // 2), "Energy contribution (%)", f_axis, -90)

    c_data = sheet_d.sort_values("year").to_dict("records")

    def cx(i: int) -> float:
        return c_frame[0] + (i + 0.5) / len(c_data) * (c_frame[2] - c_frame[0])

    def cy(v: float) -> float:
        return c_frame[3] - v / 10.0 * (c_frame[3] - c_frame[1])

    draw_frame(draw, c_frame)
    draw_ticks(
        draw,
        c_frame,
        [(i, str(int(d["year"]))) for i, d in enumerate(c_data)],
        [(0, "0"), (2, "2"), (4, "4"), (6, "6"), (8, "8"), (10, "10")],
        cx,
        cy,
        f_tick,
    )
    bar_color = (13, 81, 133)
    step = (c_frame[2] - c_frame[0]) / len(c_data)
    bar_w = step * 0.58
    pts = []
    for i, item in enumerate(c_data):
        xx = cx(i)
        yy = cy(float(item["prevalence_percent"]))
        pts.append((xx, yy))
        draw.rectangle((xx - bar_w / 2, yy, xx + bar_w / 2, c_frame[3]), fill=bar_color)
    draw.line(pts, fill=(215, 55, 39), width=5)
    for xx, yy in pts:
        draw.ellipse((xx - 13, yy - 13, xx + 13, yy + 13), fill=(255, 255, 255), outline=(215, 55, 39), width=5)
    for (xx, yy), item in zip(pts, c_data):
        draw.text((xx, yy - 40), f'{float(item["prevalence_percent"]):.1f}', font=f_value, fill=(215, 55, 39), anchor="mm")
    draw.text(((c_frame[0] + c_frame[2]) / 2, 1136), "Year", font=f_axis, fill=(0, 0, 0), anchor="mm")
    draw_rotated_text(row, (1148 + COLUMN_GAP_ADD, (c_frame[1] + c_frame[3]) // 2), "Prevalence of type 2 diabetes (%)", f_axis_small, 90)
    return row


def main() -> None:
    sheets = pd.read_excel(SOURCE_XLSX, sheet_name=None, engine="openpyxl")
    panel_a = draw_panel_a(sheets["Figure_1.a"], sheets["Figure_1.b"])
    panel_a = trim_white(panel_a, padding=0).resize((A_W, A_H), Image.Resampling.LANCZOS)
    a_left = panel_a.crop((0, 0, A_SPLIT_X, A_H))
    a_right = panel_a.crop((A_SPLIT_X, 0, A_W, A_H))
    bottom_row = draw_bottom_row(sheets["Figure_1.c"], sheets["Figure_1.d"])

    out = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")
    draw = ImageDraw.Draw(out)
    out.paste(a_left, (LABEL_W, TOP_MARGIN))
    out.paste(a_right, (LABEL_W + A_SPLIT_X + COLUMN_GAP_ADD, TOP_MARGIN))
    out.paste(bottom_row, (0, TOP_MARGIN + A_H + ROW_GAP))
    draw.rectangle((1122, TOP_MARGIN + 110, 1378, TOP_MARGIN + 880), fill=(255, 255, 255))
    draw_rotated_text(out, (LABEL_W + 1070 + COLUMN_GAP_ADD, TOP_MARGIN + 460), "Amylose (%)", font(54), 90)

    OUT_BASE.parent.mkdir(parents=True, exist_ok=True)
    png = OUT_BASE.with_suffix(".png")
    tiff = OUT_BASE.with_suffix(".tiff")
    pdf = OUT_BASE.with_suffix(".pdf")
    out.save(png, dpi=(DPI, DPI))
    out.save(tiff, compression="tiff_lzw", dpi=(DPI, DPI))
    page_w = CANVAS_W / DPI * 72
    page_h = CANVAS_H / DPI * 72
    c = canvas.Canvas(str(pdf), pagesize=(page_w, page_h))
    c.drawImage(ImageReader(out), 0, 0, width=page_w, height=page_h)
    c.showPage()
    c.save()
    print(png)
    print(tiff)
    print(pdf)


if __name__ == "__main__":
    main()
