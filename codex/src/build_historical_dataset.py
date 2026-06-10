from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from common import PROCESSED_DIR, RAW_DIR, normalize_name


def draft_year_from_season(value: object) -> Optional[int]:
    match = re.search(r"-(\d{2})$", str(value))
    if not match:
        return None
    return 2000 + int(match.group(1))


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def safe_col(df: pd.DataFrame, name: str) -> pd.Series:
    if name in df.columns:
        return to_num(df[name])
    return pd.Series(np.nan, index=df.index)


def load_jasong() -> pd.DataFrame:
    path = RAW_DIR / "historical" / "jasong_model_db.csv"
    df = pd.read_csv(path)
    draft_year = df["Season"].map(draft_year_from_season)
    pick = to_num(df.get("NBA Draft Pick", pd.Series(np.nan, index=df.index)))
    out = pd.DataFrame(
        {
            "source_dataset": "JasonG7234/NBA-Draft-Model model_db.csv",
            "draft_year": draft_year,
            "pick": pick,
            "player": df["Name"],
            "norm_name": df["Name"].map(normalize_name),
            "position": df.get("Position 1"),
            "school": df.get("School"),
            "conference": df.get("Conference"),
            "age_at_draft": safe_col(df, "Draft Day Age"),
            "height_in": safe_col(df, "Height"),
            "weight_lbs": safe_col(df, "Weight"),
            "games": safe_col(df, "G"),
            "mp": safe_col(df, "MP"),
            "ts_pct": safe_col(df, "TS%"),
            "efg_pct": safe_col(df, "eFG%"),
            "three_par": safe_col(df, "3PAr"),
            "ftr": safe_col(df, "FTr"),
            "orb_pct": safe_col(df, "ORB%"),
            "drb_pct": safe_col(df, "DRB%"),
            "trb_pct": safe_col(df, "TRB%"),
            "ast_pct": safe_col(df, "AST%"),
            "stl_pct": safe_col(df, "STL%"),
            "blk_pct": safe_col(df, "BLK%"),
            "tov_pct": safe_col(df, "TOV%"),
            "usg_pct": safe_col(df, "USG%"),
            "obpm": safe_col(df, "OBPM"),
            "dbpm": safe_col(df, "DBPM"),
            "bpm": safe_col(df, "BPM"),
            "ast_to_tov": safe_col(df, "AST/TOV"),
            "pts_per40": safe_col(df, "PTS/40"),
            "reb_per40": safe_col(df, "TRB/40"),
            "ast_per40": safe_col(df, "AST/40"),
            "stl_per40": safe_col(df, "STL/40"),
            "blk_per40": safe_col(df, "BLK/40"),
            "tov_per40": safe_col(df, "TOV/40"),
            "ft_pct": safe_col(df, "FT%"),
            "three_pct": safe_col(df, "3FG%"),
            "three_pa_per40": safe_col(df, "3FGA/40"),
            "draft_score": safe_col(df, "Draft Score"),
            "nba_mpg": safe_col(df, "NBA MPG"),
        }
    )
    return out[out["draft_year"].between(2009, 2021) & out["pick"].between(1, 60)].copy()


def load_woodfin() -> pd.DataFrame:
    path = RAW_DIR / "historical" / "woodfin_combined_data.csv"
    df = pd.read_csv(path)
    out = pd.DataFrame(
        {
            "source_dataset": "woodfin8/Draft_Machine combined_data.csv",
            "draft_year": safe_col(df, "year"),
            "pick": safe_col(df, "rank"),
            "player": df.get("name", df.get("player")),
            "norm_name": df.get("name", df.get("player")).map(normalize_name),
            "position": np.nan,
            "school": df.get("college"),
            "conference": np.nan,
            "age_at_draft": np.nan,
            "height_in": safe_col(df, "height"),
            "weight_lbs": np.nan,
            "games": safe_col(df, "games_played"),
            "mp": safe_col(df, "minutes_played"),
            "ts_pct": safe_col(df, "true_shooting_percentage"),
            "efg_pct": safe_col(df, "effective_field_goal_percentage"),
            "three_par": np.nan,
            "ftr": safe_col(df, "free_throw_attempt_rate"),
            "orb_pct": np.nan,
            "drb_pct": np.nan,
            "trb_pct": np.nan,
            "ast_pct": np.nan,
            "stl_pct": np.nan,
            "blk_pct": np.nan,
            "tov_pct": safe_col(df, "turnover_percentage"),
            "usg_pct": np.nan,
            "obpm": np.nan,
            "dbpm": np.nan,
            "bpm": np.nan,
            "ast_to_tov": np.nan,
            "pts_per40": safe_col(df, "points_per_40"),
            "reb_per40": safe_col(df, "total_rebounds_per_40"),
            "ast_per40": safe_col(df, "assists_per_40"),
            "stl_per40": safe_col(df, "steals_per_40"),
            "blk_per40": safe_col(df, "blocks_per_40"),
            "tov_per40": safe_col(df, "turnovers_per_40"),
            "ft_pct": safe_col(df, "free_throw_percentage"),
            "three_pct": safe_col(df, "three_point_percentage"),
            "three_pa_per40": safe_col(df, "three_pointers_per_40"),
            "draft_score": np.nan,
            "nba_mpg": safe_col(df, "mins played (per game)"),
            "career_games": safe_col(df, "games"),
            "career_minutes": safe_col(df, "mins played (total)"),
            "career_ws": safe_col(df, "win shares"),
            "career_ws48": safe_col(df, "ws/48"),
            "career_bpm": safe_col(df, "box +/-"),
            "career_vorp": safe_col(df, "value overall replacement player"),
        }
    )
    return out[out["draft_year"].between(2000, 2021) & out["pick"].between(1, 60)].copy()


def merge_combine(df: pd.DataFrame) -> pd.DataFrame:
    combine_path = RAW_DIR / "historical" / "achou11_nba_draft_combine_all_years.csv"
    if not combine_path.exists():
        return df
    combine = pd.read_csv(combine_path)
    combine["norm_name"] = combine["Player"].map(normalize_name)
    combine["draft_year"] = to_num(combine["Year"])
    keep = combine[
        [
            "norm_name",
            "draft_year",
            "Height (No Shoes)",
            "Height (With Shoes)",
            "Wingspan",
            "Standing reach",
            "Vertical (Max)",
            "Vertical (No Step)",
            "Weight",
            "Agility",
            "Sprint",
        ]
    ].rename(
        columns={
            "Height (No Shoes)": "combine_height_no_shoes_in",
            "Height (With Shoes)": "combine_height_with_shoes_in",
            "Wingspan": "wingspan_in",
            "Standing reach": "standing_reach_in",
            "Vertical (Max)": "max_vert_in",
            "Vertical (No Step)": "standing_vert_in",
            "Weight": "combine_weight_lbs",
            "Agility": "lane_agility_s",
            "Sprint": "sprint_s",
        }
    )
    out = df.merge(keep, on=["norm_name", "draft_year"], how="left")
    out["height_in"] = out["combine_height_no_shoes_in"].combine_first(out["height_in"])
    out["weight_lbs"] = out["combine_weight_lbs"].combine_first(out["weight_lbs"])
    return out


def merge_woodfin_outcomes(base: pd.DataFrame, woodfin: pd.DataFrame) -> pd.DataFrame:
    outcome_cols = ["career_games", "career_minutes", "career_ws", "career_ws48", "career_bpm", "career_vorp"]
    src = woodfin[["norm_name", "draft_year", *[c for c in outcome_cols if c in woodfin.columns]]].drop_duplicates(
        ["norm_name", "draft_year"]
    )
    out = base.merge(src, on=["norm_name", "draft_year"], how="left", suffixes=("", "_woodfin"))
    for col in outcome_cols:
        other = f"{col}_woodfin"
        if other in out.columns:
            if col in out.columns:
                out[col] = out[col].combine_first(out[other])
            else:
                out[col] = out[other]
            out = out.drop(columns=[other])
    return out


def add_538(df: pd.DataFrame) -> pd.DataFrame:
    path = RAW_DIR / "historical" / "fivethirtyeight_historical_projections.csv"
    if not path.exists():
        return df
    fte = pd.read_csv(path)
    fte["norm_name"] = fte["Player"].map(normalize_name)
    fte = fte.rename(
        columns={
            "Draft Year": "draft_year",
            "Projected SPM": "fte_projected_spm",
            "Superstar": "fte_superstar_prob",
            "Starter": "fte_starter_prob",
            "Role Player": "fte_role_player_prob",
            "Bust": "fte_bust_prob",
        }
    )
    return df.merge(
        fte[
            [
                "norm_name",
                "draft_year",
                "fte_projected_spm",
                "fte_superstar_prob",
                "fte_starter_prob",
                "fte_role_player_prob",
                "fte_bust_prob",
            ]
        ],
        on=["norm_name", "draft_year"],
        how="left",
    )


def classify_tier(row: pd.Series) -> str:
    mpg = row.get("nba_mpg")
    vorp = row.get("career_vorp")
    ws = row.get("career_ws")
    if pd.notna(mpg) and mpg >= 30 and (pd.isna(vorp) or vorp >= 12):
        return "star"
    if pd.notna(mpg) and mpg >= 24:
        return "starter"
    if pd.notna(mpg) and mpg >= 15:
        return "rotation"
    if pd.notna(mpg) and mpg >= 8:
        return "bench"
    if pd.notna(ws) and ws >= 20:
        return "rotation"
    return "bust"


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    jason = load_jasong()
    woodfin = load_woodfin()
    combined = pd.concat([woodfin[woodfin["draft_year"] < 2009], jason], ignore_index=True)
    combined = merge_woodfin_outcomes(combined, woodfin)
    combined = merge_combine(combined)
    combined = add_538(combined)
    combined["draft_year"] = combined["draft_year"].astype(int)
    combined["pick"] = combined["pick"].astype(float)
    combined["outcome_mpg"] = combined["nba_mpg"]
    combined["outcome_tier"] = combined.apply(classify_tier, axis=1)
    combined["outcome_value"] = combined["outcome_mpg"]
    combined = combined.sort_values(["draft_year", "pick", "player"]).drop_duplicates(["draft_year", "pick"])
    combined.to_csv(PROCESSED_DIR / "historical.csv", index=False)

    coverage = {
        "rows": int(len(combined)),
        "draft_year_min": int(combined["draft_year"].min()),
        "draft_year_max": int(combined["draft_year"].max()),
        "first_round_rows": int(combined["pick"].between(1, 30).sum()),
        "coverage": {
            col: float(combined[col].notna().mean())
            for col in [
                "age_at_draft",
                "height_in",
                "weight_lbs",
                "wingspan_in",
                "standing_reach_in",
                "ts_pct",
                "usg_pct",
                "bpm",
                "outcome_mpg",
                "career_vorp",
                "career_ws",
            ]
            if col in combined.columns
        },
        "notes": [
            "Rows 2000-2008 use woodfin8/Draft_Machine because the richer JasonG dataset begins in 2009.",
            "Rows 2009-2021 use JasonG7234/NBA-Draft-Model for pre-draft features and NBA MPG outcome proxy.",
            "Career WS/VORP coverage is strongest for woodfin rows and missing for many 2019-2021 rows; the primary model target is NBA MPG.",
        ],
    }
    (PROCESSED_DIR / "historical_coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")
    print(json.dumps(coverage, indent=2))


if __name__ == "__main__":
    main()
