"""Shared feature engineering for Phase 3 modeling.

Feature policy (documented choices, see models/iterations.md):
- Pick slot is EXCLUDED from prospect-skill models (we want talent signal,
  not market echo). A with-pick variant is reported for comparison only.
- Missing data: median impute (medians learned inside CV train folds via
  SimpleImputer in each pipeline) PLUS explicit missingness indicator
  columns computed up front (missingness is a property of the row, no
  leakage). Never silent.
- 3PA rate is normalized to per-40 minutes (3pa_pg * 40 / mpg) so that
  low-minute players are not penalized.
- Career outcome columns that are NaN because the player never appeared in
  an NBA game (161 players, verified notes say "never played") are filled
  with 0 (games/minutes/WS/VORP). They are real draft outcomes, not missing
  data.
"""

import re
import unicodedata

import numpy as np
import pandas as pd

SEED = 42

ANTHRO_FEATURES = [
    "height_in",
    "weight_lbs",
    "wingspan_in",
    "standing_reach_in",
    "wing_minus_height",
]

NCAA_FEATURES = [
    "ncaa_ts_pct",
    "ncaa_usg_pct",
    "ncaa_ast_pct",
    "ncaa_tov_pct",
    "ncaa_stl_pct",
    "ncaa_blk_pct",
    "ncaa_ft_pct",
    "ncaa_3pa_per40",
    "ncaa_obpm",
    "ncaa_bpm",
]

MISS_INDICATORS = [
    "miss_age",
    "miss_anthro",
    "miss_wingspan",
    "miss_ncaa_core",
    "miss_ncaa_adv",
]

SKILL_FEATURES = ["age_at_draft"] + ANTHRO_FEATURES + NCAA_FEATURES + MISS_INDICATORS
PICK_FEATURES = SKILL_FEATURES + ["pick"]


def normalize_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z ]", "", s.lower())
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s)
    return re.sub(r"\s+", " ", s).strip()


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived feature columns; expects historical-style column names."""
    df = df.copy()
    df["wing_minus_height"] = df["wingspan_in"] - df["height_in"]
    df["ncaa_3pa_per40"] = df["ncaa_3pa_pg"] * 40.0 / df["ncaa_mpg"]
    # explicit missingness indicators (1 = value absent before imputation)
    df["miss_age"] = df["age_at_draft"].isna().astype(int)
    df["miss_anthro"] = df["height_in"].isna().astype(int)
    df["miss_wingspan"] = df["wingspan_in"].isna().astype(int)
    df["miss_ncaa_core"] = df["ncaa_ts_pct"].isna().astype(int)
    df["miss_ncaa_adv"] = df["ncaa_obpm"].isna().astype(int)
    return df


def load_historical(path: str) -> pd.DataFrame:
    h = pd.read_csv(path)
    # never-played NBA -> 0 career outcomes (verified: notes say never played)
    for c in ["career_games", "career_minutes", "career_ws", "career_vorp"]:
        h[c] = h[c].fillna(0.0)
    h = add_derived(h)
    h["intl"] = h["ncaa_source"].isna().astype(int)
    return h


def assign_tier(row) -> str:
    """Exact tier definitions, see models/tier_definitions.md."""
    if row["allstar"] == 1:
        return "AllStar"
    if row["career_minutes"] >= 12000 and row["career_ws"] >= 25:
        return "Starter"
    if row["career_minutes"] >= 5000 and row["career_ws"] >= 5:
        return "Rotation"
    if row["career_games"] >= 100 and row["career_ws"] > 2:
        return "Bench"
    return "Bust"


TIER_ORDER = ["AllStar", "Starter", "Rotation", "Bench", "Bust"]


def assign_bust(df: pd.DataFrame) -> pd.Series:
    """Bust = fewer than 100 career games OR near-zero career win shares."""
    return ((df["career_games"] < 100) | (df["career_ws"] < 2.0)).astype(int)


# ---- target transforms (chosen by CV, see iterations.md) ----
TRANSFORMS = {
    "identity": (lambda y: y, lambda z: z),
    "asinh": (np.arcsinh, np.sinh),
    "signed_sqrt": (
        lambda y: np.sign(y) * np.sqrt(np.abs(y)),
        lambda z: np.sign(z) * z**2,
    ),
}
