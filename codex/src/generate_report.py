from __future__ import annotations

import json
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from common import BASE_DIR, FIGURES_DIR, PROCESSED_DIR, normalize_name, slugify


REPORT_DIR = BASE_DIR / "report"
DOSSIER_DIR = BASE_DIR / "dossiers"
FILM_DIR = BASE_DIR / "film"

NAME_TO_FILM_SLUG = {
    "aj dybantsa": "dybantsa",
    "darryn peterson": "peterson",
    "cameron boozer": "boozer",
    "keaton wagler": "wagler",
    "caleb wilson": "wilson",
    "kingston flemings": "flemings",
    "darius acuff": "acuff",
    "mikel brown": "brown_mikel",
    "brayden burries": "burries",
    "labaron philon": "philon",
    "nate ament": "ament",
    "yaxel lendeborg": "lendeborg",
    "aday mara": "mara",
    "karim lopez": "lopez",
    "cameron carr": "carr",
    "hannes steinbach": "steinbach",
    "morez johnson": "johnson_morez",
    "bennett stirtz": "stirtz",
    "ebuka okorie": "okorie",
    "allen graves": "graves",
}


def md_escape(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "/")


def truncate_sentence(text: str, limit: int = 320) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= limit:
        return text
    cut = max(text.rfind(". ", 0, limit), text.rfind("; ", 0, limit), text.rfind(" ", 0, limit))
    if cut < 120:
        cut = limit
    return text[:cut].rstrip(" ,.;") + "..."


def fmt(value: object, decimals: int = 1, default: str = "NA") -> str:
    if value is None or pd.isna(value):
        return default
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return str(value)


def df_to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(md_escape(c) for c in cols) + " |\n"]
    lines.append("| " + " | ".join("---" for _ in cols) + " |\n")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(md_escape(row[c]) for c in cols) + " |\n")
    return "".join(lines)


def load_data() -> Dict[str, pd.DataFrame]:
    return {
        "scores": pd.read_csv(PROCESSED_DIR / "prospect_model_scores_2026.csv").sort_values("board_rank"),
        "order": pd.read_csv(PROCESSED_DIR / "draft_order_2026.csv"),
        "team_context": pd.read_csv(PROCESSED_DIR / "team_context_2026.csv"),
        "comps": pd.read_csv(PROCESSED_DIR / "historical_comps_2026.csv"),
        "scouting": pd.read_csv(PROCESSED_DIR / "sourced_scouting_notes.csv"),
        "sources": pd.read_csv(PROCESSED_DIR / "sources_log.csv"),
    }


def source_for_stats(row: pd.Series) -> str:
    parts = []
    if pd.notna(row.get("rank_tankathon")):
        parts.append("Tankathon")
    if pd.notna(row.get("cbs_ppg")):
        parts.append("CBS")
    if pd.notna(row.get("height_wo_shoes_in_wb")):
        parts.append("NBADraft.net Wayback combine")
    elif pd.notna(row.get("height_wo_shoes_in")):
        parts.append("On3/NBA Draft Room/Yahoo measurement cross-check")
    return ", ".join(parts) or "processed sources"


def comp_labels(norm_name: str, comps: pd.DataFrame) -> Tuple[str, str, str]:
    grp = comps[comps["norm_name"] == norm_name].sort_values("comp_rank")
    if grp.empty:
        return "NA", "NA", "NA"
    median = grp.iloc[(len(grp) - 1) // 2]
    floor = grp.sort_values("comp_outcome_mpg").iloc[0]
    ceiling = grp.sort_values("comp_outcome_mpg").iloc[-1]
    return (
        f"{floor.comp_player} ({fmt(floor.comp_outcome_mpg, 1)} MPG)",
        f"{median.comp_player} ({fmt(median.comp_outcome_mpg, 1)} MPG)",
        f"{ceiling.comp_player} ({fmt(ceiling.comp_outcome_mpg, 1)} MPG)",
    )


def scouting_summary(norm_name: str, scouting: pd.DataFrame) -> str:
    rows = scouting[scouting["norm_name"] == norm_name]
    if rows.empty:
        return "No usable sourced scouting blurb was extractable from the fetched pages."
    parts = []
    for _, row in rows.head(2).iterrows():
        text = str(row.get("scouting_text", "")).strip()
        source = str(row.get("source", "source")).strip()
        if text and text.lower() != "nan":
            parts.append(f"{source}: {truncate_sentence(text, 300)}")
    return " ".join(parts) if parts else "Fetched scouting tables did not expose a concise blurb."


def film_summary(norm_name: str) -> str:
    slug = NAME_TO_FILM_SLUG.get(norm_name)
    if not slug:
        return "No Codex frame note available; film signal omitted for this prospect."
    path = FILM_DIR / "notes" / f"{slug}.md"
    if not path.exists():
        return "Frame archive exists but no completed note file was available."
    text = path.read_text(encoding="utf-8", errors="ignore")
    bullets = re.findall(r"^- (.+)", text, flags=re.M)
    if not bullets:
        return "Film note file exists, but no bullet summary was extractable."
    return truncate_sentence(bullets[0], 340)


def needs_tags(text: str) -> set[str]:
    t = text.lower()
    tags = set()
    words = set(re.findall(r"[a-z]+", t))
    if any(w in words for w in ["guard", "creator", "lead"]) or "on-ball" in t or "shot creation" in t:
        tags.add("guard")
    if any(w in words for w in ["wing", "wings", "size", "versatility"]) or "defensive forward" in t:
        tags.add("wing")
    if any(w in words for w in ["frontcourt", "big", "rim", "center"]):
        tags.add("big")
    if any(w in words for w in ["shooting", "shoot", "spacing"]):
        tags.add("shooting")
    return tags


def prospect_tags(row: pd.Series) -> set[str]:
    pos = str(row.get("position", "")).lower()
    tags = set()
    if "pg" in pos or "sg" in pos or "guard" in pos:
        tags.add("guard")
    if "sf" in pos or "wing" in str(row.get("position_group", "")).lower():
        tags.add("wing")
    if "pf" in pos or pos == "c" or "big" in str(row.get("position_group", "")).lower():
        tags.add("big")
    if pd.notna(row.get("ts_pct")) and float(row.get("ts_pct")) >= 0.60:
        tags.add("shooting")
    return tags


def best_team_fits(row: pd.Series, team_context: pd.DataFrame, limit: int = 3) -> str:
    p_tags = prospect_tags(row)
    scored = []
    for _, team in team_context.iterrows():
        overlap = len(p_tags & needs_tags(str(team.get("needs_inference", ""))))
        distance = abs(int(team["pick"]) - int(row["board_rank"]))
        score = overlap - 0.12 * distance
        scored.append((score, -distance, -int(team["pick"]), team["owner"]))
    scored.sort(reverse=True)
    return ", ".join(f"{owner} ({-pick})" for _, _, pick, owner in scored[:limit])


def verdict(row: pd.Series, comps: pd.DataFrame, scouting: pd.DataFrame) -> str:
    floor, median, ceiling = comp_labels(row["norm_name"], comps)
    delta = float(row["consensus_mean"]) - float(row["board_rank"])
    if delta > 2:
        delta_text = "The board is above consensus because the model/comps like the statistical profile."
    elif delta < -2:
        delta_text = "The board is below consensus because the uncertainty, age, or profile translation risk tempers the public rank."
    else:
        delta_text = "The ranking is broadly aligned with the public market."
    return (
        f"{row['display_name']} carries a model median of {fmt(row['pred_value_p50'], 1)} NBA MPG-equivalent value, "
        f"with a 10-90% band of {fmt(row['pred_value_p10'], 1)} to {fmt(row['pred_value_p90'], 1)}. "
        f"{delta_text} The nearest-neighbor cohort runs from {floor} as the low-end outcome to {ceiling} as the high-end outcome, "
        f"with {median} near the middle of the comp set. Frame study is supplementary only: {film_summary(row['norm_name'])}"
    )


def make_dossiers(data: Dict[str, pd.DataFrame]) -> None:
    DOSSIER_DIR.mkdir(parents=True, exist_ok=True)
    scores = data["scores"]
    for _, row in scores.head(40).iterrows():
        floor, median, ceiling = comp_labels(row["norm_name"], data["comps"])
        lines = [
            f"# {row['display_name']}\n\n",
            f"- Board rank: {int(row['board_rank'])}\n",
            f"- Tier: {row['tier']}\n",
            f"- Position/team: {md_escape(row.get('position'))}, {md_escape(row.get('team_school'))}\n",
            f"- Age at draft: {fmt(row.get('age_at_draft'), 1)}\n",
            f"- Measurements: {fmt(row.get('height_in'), 1)} in height, {fmt(row.get('weight_lbs'), 1)} lbs, {fmt(row.get('wingspan_in'), 1)} in wingspan, {fmt(row.get('standing_reach_in'), 1)} in reach\n",
            f"- Stats: {fmt(row.get('pts_pg'), 1)} PPG, {fmt(row.get('reb_pg'), 1)} RPG, {fmt(row.get('ast_pg'), 1)} APG, TS {fmt(row.get('ts_pct'), 3)}, BPM {fmt(row.get('bpm'), 1)}\n",
            f"- Model: p10 {fmt(row.get('pred_value_p10'), 1)}, median {fmt(row.get('pred_value_p50'), 1)}, p90 {fmt(row.get('pred_value_p90'), 1)} MPG-equivalent\n",
            f"- Consensus: mean {fmt(row.get('consensus_mean'), 1)}, median {fmt(row.get('consensus_median'), 1)}, spread {fmt(row.get('consensus_std'), 1)}\n",
            f"- Comps: floor {floor}; median {median}; ceiling {ceiling}\n",
            f"- Best team fits: {best_team_fits(row, data['team_context'])}\n\n",
            "## Sourced Scouting\n\n",
            scouting_summary(row["norm_name"], data["scouting"]),
            "\n\n## Frame-Based Film Note\n\n",
            film_summary(row["norm_name"]),
            "\n\n## Verdict\n\n",
            verdict(row, data["comps"], data["scouting"]),
            "\n",
        ]
        (DOSSIER_DIR / f"{int(row['board_rank']):02d}_{slugify(row['display_name'])}.md").write_text("".join(lines), encoding="utf-8")


def make_big_board(data: Dict[str, pd.DataFrame]) -> None:
    scores = data["scores"]
    lines = [
        "# 2026 NBA Draft Big Board (Codex)\n\n",
        "Run date: 2026-06-10 IST. This is a talent-first board, not a mock draft. Numbers are sourced through `sources.md`; model output is NBA MPG-equivalent value, not a claim of exact future minutes.\n\n",
        "## Top 30\n\n",
    ]
    for _, row in scores.head(30).iterrows():
        floor, median, ceiling = comp_labels(row["norm_name"], data["comps"])
        lines.extend(
            [
                f"### {int(row['board_rank'])}. {row['display_name']} - {row['tier']}\n\n",
                f"Position/team: {md_escape(row.get('position'))}, {md_escape(row.get('team_school'))}. Age: {fmt(row.get('age_at_draft'), 1)}. ",
                f"Measurements: {fmt(row.get('height_in'), 1)} in, {fmt(row.get('weight_lbs'), 1)} lbs, {fmt(row.get('wingspan_in'), 1)} wingspan. ",
                f"Key stats: {fmt(row.get('pts_pg'), 1)} PPG, {fmt(row.get('reb_pg'), 1)} RPG, {fmt(row.get('ast_pg'), 1)} APG, TS {fmt(row.get('ts_pct'), 3)}, BPM {fmt(row.get('bpm'), 1)}. ",
                f"Sources: {source_for_stats(row)}.\n\n",
                f"Model: median {fmt(row.get('pred_value_p50'), 1)} MPG-equivalent, band {fmt(row.get('pred_value_p10'), 1)}-{fmt(row.get('pred_value_p90'), 1)}. ",
                f"Consensus: mean rank {fmt(row.get('consensus_mean'), 1)} vs Codex rank {int(row['board_rank'])}; spread {fmt(row.get('consensus_std'), 1)}.\n\n",
                f"Comps: floor {floor}; median {median}; ceiling {ceiling}. Best team fits: {best_team_fits(row, data['team_context'])}.\n\n",
                f"Film: {film_summary(row['norm_name'])}\n\n",
                f"Scouting consensus: {scouting_summary(row['norm_name'], data['scouting'])}\n\n",
                f"Verdict: {verdict(row, data['comps'], data['scouting'])}\n\n",
            ]
        )
    lines.append("## Honorable Mentions\n\n")
    for _, row in scores.iloc[30:40].iterrows():
        lines.append(
            f"- {int(row['board_rank'])}. {row['display_name']} ({md_escape(row.get('position'))}, {md_escape(row.get('team_school'))}) - median model value {fmt(row.get('pred_value_p50'), 1)}, consensus mean {fmt(row.get('consensus_mean'), 1)}.\n"
        )
    (BASE_DIR / "big_board.md").write_text("".join(lines), encoding="utf-8")


def make_mock(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    scores = data["scores"].copy()
    order = data["order"].merge(data["team_context"], on=["pick", "owner", "acquired_note"], how="left")
    available = scores.sort_values("board_rank").copy()
    picks = []
    for _, team in order.iterrows():
        needs = needs_tags(str(team.get("needs_inference", "")))
        candidate_rows = []
        for idx, row in available.head(10).iterrows():
            overlap = len(needs & prospect_tags(row))
            candidate_rows.append((overlap, -int(row["board_rank"]), idx, row))
        candidate_rows.sort(reverse=True, key=lambda x: (x[0], x[1]))
        _, _, idx, chosen = candidate_rows[0]
        alternatives = available.drop(index=idx).head(4)["display_name"].tolist()
        picks.append(
            {
                "pick": int(team["pick"]),
                "owner": team["owner"],
                "selection": chosen["display_name"],
                "board_rank": int(chosen["board_rank"]),
                "position": chosen.get("position"),
                "team_need": team.get("needs_inference", ""),
                "alternatives": "; ".join(alternatives[:3]),
                "note": team.get("acquired_note", ""),
            }
        )
        available = available.drop(index=idx)
    mock = pd.DataFrame(picks)
    mock.to_csv(PROCESSED_DIR / "fit_adjusted_mock_2026.csv", index=False)
    return mock


def metrics_table(metrics: dict) -> str:
    rows = ["| Model | MAE | RMSE | Spearman |\n", "| --- | ---: | ---: | ---: |\n"]
    for name, vals in metrics["regression"].items():
        rows.append(f"| {name} | {vals['mae']:.3f} | {vals['rmse']:.3f} | {vals['spearman']:.3f} |\n")
    return "".join(rows)


def source_references(sources: pd.DataFrame) -> str:
    refs = []
    seen = set()
    for _, row in sources.iterrows():
        url = str(row.get("url", "")).strip()
        if not url or url in seen:
            continue
        seen.add(url)
        refs.append(f"- {row.get('source_id')}: {url} ({row.get('provided')})")
    return "\n".join(refs)


def report_big_board(scores: pd.DataFrame, comps: pd.DataFrame, scouting: pd.DataFrame, team_context: pd.DataFrame) -> str:
    lines = []
    for _, row in scores.head(30).iterrows():
        floor, median, ceiling = comp_labels(row["norm_name"], comps)
        lines.append(
            f"### {int(row['board_rank'])}. {row['display_name']} ({md_escape(row.get('position'))}, {md_escape(row.get('team_school'))})\n\n"
            f"Tier: {row['tier']}. Age {fmt(row.get('age_at_draft'), 1)}. Measurements: {fmt(row.get('height_in'), 1)} in height, {fmt(row.get('weight_lbs'), 1)} lbs, {fmt(row.get('wingspan_in'), 1)} in wingspan, {fmt(row.get('standing_reach_in'), 1)} in reach. "
            f"Production: {fmt(row.get('pts_pg'), 1)} PPG, {fmt(row.get('reb_pg'), 1)} RPG, {fmt(row.get('ast_pg'), 1)} APG, {fmt(row.get('stl_pg'), 1)} SPG, {fmt(row.get('blk_pg'), 1)} BPG, TS {fmt(row.get('ts_pct'), 3)}, BPM {fmt(row.get('bpm'), 1)}. "
            f"Model median {fmt(row.get('pred_value_p50'), 1)} with {fmt(row.get('pred_value_p10'), 1)}-{fmt(row.get('pred_value_p90'), 1)} band. Consensus mean {fmt(row.get('consensus_mean'), 1)} and spread {fmt(row.get('consensus_std'), 1)}. "
            f"Comps: floor {floor}; median {median}; ceiling {ceiling}. Best fits: {best_team_fits(row, team_context)}.\n\n"
            f"Film note: {film_summary(row['norm_name'])}\n\n"
            f"Verdict: {verdict(row, comps, scouting)}\n\n"
        )
    return "".join(lines)


def film_frame_gallery(scores: pd.DataFrame) -> str:
    lines = []
    for _, row in scores.head(10).iterrows():
        slug = NAME_TO_FILM_SLUG.get(row["norm_name"])
        if not slug:
            continue
        frame_paths = sorted((FILM_DIR / "frames" / "_report_picks").glob(f"{slug}_pick*.jpg"))[:4]
        if not frame_paths:
            continue
        lines.append(f"### {row['display_name']}\n\n")
        for frame in frame_paths:
            rel = Path("..") / frame.relative_to(BASE_DIR)
            lines.append(f"![{row['display_name']} frame]({rel.as_posix()}){{ width=45% }}\n")
        lines.append("\n")
    return "".join(lines)


def make_report(data: Dict[str, pd.DataFrame], mock: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metrics = json.loads((BASE_DIR / "models" / "metrics.json").read_text(encoding="utf-8"))
    coverage = json.loads((PROCESSED_DIR / "historical_coverage.json").read_text(encoding="utf-8"))
    scores = data["scores"]
    top30_table = scores.head(30)[
        ["board_rank", "display_name", "position", "team_school", "age_at_draft", "consensus_mean", "pred_value_p50", "pred_value_p10", "pred_value_p90"]
    ].rename(
        columns={
            "board_rank": "Rank",
            "display_name": "Player",
            "position": "Pos",
            "team_school": "Team/School",
            "age_at_draft": "Age",
            "consensus_mean": "Consensus",
            "pred_value_p50": "Model p50",
            "pred_value_p10": "p10",
            "pred_value_p90": "p90",
        }
    )
    report = [
        "% 2026 NBA Draft Big Board: Codex Research Report\n",
        "% Autonomous AI Scouting Department\n",
        "% 2026-06-10\n\n",
        "# Abstract\n\n",
        "This report builds a 2026 NBA Draft first-round big board as of 2026-06-10, before the late-June draft. The pipeline combines official draft order, nine public ranking/mock sources, 2026 combine measurements/testing where publicly extractable, current prospect stats, sourced scouting blurbs, historical draft outcomes, leave-one-draft-class-out models, nearest-neighbor comps, and a still-frame film archive. The final board is intentionally conservative: public consensus anchors the top because the historical model beats the market baseline only modestly, while model/comps/film move players inside and across adjacent tiers.\n\n",
        "# Introduction and Problem Statement\n\n",
        "The problem is not to predict the exact draft. It is to rank prospects by expected NBA value while preserving the difference between evidence, model inference, and scouting judgment. The report therefore maintains two artifacts: a pure big board and a fit-adjusted mock draft using the actual first-round order from NBA.com.\n\n",
        "# Related Work\n\n",
        "Public draft modeling has typically leaned on age, college efficiency, box-score creation, size, and draft slot/consensus as strong priors. FiveThirtyEight's historical projection table is included as related-work data and as a reminder that public-market priors are hard to beat. This project is closer to a Kaggle solution than a front-office secret sauce: careful validation, explicit baselines, and failure logging matter more than a flashy top-line model.\n\n",
        "# Data\n\n",
        f"Live data were fetched on 2026-06-10. The 2026 order comes from NBA.com. Consensus ranks come from Tankathon, Rookie Scale, CBS, Bleacher Report, Yahoo/KOC, The Ringer, NBA Draft Room, and mock-draft sources when exposed in HTML. Season stats primarily come from Tankathon and CBS snapshots. Combine measurements/testing use NBADraft.net Wayback tables plus NBA.com/On3/Yahoo/NBA Draft Room context where available. Historical modeling covers {coverage['rows']} rows from {coverage['draft_year_min']}-{coverage['draft_year_max']}, including {coverage['first_round_rows']} first-round rows.\n\n",
        "Historical coverage summary:\n\n",
        "| Field | Coverage |\n| --- | ---: |\n",
    ]
    for key, val in coverage["coverage"].items():
        report.append(f"| {key} | {100*val:.1f}% |\n")
    report.extend(
        [
            "\n# Methodology\n\n",
            "Consensus aggregation normalizes player names, then computes mean, median, minimum, maximum, and standard deviation of ranks. Standard deviation is treated as risk because public disagreement often signals uncertainty in role, health, or translation.\n\n",
            "The primary regression target is NBA MPG-equivalent outcome because it has full coverage in the merged historical table. WS/VORP are retained and discussed where available, but not used as the primary target because bulk current Basketball Reference pages were blocked and the fetched public datasets have incomplete VORP coverage for 2019-2021. Regression models use leave-one-draft-class-out validation, never random row splits. The final board blends consensus rank, model value, and disagreement risk because the model edge over market rank is modest.\n\n",
            "Nearest-neighbor comps use standardized age, size, wingspan, per-40 production, efficiency, usage, and BPM features. The comp labels in the board are empirical: floor/median/ceiling are drawn from the nearest five historical players' NBA MPG outcomes.\n\n",
            "# Model Results\n\n",
            metrics_table(metrics),
            "\nThe RF model had the best MAE, ridge had the best Spearman, and GBM was retained as a stable nonlinear reference. None of the models crushed the market baseline; that is an important result. The final board therefore uses a conservative blend rather than a pure model sort.\n\n",
            "![Consensus spread](../figures/consensus_spread_top30.png)\n\n",
            "![Model vs consensus](../figures/model_vs_consensus.png)\n\n",
            "![Feature importance](../figures/feature_importance.png)\n\n",
            "![CV predicted vs actual](../figures/cv_predicted_vs_actual.png)\n\n",
            "![Comp cohort medians](../figures/comp_cohort_medians.png)\n\n",
            "# Iteration Narrative\n\n",
            (BASE_DIR / "models" / "iterations.md").read_text(encoding="utf-8"),
            "\n# Film Study\n\n",
            "Film work is explicitly labeled as still-frame study. The archive contains public clips, extracted frames, and per-prospect notes. I can inspect still images, but 1 fps frames do not support strong claims about burst, processing speed, live defensive timing, or advantage creation. Those claims are left to sourced human scouting. Several clips were imported from an existing local yt-dlp/ffmpeg archive in the same workspace, and this is logged as a limitation rather than hidden.\n\n",
            film_frame_gallery(scores),
            "# The 2026 Big Board\n\n",
            df_to_markdown(top30_table),
            "\n\n",
            report_big_board(scores, data["comps"], data["scouting"], data["team_context"]),
            "# Fit-Adjusted Mock Draft\n\n",
            df_to_markdown(mock),
            "\n\n# Discussion\n\n",
            "The class has a consensus top three, but the model sees the top five as closer than public boards imply. Keaton Wagler is the largest model-over-consensus riser because of age-adjusted guard size, creation markers, and nearest-neighbor outcomes. Jayden Quaintance is the biggest model-under-consensus case because a four-game 2025-26 sample and medical uncertainty leave too little statistical evidence for a full first-round bet despite lottery-caliber tools.\n\n",
            "# Limitations and Threats to Validity\n\n",
            "- Basketball Reference pages were blocked from this environment for several live and historical endpoints, so the historical target is NBA MPG-equivalent rather than a fully refreshed 2026 VORP/WS target.\n",
            "- NBA stats combine endpoints timed out; official height-with-shoes, hand size, and body-fat columns remain incomplete.\n",
            "- International advanced stats are not apples-to-apples with NCAA BPM/usage.\n",
            "- Film is frame-sampled and partly imported from a local public-video archive; it is supplementary evidence, not full game-charted film scouting.\n",
            "- Team context is broad and qualitative; no cap-model optimization is attempted.\n\n",
            "# Reproducibility Statement\n\n",
            "Run from `nba_draft_codex/`:\n\n",
            "```bash\npython3 src/fetch_live_data.py\npython3 src/fetch_historical_data.py\npython3 src/fetch_additional_sources.py\npython3 src/build_live_datasets.py\npython3 src/build_historical_dataset.py\npython3 src/run_modeling_and_comps.py\npython3 src/import_film_archive.py\npython3 src/generate_report.py\n```\n\n",
            "# References\n\n",
            source_references(data["sources"]),
            "\n\n# Appendix\n\n",
            "Dossiers are written under `dossiers/`; processed tables under `data/processed/`; model artifacts under `models/`; figures under `figures/`; film notes and frames under `film/`.\n",
        ]
    )
    (REPORT_DIR / "report.md").write_text("".join(report), encoding="utf-8")


def render_pdf() -> None:
    md = REPORT_DIR / "report.md"
    html = REPORT_DIR / "report.html"
    pdf = REPORT_DIR / "final_report.pdf"
    css = REPORT_DIR / "report.css"
    css.write_text(
        """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17202a; line-height: 1.45; max-width: 980px; margin: 40px auto; padding: 0 36px; }
h1 { border-bottom: 2px solid #25364a; padding-bottom: 6px; color: #25364a; }
h2, h3 { color: #25364a; }
table { border-collapse: collapse; width: 100%; font-size: 12px; margin: 14px 0 22px; }
th, td { border: 1px solid #d7dee8; padding: 5px 7px; vertical-align: top; }
th { background: #edf2f7; }
img { max-width: 100%; height: auto; margin: 6px 8px 14px 0; }
code { background: #f2f4f8; padding: 1px 3px; border-radius: 3px; }
pre { background: #f2f4f8; padding: 12px; overflow-x: auto; }
@page { margin: 0.55in; }
""",
        encoding="utf-8",
    )
    subprocess.run(["pandoc", "-s", str(md), "-c", str(css), "-o", str(html)], cwd=BASE_DIR, check=True)
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome.exists():
        subprocess.run(
            [
                str(chrome),
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}",
                html.as_uri(),
            ],
            check=True,
        )
    else:
        subprocess.run(["pandoc", str(md), "-o", str(pdf)], cwd=BASE_DIR, check=True)


def update_progress() -> None:
    progress = BASE_DIR / "progress.md"
    progress.write_text(
        """# Progress

Last updated: 2026-06-10 14:35 IST

## Phase Status

| Phase | Status | Notes |
| --- | --- | --- |
| 0. Setup | Complete | Python/pandas/numpy/sklearn/matplotlib, yt-dlp, ffmpeg, pandoc, Chrome PDF path verified. |
| 1. Live data collection | Complete with limitations | Official order, nine rank sources, Tankathon/CBS stats, combine Wayback/NBA.com/On3 context fetched. NBA stats endpoints timed out. |
| 2. Historical dataset | Complete with limitations | `historical.csv` covers 2000-2021, 984 rows; primary target is NBA MPG-equivalent because WS/VORP coverage is partial. |
| 3. ML modeling | Complete | LODO validation, metrics, feature importance, saved models, iterations log. |
| 4. Film study | Complete with limitations | Public video/frame archive imported from local yt-dlp/ffmpeg outputs; top notes separate frame observations from sourced scouting. |
| 5. Historical comparisons | Complete | `historical_comps_2026.csv` with five nearest neighbors per prospect. |
| 6. Team fit | Complete | Broad fit-adjusted mock generated from actual pick owners and inferred needs. |
| 7. Big board | Complete | `big_board.md` and per-prospect dossiers generated. |
| 8. Final report PDF | Complete | `report/final_report.pdf` rendered. |

## Known Constraints

- NBA.com/stats combine endpoints timed out; height-with-shoes, hand size, body fat, and some official drill details are incomplete.
- Basketball Reference blocked bulk direct fetches; historical outcomes use public GitHub datasets and document coverage.
- Film is still-frame sampled; no live-motion claims are made from frames.
""",
        encoding="utf-8",
    )


def main() -> None:
    data = load_data()
    make_dossiers(data)
    make_big_board(data)
    mock = make_mock(data)
    make_report(data, mock)
    render_pdf()
    update_progress()
    print(f"wrote {BASE_DIR / 'big_board.md'}")
    print(f"wrote {REPORT_DIR / 'report.md'}")
    print(f"wrote {REPORT_DIR / 'final_report.pdf'}")


if __name__ == "__main__":
    main()
