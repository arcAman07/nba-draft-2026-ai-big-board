"""Render the shareable big-board infographic (figures/social_board.png).

Inputs: data/processed/final_board.csv (ranks, tiers, deltas) and
data/processed/consensus_board.csv (position, school). Output sized 4:5
at 200 dpi, dark theme, suitable for X / Instagram.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
board = pd.read_csv(BASE / "data/processed/final_board.csv")
cons = pd.read_csv(BASE / "data/processed/consensus_board.csv")[
    ["player", "position", "team_school"]
]
df = board.merge(cons, on="player", how="left")
top30 = df[df["my_rank"] <= 30].copy()

TIER_COLORS = {
    "1": "#f5c542",  # gold
    "2": "#5ec8e5",  # cyan
    "3": "#9b8cff",  # violet
    "4": "#7fd17f",  # green
    "5": "#c9c9c9",  # grey
}
TIER_NAMES = {
    "1": "TIER 1  Franchise Cornerstones",
    "2": "TIER 2  High-Leverage Starters",
    "3": "TIER 3  Starter-or-Bust Swings",
    "4": "TIER 4  Rotation Bets, Upside Tails",
    "5": "TIER 5  Specialists / Projects",
}

BG = "#101418"
PANEL = "#1a2027"
FG = "#f2f2f2"
MUTED = "#8a949e"

fig = plt.figure(figsize=(8, 10), dpi=200)
fig.patch.set_facecolor(BG)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 125)
ax.axis("off")

# Header
ax.text(50, 121.5, "2026 NBA DRAFT BIG BOARD", ha="center", va="center",
        fontsize=21, fontweight="bold", color=FG, family="DejaVu Sans")
ax.text(50, 117.8,
        "AI scouting department: 6-board consensus + ML models (1,309 players, 2000-2021)\n"
        "+ historical comps engine + combine data + frame-based film study of the top 20",
        ha="center", va="center", fontsize=7.8, color=MUTED)

# Two columns of 15
col_x = {0: 2.5, 1: 51.5}
row_h = 6.9
top_y = 112.5

for i, (_, r) in enumerate(top30.iterrows()):
    col = 0 if i < 15 else 1
    row = i % 15
    x = col_x[col]
    y = top_y - row * row_h
    tier = str(r["tier"])
    c = TIER_COLORS.get(tier, MUTED)

    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y - 5.6), 46, 5.9,
        boxstyle="round,pad=0.15,rounding_size=0.6",
        linewidth=1.0, edgecolor=c, facecolor=PANEL))
    ax.text(x + 2.6, y - 2.0, f"{int(r['my_rank'])}", ha="center", va="center",
            fontsize=12.5, fontweight="bold", color=c)
    ax.text(x + 5.6, y - 1.3, r["player"], ha="left", va="center",
            fontsize=8.6, fontweight="bold", color=FG)
    pos = r["position"] if isinstance(r["position"], str) else ""
    sch = r["team_school"] if isinstance(r["team_school"], str) else ""
    ax.text(x + 5.6, y - 3.6, f"{pos}  |  {sch}", ha="left", va="center",
            fontsize=6.6, color=MUTED)

    delta = r["consensus_median"] - r["my_rank"]
    if pd.notna(delta) and abs(delta) >= 3:
        sym, dc = ("▲", "#7fd17f") if delta > 0 else ("▼", "#e57373")
        ax.text(x + 43.4, y - 2.6, f"{sym}{abs(delta):.0f}", ha="center",
                va="center", fontsize=7.6, fontweight="bold", color=dc)

# Tier legend
legend_y = 7.6
lx = 3.0
for t in ["1", "2", "3", "4", "5"]:
    ax.add_patch(mpatches.Rectangle((lx, legend_y - 0.9), 1.6, 1.6,
                                    facecolor=TIER_COLORS[t], edgecolor="none"))
    ax.text(lx + 2.2, legend_y, TIER_NAMES[t].split("  ")[1], ha="left",
            va="center", fontsize=5.9, color=MUTED)
    lx += 19.5

ax.text(50, 3.4,
        "▲▼ = rise/fall of 3+ spots vs the 6-board market consensus  |  "
        "built by an autonomous AI pipeline, June 10, 2026",
        ha="center", va="center", fontsize=6.4, color=MUTED)

out = BASE / "figures/social_board.png"
fig.savefig(out, facecolor=BG, bbox_inches="tight", pad_inches=0.15)
print(f"wrote {out}")
