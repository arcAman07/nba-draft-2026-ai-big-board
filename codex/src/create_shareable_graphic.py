from __future__ import annotations

import math
import textwrap
from pathlib import Path
from typing import Iterable, Tuple

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from common import BASE_DIR, FIGURES_DIR


OUT_LANDSCAPE = FIGURES_DIR / "shareable_mock_draft_16x9.png"
OUT_STORY_1 = FIGURES_DIR / "shareable_mock_draft_story_picks_01_10.png"
OUT_STORY_2 = FIGURES_DIR / "shareable_mock_draft_story_picks_11_20.png"
OUT_STORY_3 = FIGURES_DIR / "shareable_mock_draft_story_picks_21_30.png"
OUT_STORY_DECK = FIGURES_DIR / "shareable_mock_draft_story_deck.pdf"

FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

BG = "#f7f8fb"
INK = "#17202a"
MUTED = "#5f6b7a"
CARD = "#ffffff"
LINE = "#d8dee8"
TITLE = "#16283d"
GOLD = "#c79a35"

POSITION_COLORS = {
    "guard": "#2f6fdb",
    "wing": "#23966f",
    "forward": "#b36a2e",
    "big": "#b84a5b",
    "hybrid": "#6b5fb5",
}

TEAM_ABBR = {
    "Washington": "WAS",
    "Utah": "UTA",
    "Memphis": "MEM",
    "Chicago": "CHI",
    "LA Clippers": "LAC",
    "Brooklyn": "BKN",
    "Sacramento": "SAC",
    "Atlanta": "ATL",
    "Dallas": "DAL",
    "Milwaukee": "MIL",
    "Golden State": "GSW",
    "Oklahoma City": "OKC",
    "Miami": "MIA",
    "Charlotte": "CHA",
    "Toronto": "TOR",
    "San Antonio": "SAS",
    "Detroit": "DET",
    "Philadelphia": "PHI",
    "New York": "NYK",
    "Los Angeles Lakers": "LAL",
    "Denver": "DEN",
    "Boston": "BOS",
    "Minnesota": "MIN",
    "Cleveland": "CLE",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, min_size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    size = start
    while size > min_size:
        fnt = font(size, bold)
        if text_size(draw, text, fnt)[0] <= max_width:
            return fnt
        size -= 1
    return font(min_size, bold)


def rounded_rect(draw: ImageDraw.ImageDraw, xy: Tuple[int, int, int, int], radius: int, fill: str, outline: str | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def pill(draw: ImageDraw.ImageDraw, xy: Tuple[int, int, int, int], fill: str, text: str, text_fill: str, fnt: ImageFont.FreeTypeFont) -> None:
    rounded_rect(draw, xy, 18, fill)
    tw, th = text_size(draw, text, fnt)
    x1, y1, x2, y2 = xy
    draw.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2 - 1), text, fill=text_fill, font=fnt)


def position_bucket(pos: str) -> str:
    p = str(pos).upper()
    if "/" in p:
        return "hybrid"
    if "PG" in p or "SG" in p:
        return "guard"
    if "SF" in p:
        return "wing"
    if "PF" in p:
        return "forward"
    if p == "C" or "C" in p:
        return "big"
    return "hybrid"


def load() -> pd.DataFrame:
    mock = pd.read_csv(BASE_DIR / "data/processed/fit_adjusted_mock_2026.csv")
    scores = pd.read_csv(BASE_DIR / "data/processed/prospect_model_scores_2026.csv")
    scores = scores[["display_name", "pred_value_p50", "pred_value_p10", "pred_value_p90", "consensus_mean", "tier"]]
    out = mock.merge(scores, left_on="selection", right_on="display_name", how="left")
    out["team_abbr"] = out["owner"].map(TEAM_ABBR).fillna(out["owner"].str[:3].str.upper())
    return out


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int, max_lines: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    cur = ""
    for word in words:
        candidate = f"{cur} {word}".strip()
        if text_size(draw, candidate, fnt)[0] <= max_width:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = word
        if len(lines) == max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if len(lines) == max_lines and words:
        joined = " ".join(lines)
        if len(joined) < len(str(text)):
            lines[-1] = lines[-1].rstrip(".,") + "..."
    return lines


def draw_card(
    draw: ImageDraw.ImageDraw,
    row: pd.Series,
    xy: Tuple[int, int, int, int],
    compact: bool = False,
) -> None:
    x1, y1, x2, y2 = xy
    w, h = x2 - x1, y2 - y1
    bucket = position_bucket(row["position"])
    color = POSITION_COLORS[bucket]

    # Card shadow and shell.
    rounded_rect(draw, (x1 + 4, y1 + 5, x2 + 4, y2 + 5), 8, "#dfe4ec")
    rounded_rect(draw, xy, 8, CARD, LINE, 2)
    draw.rectangle((x1, y1, x1 + 8, y2), fill=color)

    pad = 18 if not compact else 13
    pick_f = font(24 if not compact else 20, True)
    team_f = font(17 if not compact else 14, True)
    small_f = font(15 if not compact else 12)
    micro_f = font(13 if not compact else 10)

    # Pick badge.
    badge_w = 58 if not compact else 48
    badge_h = 36 if not compact else 30
    pill(draw, (x1 + pad, y1 + pad, x1 + pad + badge_w, y1 + pad + badge_h), color, f"#{int(row['pick'])}", "#ffffff", pick_f)
    draw.text((x1 + pad + badge_w + 10, y1 + pad + 1), row["team_abbr"], fill=TITLE, font=team_f)
    owner = str(row["owner"])
    owner_f = fit_font(draw, owner, w - pad * 2 - badge_w - 12, 14 if not compact else 11, 9)
    draw.text((x1 + pad + badge_w + 10, y1 + pad + (21 if not compact else 17)), owner, fill=MUTED, font=owner_f)

    # Player name.
    name_top = y1 + pad + badge_h + (17 if not compact else 11)
    name = str(row["selection"])
    name_f = fit_font(draw, name, w - 2 * pad, 29 if not compact else 21, 16 if not compact else 13, True)
    draw.text((x1 + pad, name_top), name, fill=INK, font=name_f)

    # Meta row.
    meta_y = name_top + text_size(draw, name, name_f)[1] + (13 if not compact else 8)
    pos_text = f"{row['position']}  |  Board {int(row['board_rank'])}"
    draw.text((x1 + pad, meta_y), pos_text, fill=color, font=small_f)
    model = f"Model p50 {float(row['pred_value_p50']):.1f}"
    draw.text((x2 - pad - text_size(draw, model, small_f)[0], meta_y), model, fill=TITLE, font=small_f)

    # Need snippet.
    need_y = meta_y + (27 if not compact else 21)
    draw.line((x1 + pad, need_y - 8, x2 - pad, need_y - 8), fill="#eef1f5", width=2)
    need_f = font(14 if not compact else 11)
    need_lines = wrap(draw, str(row["team_need"]), need_f, w - 2 * pad, 2 if not compact else 2)
    draw.text((x1 + pad, need_y), "Need: " + (need_lines[0] if need_lines else ""), fill=MUTED, font=need_f)
    if len(need_lines) > 1:
        draw.text((x1 + pad, need_y + (18 if not compact else 14)), need_lines[1], fill=MUTED, font=need_f)

    if h > 190:
        detail_y = need_y + 48
        draw.text((x1 + pad, detail_y), "Decision factors", fill=TITLE, font=font(14, True))
        detail_y += 28
        factor_f = font(13)
        rows = [
            f"Consensus rank: {float(row['consensus_mean']):.1f}",
            f"Model band: {float(row['pred_value_p10']):.1f}-{float(row['pred_value_p90']):.1f} MPG-eq",
            f"Pure board rank: {int(row['board_rank'])}",
        ]
        for item in rows:
            draw.text((x1 + pad, detail_y), item, fill=INK, font=factor_f)
            detail_y += 22
        detail_y += 8
        draw.text((x1 + pad, detail_y), "Fit note", fill=TITLE, font=font(14, True))
        detail_y += 26
        for line in wrap(draw, str(row["team_need"]), factor_f, w - 2 * pad, 4):
            draw.text((x1 + pad, detail_y), line, fill=MUTED, font=factor_f)
            detail_y += 20


def draw_legend(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    f = font(22, True)
    draw.text((x, y), "Position color", fill=MUTED, font=font(18, True))
    cur_x = x
    y += 30
    for label in ["guard", "wing", "forward", "big", "hybrid"]:
        color = POSITION_COLORS[label]
        pill(draw, (cur_x, y, cur_x + 122, y + 34), color, label.upper(), "#ffffff", font(14, True))
        cur_x += 136


def render(
    df: pd.DataFrame,
    path: Path,
    size: Tuple[int, int],
    cols: int,
    rows: int,
    compact: bool = False,
    start: int = 0,
    range_label: str = "Full first round",
) -> None:
    W, H = size
    img = Image.new("RGB", size, BG)
    draw = ImageDraw.Draw(img)

    margin_x = 70 if not compact else 46
    margin_top = 54 if not compact else 48
    header_h = 175 if not compact else 245
    footer_h = 52 if not compact else 66
    gap = 22 if not compact else 15

    draw.text((margin_x, margin_top), "2026 NBA Draft Mock", fill=TITLE, font=font(58 if not compact else 46, True))
    draw.text(
        (margin_x, margin_top + (68 if not compact else 56)),
        "Fit-adjusted first round from the Codex research board",
        fill=MUTED,
        font=font(25 if not compact else 22),
    )
    draw.text(
        (margin_x, margin_top + (105 if not compact else 91)),
        "Talent-first board + model score + consensus + team needs | As of 2026-06-10",
        fill=INK,
        font=font(21 if not compact else 18, True),
    )
    draw.text(
        (margin_x, margin_top + (134 if not compact else 120)),
        range_label,
        fill=GOLD,
        font=font(19 if not compact else 17, True),
    )

    if not compact:
        draw_legend(draw, W - 760, margin_top + 24)
    else:
        draw_legend(draw, margin_x, margin_top + 158)

    grid_top = margin_top + header_h
    grid_bottom = H - footer_h - 26
    card_w = (W - 2 * margin_x - (cols - 1) * gap) // cols
    card_h = (grid_bottom - grid_top - (rows - 1) * gap) // rows

    page = df.iloc[start : start + cols * rows]
    for i, (_, row) in enumerate(page.iterrows()):
        r = i // cols
        c = i % cols
        x1 = margin_x + c * (card_w + gap)
        y1 = grid_top + r * (card_h + gap)
        draw_card(draw, row, (x1, y1, x1 + card_w, y1 + card_h), compact=compact)

    footer = "Source: nba_draft_codex/report/final_report.pdf  |  Model value = NBA MPG-equivalent median, not a guarantee"
    draw.text((margin_x, H - footer_h + 6), footer, fill=MUTED, font=font(18 if not compact else 16))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=95)


def main() -> None:
    df = load()
    render(df, OUT_LANDSCAPE, (2400, 1350), cols=5, rows=6, compact=False, range_label="Full first round: picks 1-30")
    render(df, OUT_STORY_1, (1080, 1920), cols=2, rows=5, compact=True, start=0, range_label="Story slide 1 of 3: picks 1-10")
    render(df, OUT_STORY_2, (1080, 1920), cols=2, rows=5, compact=True, start=10, range_label="Story slide 2 of 3: picks 11-20")
    render(df, OUT_STORY_3, (1080, 1920), cols=2, rows=5, compact=True, start=20, range_label="Story slide 3 of 3: picks 21-30")
    story_images = [Image.open(path).convert("RGB") for path in [OUT_STORY_1, OUT_STORY_2, OUT_STORY_3]]
    story_images[0].save(OUT_STORY_DECK, save_all=True, append_images=story_images[1:])
    print(f"wrote {OUT_LANDSCAPE}")
    print(f"wrote {OUT_STORY_1}")
    print(f"wrote {OUT_STORY_2}")
    print(f"wrote {OUT_STORY_3}")
    print(f"wrote {OUT_STORY_DECK}")


if __name__ == "__main__":
    main()
