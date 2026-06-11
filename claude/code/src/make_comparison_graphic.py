"""Render the Fable vs Codex board-comparison slope chart
(release/images/tweet2_board_comparison.png). Left column is the Fable
top 30 from final_board.csv, right column is the Codex top 30 parsed
from codex/big_board.md headers. Lines connect the same player and are
colored by how far the two boards disagree.
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[3]
fable = pd.read_csv(REPO / "claude/code/data/processed/final_board.csv")
fable = fable[fable["my_rank"] <= 30][["my_rank", "player"]]

codex_text = (REPO / "codex/big_board.md").read_text()
codex = re.findall(r"^### (\d+)\. (.+?) - Tier", codex_text, re.M)
codex = {normed: int(rank) for rank, name in codex
         for normed in [unicodedata.normalize("NFKD", name)
                        .encode("ascii", "ignore").decode().lower().strip()]}


def norm(name):
    return (unicodedata.normalize("NFKD", name)
            .encode("ascii", "ignore").decode().lower().strip())


BG = "#101418"
PANEL = "#1a2027"
FG = "#f2f2f2"
MUTED = "#8a949e"

fig, ax = plt.subplots(figsize=(8, 10), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 10)
ax.set_ylim(31.8, -3.2)
ax.axis("off")

ax.text(5, -2.4, "ONE PROMPT, TWO AI SCOUTS", ha="center", va="center",
        fontsize=19, fontweight="bold", color=FG)
ax.text(5, -1.2, "2026 NBA Draft top 30, same brief, zero hints, run independently",
        ha="center", va="center", fontsize=8.5, color=MUTED)
ax.text(2.6, -0.1, "CLAUDE FABLE 5", ha="center", va="center",
        fontsize=11, fontweight="bold", color="#5ec8e5")
ax.text(7.4, -0.1, "CODEX GPT 5.5", ha="center", va="center",
        fontsize=11, fontweight="bold", color="#f5c542")

for _, r in fable.iterrows():
    fr = int(r["my_rank"])
    cr = codex.get(norm(r["player"]))
    delta = abs(fr - cr) if cr else None
    if cr is None:
        color, lw = "#e57373", 0
    elif delta >= 5:
        color, lw = "#e57373", 1.8
    elif delta >= 3:
        color, lw = "#f5c542", 1.4
    else:
        color, lw = "#3a4754", 1.0
    ax.text(2.6, fr, f"{fr:>2}  {r['player']}", ha="center", va="center",
            fontsize=7.6, color=FG,
            bbox=dict(boxstyle="round,pad=0.32", fc=PANEL, ec=color, lw=0.8))
    if cr:
        ax.plot([3.85, 6.15], [fr, cr], color=color, lw=lw, alpha=0.85,
                solid_capstyle="round", zorder=1)
    else:
        ax.text(3.95, fr, "not in Codex top 30", ha="left", va="center",
                fontsize=6.0, color="#e57373", style="italic")

fable_names = {norm(p) for p in fable["player"]}
for name_norm, cr in codex.items():
    display = next((n for r, n in re.findall(r"^### (\d+)\. (.+?) - Tier",
                                             codex_text, re.M)
                    if int(r) == cr), name_norm.title())
    in_fable = name_norm in fable_names
    ec = "#3a4754" if in_fable else "#e57373"
    ax.text(7.4, cr, f"{cr:>2}  {display}", ha="center", va="center",
            fontsize=7.6, color=FG,
            bbox=dict(boxstyle="round,pad=0.32", fc=PANEL, ec=ec, lw=0.8))
    if not in_fable:
        ax.text(6.05, cr, "not in Fable top 30", ha="right", va="center",
                fontsize=6.0, color="#e57373", style="italic")

ax.text(5, 31.3,
        "line color = disagreement   grey under 3 spots   gold 3-4   red 5+ or unranked\n"
        "Codex's model includes the market's own ranking (16x its top skill feature) and hugs consensus.\n"
        "Fable excludes draft position entirely and argues with the market when its evidence disagrees.",
        ha="center", va="center", fontsize=7.0, color=MUTED)

out = REPO / "release/images/tweet2_board_comparison.png"
fig.savefig(out, facecolor=BG, bbox_inches="tight", pad_inches=0.18)
print(f"wrote {out}")
