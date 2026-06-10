from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from common import BASE_DIR, FIGURES_DIR, PROCESSED_DIR


REPORT_DIR = BASE_DIR / "report"
TEX_PATH = REPORT_DIR / "report.tex"
PDF_PATH = REPORT_DIR / "final_report.pdf"
LATEX_PDF_PATH = REPORT_DIR / "final_report_latex.pdf"
FILM_NOTES_DIR = BASE_DIR / "film/notes"
REPORT_FRAMES_DIR = BASE_DIR / "film/frames/_report_picks"

FEATURES_NUMERIC = [
    "market_rank",
    "age_at_draft",
    "height_in",
    "weight_lbs",
    "wingspan_in",
    "standing_reach_in",
    "pts_per40",
    "reb_per40",
    "ast_per40",
    "stl_per40",
    "blk_per40",
    "tov_per40",
    "ts_pct",
    "usg_pct",
    "obpm",
    "dbpm",
    "bpm",
    "ft_pct",
    "three_pct",
    "three_pa_per40",
]
FEATURES_CATEGORICAL = ["position_group"]
COMP_FEATURES = [
    "age_at_draft",
    "height_in",
    "weight_lbs",
    "wingspan_in",
    "pts_per40",
    "reb_per40",
    "ast_per40",
    "stl_per40",
    "blk_per40",
    "ts_pct",
    "usg_pct",
    "bpm",
]

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


def tex(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def url(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return r"\url{" + text.replace("}", "%7D").replace("{", "%7B") + "}"


def fmt(value: object, decimals: int = 1, default: str = "NA") -> str:
    try:
        if pd.isna(value):
            return default
        return f"{float(value):.{decimals}f}"
    except Exception:
        return tex(value)


def pct(value: object, decimals: int = 0, default: str = "NA") -> str:
    try:
        if pd.isna(value):
            return default
        return f"{100 * float(value):.{decimals}f}%"
    except Exception:
        return default


def short(text: object, limit: int = 420) -> str:
    raw = re.sub(r"\s+", " ", "" if text is None else str(text)).strip()
    if len(raw) <= limit:
        return raw
    cut = max(raw.rfind(". ", 0, limit), raw.rfind("; ", 0, limit), raw.rfind(" ", 0, limit))
    if cut < 120:
        cut = limit
    return raw[:cut].rstrip(" ,.;") + "..."


def section_text(markdown: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*$"
    match = re.search(pattern, markdown, flags=re.M)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+", markdown[start:], flags=re.M)
    end = start + next_match.start() if next_match else len(markdown)
    return markdown[start:end].strip()


def bullets(markdown: str, limit: int = 3) -> list[str]:
    out = []
    for line in markdown.splitlines():
        if line.startswith("- "):
            item = line[2:].strip()
            if item:
                out.append(item)
        if len(out) >= limit:
            break
    return out


def latex_table(headers: list[str], rows: Iterable[Iterable[object]], widths: list[float] | None = None, size: str = r"\small") -> str:
    if widths:
        total = sum(widths)
        scale = min(1.0, 0.92 / total) if total else 1.0
        spec = "@{}" + "".join([f">{{\\raggedright\\arraybackslash}}p{{{w * scale:.3f}\\linewidth}}" for w in widths]) + "@{}"
    else:
        spec = "l" * len(headers)
    lines = [
        r"\begin{center}",
        size,
        rf"\begin{{longtable}}{{{spec}}}",
        r"\toprule",
        " & ".join(tex(h) for h in headers) + r" \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        " & ".join(tex(h) for h in headers) + r" \\",
        r"\midrule",
        r"\endhead",
    ]
    for row in rows:
        lines.append(" & ".join(tex(cell) for cell in row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{longtable}", r"\end{center}"])
    return "\n".join(lines) + "\n"


def read_data() -> dict[str, object]:
    data = {
        "scores": pd.read_csv(PROCESSED_DIR / "prospect_model_scores_2026.csv").sort_values("board_rank"),
        "prospects": pd.read_csv(PROCESSED_DIR / "prospects_2026.csv"),
        "mock": pd.read_csv(PROCESSED_DIR / "fit_adjusted_mock_2026.csv"),
        "order": pd.read_csv(PROCESSED_DIR / "draft_order_2026.csv"),
        "team_context": pd.read_csv(PROCESSED_DIR / "team_context_2026.csv"),
        "comps": pd.read_csv(PROCESSED_DIR / "historical_comps_2026.csv"),
        "sources": pd.read_csv(PROCESSED_DIR / "sources_log.csv"),
        "importance": pd.read_csv(BASE_DIR / "models/feature_importance.csv"),
        "metrics": json.loads((BASE_DIR / "models/metrics.json").read_text(encoding="utf-8")),
        "coverage": json.loads((PROCESSED_DIR / "historical_coverage.json").read_text(encoding="utf-8")),
    }
    return data


def model_metric_table(metrics: dict) -> str:
    rows = []
    names = {
        "baseline_market_rank_ridge": "Ridge baseline, market rank only",
        "ridge_market_plus_traits": "Ridge, market plus traits",
        "gbm_market_plus_traits": "Gradient boosting, market plus traits",
        "rf_market_plus_traits": "Random forest, market plus traits",
    }
    for key, vals in metrics["regression"].items():
        rows.append([names.get(key, key), f"{vals['mae']:.3f}", f"{vals['rmse']:.3f}", f"{vals['spearman']:.3f}"])
    return latex_table(["Model", "MAE", "RMSE", "Spearman"], rows, widths=[0.46, 0.14, 0.14, 0.16])


def classifier_table(metrics: dict) -> str:
    labels = metrics["classification"]["labels"]
    matrix = metrics["classification"]["confusion_matrix"]
    rows = []
    for label, vals in zip(labels, matrix):
        rows.append([label] + vals)
    return latex_table(["Actual"] + labels, rows, widths=[0.16] + [0.14] * len(labels), size=r"\scriptsize")


def coverage_table(coverage: dict) -> str:
    rows = [[key, f"{100 * val:.1f}%"] for key, val in coverage["coverage"].items()]
    return latex_table(["Historical field", "Non-null coverage"], rows, widths=[0.55, 0.25])


def feature_importance_table(importance: pd.DataFrame) -> str:
    rows = [[row.feature, f"{row.importance_mae:.3f}"] for _, row in importance.head(15).iterrows()]
    return latex_table(["Feature", "Permutation MAE increase"], rows, widths=[0.46, 0.32])


def top_board_table(scores: pd.DataFrame) -> str:
    rows = []
    for _, row in scores.head(30).iterrows():
        rows.append(
            [
                int(row["board_rank"]),
                row["display_name"],
                row.get("position", ""),
                row.get("team_school", ""),
                fmt(row.get("age_at_draft"), 1),
                fmt(row.get("consensus_mean"), 1),
                f"{fmt(row.get('pred_value_p50'), 1)} [{fmt(row.get('pred_value_p10'), 1)}, {fmt(row.get('pred_value_p90'), 1)}]",
                row.get("tier", ""),
            ]
        )
    return latex_table(
        ["Rank", "Prospect", "Pos", "Team/School", "Age", "Consensus", "Model p50 [p10,p90]", "Tier"],
        rows,
        widths=[0.06, 0.18, 0.08, 0.16, 0.07, 0.10, 0.17, 0.19],
        size=r"\scriptsize",
    )


def mock_table(mock: pd.DataFrame) -> str:
    rows = []
    for _, row in mock.iterrows():
        rows.append([int(row.pick), row.owner, row.selection, int(row.board_rank), row.position, row.team_need, row.alternatives])
    return latex_table(
        ["Pick", "Owner", "Selection", "Board", "Pos", "Need fit", "Alternatives"],
        rows,
        widths=[0.04, 0.11, 0.15, 0.05, 0.06, 0.27, 0.20],
        size=r"\scriptsize",
    )


def source_summary_table(sources: pd.DataFrame) -> str:
    rows = []
    groups = [
        ("Official draft order", sources["source_id"].str.contains("draft_order", na=False)),
        ("Current public boards/mocks", sources["provided"].str.contains("mock|board|rank", case=False, na=False)),
        ("Combine and measurements", sources["provided"].str.contains("combine|measurement|athletic", case=False, na=False)),
        ("Historical modeling data", sources["raw_snapshot"].str.contains("historical", case=False, na=False)),
        ("Film clips and frame archive", sources["source_id"].str.contains("^film_", regex=True, na=False)),
        ("Failed/limited endpoints", sources["status"].str.contains("ERROR|403|timeout", case=False, na=False)),
    ]
    for label, mask in groups:
        rows.append([label, int(mask.sum())])
    return latex_table(["Source family", "Logged entries"], rows, widths=[0.55, 0.22])


def source_reference_list(sources: pd.DataFrame) -> str:
    items = []
    seen: set[str] = set()
    for _, row in sources.iterrows():
        source_id = str(row.get("source_id", "")).strip()
        source_url = str(row.get("url", "")).strip()
        provided = short(row.get("provided", ""), 150)
        status = str(row.get("status", "")).strip()
        if not source_url or source_url.lower() == "nan" or source_url in seen:
            continue
        seen.add(source_url)
        items.append((source_id, status, provided, source_url))
    lines = [
        r"\scriptsize",
        r"\begin{enumerate}[leftmargin=*, itemsep=2pt]",
    ]
    for source_id, status, provided, source_url in items:
        lines.append(rf"\item \texttt{{{tex(source_id)}}} [{tex(status)}]. {tex(provided)} {url(source_url)}")
    lines.extend([r"\end{enumerate}", r"\normalsize"])
    return "\n".join(lines) + "\n"


def film_note(norm_name: str) -> tuple[list[str], list[str], list[str]]:
    slug = NAME_TO_FILM_SLUG.get(norm_name)
    if not slug:
        return [], [], []
    path = FILM_NOTES_DIR / f"{slug}.md"
    if not path.exists():
        return [], [], []
    text = path.read_text(encoding="utf-8", errors="ignore")
    frame_bullets = bullets(section_text(text, "Frame-based observations (mine)"), limit=3)
    sourced_bullets = bullets(section_text(text, "Sourced scouting observations (human scouts, cited)"), limit=3)
    urls = sorted(set(re.findall(r"https?://[^\s)]+", text)))
    source_names = []
    for item in sourced_bullets:
        names = re.findall(r"Source, ([^,\\.]+)", item)
        if names:
            source_names.extend(names)
        else:
            source_names.extend(re.findall(r"^-?\\s*([^:]+):", item))
    source_names = [name.strip() for name in source_names if name.strip()]
    if not source_names and urls:
        source_names = [Path(u.split("?")[0]).parts[1] if len(Path(u.split("?")[0]).parts) > 1 else u for u in urls[:3]]
    return frame_bullets, sorted(set(source_names)), urls


def player_factor_notes(row: pd.Series, class_median: float) -> list[str]:
    notes = []
    consensus_delta = float(row["consensus_mean"]) - float(row["board_rank"])
    if consensus_delta > 2.0:
        notes.append(
            f"Codex is {fmt(consensus_delta, 1)} slots above public mean rank because the blended board rewarded model value and/or comp outcomes more than the market did."
        )
    elif consensus_delta < -2.0:
        notes.append(
            f"Codex is {fmt(abs(consensus_delta), 1)} slots below public mean rank; the penalty comes from model uncertainty, weaker statistical translation, or higher disagreement risk."
        )
    else:
        notes.append("Codex rank is close to the public market, so the board treats this as an evidence-aligned slot rather than a strong contrarian call.")
    pred = float(row["pred_value_p50"])
    if pred >= class_median + 3:
        notes.append(f"The model median ({fmt(pred, 1)} MPG-equivalent) is comfortably above the 2026 prospect-pool median.")
    elif pred <= class_median - 2:
        notes.append(f"The model median ({fmt(pred, 1)} MPG-equivalent) is below the top-board center, so the ranking leans more on consensus and role projection.")
    else:
        notes.append(f"The model median ({fmt(pred, 1)} MPG-equivalent) is near the top-board center, making uncertainty and role clarity decisive.")
    if pd.notna(row.get("consensus_std")) and float(row["consensus_std"]) >= 3:
        notes.append(f"Consensus spread is elevated ({fmt(row['consensus_std'], 1)} slots), which I treat as risk unless film/comps justify the upside.")
    if pd.notna(row.get("age_at_draft")):
        if float(row["age_at_draft"]) < 20:
            notes.append(f"Age at draft ({fmt(row['age_at_draft'], 1)}) is a positive developmental signal in this model family.")
        elif float(row["age_at_draft"]) >= 22:
            notes.append(f"Age at draft ({fmt(row['age_at_draft'], 1)}) reduces long-horizon upside relative to younger peers.")
    if pd.notna(row.get("wingspan_in")) and pd.notna(row.get("height_in")):
        diff = float(row["wingspan_in"]) - float(row["height_in"])
        if diff >= 3:
            notes.append(f"Wingspan differential is positive at roughly +{fmt(diff, 1)} inches.")
    return notes[:5]


def player_section(row: pd.Series, comps: pd.DataFrame, class_median: float) -> str:
    frame_obs, source_names, source_urls = film_note(row["norm_name"])
    comp_rows = comps[comps["norm_name"] == row["norm_name"]].sort_values("comp_rank")
    comp_table = latex_table(
        ["#", "Historical comp", "Year", "Pick", "Outcome MPG", "Tier"],
        [
            [int(c.comp_rank), c.comp_player, int(c.comp_draft_year), fmt(c.comp_pick, 0), fmt(c.comp_outcome_mpg, 1), c.comp_outcome_tier]
            for _, c in comp_rows.iterrows()
        ],
        widths=[0.06, 0.28, 0.10, 0.10, 0.16, 0.16],
        size=r"\scriptsize",
    )
    profile_rows = [
        ["Tier", row.get("tier", "")],
        ["Position / school", f"{row.get('position', '')}, {row.get('team_school', '')}"],
        ["Age at draft", fmt(row.get("age_at_draft"), 1)],
        ["Measurements", f"{fmt(row.get('height_in'), 1)} in, {fmt(row.get('weight_lbs'), 1)} lb, {fmt(row.get('wingspan_in'), 1)} in wingspan, {fmt(row.get('standing_reach_in'), 1)} in reach"],
        ["Production", f"{fmt(row.get('pts_pg'), 1)} PPG, {fmt(row.get('reb_pg'), 1)} RPG, {fmt(row.get('ast_pg'), 1)} APG, {fmt(row.get('stl_pg'), 1)} SPG, {fmt(row.get('blk_pg'), 1)} BPG"],
        ["Efficiency / impact", f"TS {fmt(row.get('ts_pct'), 3)}, usage {fmt(row.get('usg_pct'), 1)}, BPM {fmt(row.get('bpm'), 1)}"],
        ["Consensus", f"mean {fmt(row.get('consensus_mean'), 1)}, median {fmt(row.get('consensus_median'), 1)}, spread {fmt(row.get('consensus_std'), 1)}, range {fmt(row.get('consensus_min'), 0)}-{fmt(row.get('consensus_max'), 0)}"],
        ["Model value", f"p10 {fmt(row.get('pred_value_p10'), 1)}, p50 {fmt(row.get('pred_value_p50'), 1)}, p90 {fmt(row.get('pred_value_p90'), 1)} MPG-equivalent"],
        ["Tier probabilities", f"bust {pct(row.get('prob_bust'))}, rotation {pct(row.get('prob_rotation'))}, starter {pct(row.get('prob_starter'))}, star {pct(row.get('prob_star'))}"],
    ]
    lines = [
        rf"\subsection{{{int(row['board_rank'])}. {tex(row['display_name'])}}}",
        latex_table(["Field", "Value"], profile_rows, widths=[0.23, 0.68], size=r"\scriptsize"),
        r"\paragraph{Ranking rationale.}",
        r"\begin{itemize}[leftmargin=*]",
    ]
    for note in player_factor_notes(row, class_median):
        lines.append(rf"\item {tex(note)}")
    lines.extend([r"\end{itemize}", r"\paragraph{Nearest-neighbor comps.}", comp_table])
    if frame_obs:
        lines.extend([r"\paragraph{Frame-based film observations (mine).}", r"\begin{itemize}[leftmargin=*]"])
        for obs in frame_obs[:2]:
            lines.append(rf"\item {tex(short(obs, 360))}")
        lines.append(r"\end{itemize}")
    else:
        lines.append(r"\paragraph{Frame-based film observations (mine).} No completed frame note was available for this prospect; the board does not infer film traits from missing frames.")
    if source_names or source_urls:
        lines.append(r"\paragraph{Sourced scouting cross-check.}")
        if source_names:
            lines.append(tex("Human scouting sources consulted in the note file: " + ", ".join(source_names[:5]) + ". I use these directionally and avoid treating still frames as live-film evidence."))
        elif source_urls:
            lines.append(tex("Human scouting URLs are logged in the note file and references; I use them directionally."))
    return "\n".join(lines) + "\n"


def film_gallery(scores: pd.DataFrame) -> str:
    blocks = [
        r"\section{Film Study: Protocol and Representative Frames}",
        "The film component is intentionally conservative. Public clips were downloaded or imported through a local yt-dlp/ffmpeg archive, frames were sampled, and notes were written with two separate buckets: frame-based observations made from still images, and sourced human scouting observations. A still frame can support a claim about body position, release point, gather height, handle posture, or the presence of a contest. It cannot support a confident claim about burst, processing speed, screen navigation timing, defensive reaction time, or live advantage creation. Those claims remain sourced human-scouting context, not model evidence.",
        "",
        "For the top ten, I selected up to four illustrative frames per prospect. They are included below as evidence examples, not as a substitute for full-game film charting.",
    ]
    for _, row in scores.head(10).iterrows():
        slug = NAME_TO_FILM_SLUG.get(row["norm_name"])
        if not slug:
            continue
        frames = sorted(REPORT_FRAMES_DIR.glob(f"{slug}_pick*.jpg"))[:4]
        if not frames:
            continue
        blocks.append(rf"\subsection{{{tex(row['display_name'])}: selected still frames}}")
        blocks.append(r"\begin{figure}[H]\centering")
        for frame in frames:
            rel = "../" + frame.relative_to(BASE_DIR).as_posix()
            blocks.append(rf"\includegraphics[width=0.48\linewidth]{{{rel}}}")
        blocks.append(rf"\caption{{Selected frame samples for {tex(row['display_name'])}. These images support only the static observations discussed in the notes.}}")
        blocks.append(r"\end{figure}")
    return "\n".join(blocks) + "\n"


def honorable_mentions(scores: pd.DataFrame) -> str:
    rows = []
    for _, row in scores.iloc[30:40].iterrows():
        rows.append([int(row.board_rank), row.display_name, row.get("position", ""), row.get("team_school", ""), fmt(row.pred_value_p50, 1), fmt(row.consensus_mean, 1)])
    return latex_table(["Rank", "Prospect", "Pos", "Team/School", "Model p50", "Consensus"], rows, widths=[0.08, 0.24, 0.10, 0.24, 0.13, 0.13])


def write_tex() -> None:
    data = read_data()
    scores = data["scores"]
    comps = data["comps"]
    metrics = data["metrics"]
    coverage = data["coverage"]
    importance = data["importance"]
    mock = data["mock"]
    sources = data["sources"]
    class_median = float(scores["pred_value_p50"].median())
    top30 = scores.head(30)
    top3 = ", ".join(top30.head(3)["display_name"].tolist())
    report_parts = [
        r"""\documentclass[11pt]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage{fontspec}
\IfFontExistsTF{Arial}{\setmainfont{Arial}}{\setmainfont{Latin Modern Roman}}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{xurl}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{caption}
\usepackage{amsmath}
\hypersetup{colorlinks=true, linkcolor=blue!45!black, urlcolor=blue!45!black, citecolor=blue!45!black}
\definecolor{codexblue}{HTML}{17324D}
\definecolor{codexgold}{HTML}{B9861E}
\definecolor{lightgray}{HTML}{F2F4F8}
\pagestyle{fancy}
\fancyhf{}
\lhead{2026 NBA Draft Big Board}
\rhead{Codex Research Department}
\cfoot{\thepage}
\titleformat{\section}{\Large\bfseries\color{codexblue}}{\thesection}{0.7em}{}
\titleformat{\subsection}{\large\bfseries\color{codexblue}}{\thesubsection}{0.7em}{}
\setlist[itemize]{itemsep=2pt, topsep=3pt}
\setlength{\LTpre}{4pt}
\setlength{\LTpost}{8pt}
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.08}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\emergencystretch=3em
\sloppy
\begin{document}
\begin{titlepage}
\centering
\vspace*{0.6in}
{\Huge\bfseries 2026 NBA Draft Big Board\par}
\vspace{0.18in}
{\Large A LaTeX Research Report from the Codex Scouting Department\par}
\vspace{0.18in}
{\large Current as of 2026-06-10 IST\par}
\vspace{0.5in}
\includegraphics[width=0.94\linewidth]{../figures/shareable_mock_draft_16x9.png}
\vfill
{\large Data, modeling, film-frame protocol, historical comps, and fit-adjusted mock draft\par}
\end{titlepage}
\tableofcontents
\newpage
""",
        r"\section{Abstract}",
        tex(
            f"This report constructs a first-round 2026 NBA Draft big board from live public data collected on 2026-06-10. The final board is led by {top3}. The project combines official first-round pick ownership, nine public ranking/mock signals, 2026 combine measurements where recoverable, season production, sourced scouting notes, still-frame film study, a historical draft dataset covering 2000-2021, leave-one-draft-class-out machine learning, bootstrapped uncertainty bands, nearest-neighbor historical comparisons, and team-fit context. The key modeling result is sober rather than flashy: market rank remains the strongest single predictor, and trait models improve the baseline only modestly. Therefore the final board uses a conservative blend of consensus rank, model median value, uncertainty, comps, and film/scouting context."
        ),
        r"\section{Introduction and Problem Statement}",
        tex(
            "The assignment is not merely to list the first thirty prospects. The hard problem is evidence integration: a draft board should separate fetched facts from model inference, and it should distinguish a talent-first ranking from a fit-adjusted mock draft. The output therefore has two ranked artifacts. The big board ranks prospects by expected NBA value. The mock draft maps those prospects onto the actual first-round pick owners and broad roster needs."
        ),
        tex(
            "This report is written like a Kaggle solution because the model is only useful if it is reproducible and benchmarked. It is written like an academic paper because the validity threats matter as much as the result. The 2026 class includes NCAA freshmen, older college producers, international prospects, and players with uneven samples. That mixture creates missing-data problems and translation-risk problems that should be visible to the reader."
        ),
        r"\section{Related Work and Prior Assumptions}",
        tex(
            "Public draft models have repeatedly found that the market is difficult to beat. Draft slot and consensus rank capture a large amount of dispersed information: live scouting, medical intel, workouts, team interviews, and private measurements. Trait models can still help, especially when they identify statistical profiles that the market underprices, but a model that ignores consensus is likely to overfit. This project therefore treats market rank as the baseline to beat and as an input feature, not as an enemy."
        ),
        tex(
            "The historical sources include public GitHub draft-model datasets, FiveThirtyEight historical projection data, draft-history/value tables, and combine measurement collections. These sources are imperfect but provide enough scale for a leave-one-draft-class-out validation design. The board also uses public scouting boards from Tankathon, Rookie Scale, CBS, Bleacher Report, Yahoo/KOC, The Ringer, and NBA Draft Room when the HTML snapshot exposed usable data."
        ),
        r"\section{Data Collection and Cleaning}",
        tex(
            "All fetched live data and raw snapshots are logged under data/raw and sources.md. Processed tables live under data/processed. The draft order comes from NBA.com and is used only for the fit-adjusted mock draft; it does not change the pure big board. Prospect statistics primarily come from Tankathon and CBS snapshots. Combine measurements use the NBADraft.net Wayback snapshots plus NBA.com, On3, Yahoo, and NBA Draft Room context where accessible. Several official NBA stats endpoints timed out and Basketball Reference bulk pages returned access blocks; those failures are carried into the limitations rather than hidden."
        ),
        source_summary_table(sources),
        r"\subsection{Historical Dataset}",
        tex(
            f"The historical table contains {coverage['rows']} player-seasons/records from draft classes {coverage['draft_year_min']} through {coverage['draft_year_max']}, including {coverage['first_round_rows']} first-round rows. Rows from 2000-2008 primarily come from the woodfin8 Draft Machine merged data. Rows from 2009-2021 use the JasonG NBA Draft Model data because it has richer pre-draft features and an NBA MPG proxy outcome. Career win shares and VORP are retained where present, but coverage is incomplete enough that the primary supervised target is NBA MPG-equivalent value."
        ),
        coverage_table(coverage),
        r"\subsection{Feature Families}",
        tex(
            "The modeling matrix is intentionally broad but not exotic. Numeric features are: "
            + ", ".join(FEATURES_NUMERIC)
            + ". The categorical feature is position_group. For the comps engine, I used a narrower standardized vector: "
            + ", ".join(COMP_FEATURES)
            + ". Missing numeric values are median-imputed inside each training fold, and position_group is most-frequent imputed then one-hot encoded. This matters because several 2026 prospects have incomplete official combine or shooting fields."
        ),
        r"\subsection{Outcome Definitions}",
        tex(
            "The regression target is outcome_value, defined as NBA MPG-equivalent value in the merged historical dataset. The tier classifier uses five ordered labels: bust, bench, rotation, starter, and star. The tier labels are not the ranking engine; they are probability-flavored context used to communicate floor and ceiling. The report does not claim that an MPG-equivalent model can fully summarize impact, defense, or playoff scalability."
        ),
        r"\section{Methodology}",
        r"\subsection{Consensus Aggregation}",
        tex(
            "Player names are normalized across public boards. For every prospect, the pipeline computes source count, mean rank, median rank, minimum rank, maximum rank, and rank standard deviation. The standard deviation is treated as a risk signal: disagreement can indicate role uncertainty, medical uncertainty, sample-size uncertainty, or genuine upside/downside disagreement."
        ),
        r"\subsection{Machine Learning Models}",
        tex(
            "The validation design is leave-one-draft-class-out. For each held-out draft year, every model is trained on all other years and evaluated on the held-out class. This avoids random-row leakage across eras and draft cohorts. The baseline is a ridge regression using only market_rank. The richer ridge model adds age, measurements, box-score rates, efficiency, usage, BPM components, shooting proxies, and position group. Nonlinear models are gradient boosting regression and random forest regression. A separate gradient boosting classifier predicts outcome tiers."
        ),
        tex(
            "The specific model family choices are modest by design. Ridge provides interpretability and a strong regularized baseline. Gradient boosting captures nonlinear interactions such as age-by-production or size-by-role without requiring deep learning scale. Random forest is used as a robustness check. The bootstrap uncertainty band samples historical draft years with replacement and fits eighty shallow gradient boosting models; the reported p10/p50/p90 for 2026 prospects are percentiles of those bootstrap predictions."
        ),
        r"\subsection{Final Board Formula}",
        tex(
            "Because the learned models only modestly beat the market baseline, the final board is a blended ranking rather than a pure model sort. The board score is:"
        ),
        r"\[ S = 0.68(-z_{\mathrm{consensus}}) + 0.27 z_{\mathrm{model}} - 0.05 z_{\mathrm{spread}} \]",
        tex(
            "where lower consensus rank is better, model is predicted p50 MPG-equivalent value, and spread is public-rank standard deviation. This weighting anchors the board to the strongest signal while still allowing model value and disagreement risk to move prospects within tiers."
        ),
        r"\subsection{Historical Comps Engine}",
        tex(
            "The comps engine standardizes age, height, weight, wingspan, per-40 production, efficiency, usage, and BPM, then fits a five-nearest-neighbor model with Euclidean distance. Every comp cohort is empirical: the low, median, and high outcomes are the actual NBA MPG-equivalent outcomes of those historical neighbors. A comp is not claimed as a stylistic clone. It is a statistical-profile neighbor, and the report flags this distinction throughout."
        ),
        r"\section{Model Results}",
        model_metric_table(metrics),
        tex(
            f"The market-only baseline posted MAE {metrics['regression']['baseline_market_rank_ridge']['mae']:.3f}, RMSE {metrics['regression']['baseline_market_rank_ridge']['rmse']:.3f}, and Spearman {metrics['regression']['baseline_market_rank_ridge']['spearman']:.3f}. The random forest posted the best MAE at {metrics['regression']['rf_market_plus_traits']['mae']:.3f}; ridge with traits posted the best rank correlation at {metrics['regression']['ridge_market_plus_traits']['spearman']:.3f}. This is a narrow win, not a model landslide. The main conclusion is that model output is useful as a board modifier, but the public market remains the dominant prior."
        ),
        r"\subsection{Classifier}",
        tex(f"The tier classifier accuracy is {metrics['classification']['accuracy']:.3f}. Its confusion matrix shows the expected draft-model problem: stars and busts are hard to separate from adjacent outcomes, and many true starters/rotation players collapse into the middle classes."),
        classifier_table(metrics),
        r"\subsection{Feature Importance}",
        tex(
            "Permutation importance confirms the central lesson. Market rank dominates. Secondary signals with meaningful but much smaller importance include assist production, age, turnovers, block/steal production, scoring volume, and shooting indicators. This aligns with the final-board design: a smart board can move from consensus, but it should not pretend that a small public feature set fully replaces the market."
        ),
        feature_importance_table(importance),
        r"\begin{figure}[H]\centering\includegraphics[width=0.92\linewidth]{../figures/feature_importance.png}\caption{Permutation importance for the final gradient boosting model.}\end{figure}",
        r"\begin{figure}[H]\centering\includegraphics[width=0.82\linewidth]{../figures/cv_predicted_vs_actual.png}\caption{Leave-one-draft-class-out predictions versus actual NBA MPG-equivalent outcome.}\end{figure}",
        r"\section{Board-Level Figures}",
        r"\begin{figure}[H]\centering\includegraphics[width=0.95\linewidth]{../figures/consensus_spread_top30.png}\caption{Public-board disagreement among top prospects. Spread is used as a risk feature.}\end{figure}",
        r"\begin{figure}[H]\centering\includegraphics[width=0.88\linewidth]{../figures/model_vs_consensus.png}\caption{Model value versus consensus rank; color encodes consensus spread.}\end{figure}",
        r"\begin{figure}[H]\centering\includegraphics[width=0.92\linewidth]{../figures/comp_cohort_medians.png}\caption{Median NBA MPG outcome of nearest-neighbor historical comp cohorts.}\end{figure}",
        film_gallery(scores),
        r"\section{The 2026 Talent-First Big Board}",
        tex("The table below is the pure board. It is not a mock draft. The model value is an NBA MPG-equivalent median with a bootstrapped p10-p90 band, not a guaranteed minute projection."),
        top_board_table(scores),
    ]
    for _, row in top30.iterrows():
        report_parts.append(player_section(row, comps, class_median))
    report_parts.extend(
        [
            r"\section{Honorable Mentions}",
            honorable_mentions(scores),
            r"\section{Fit-Adjusted Mock Draft}",
            tex(
                "This mock draft is a separate artifact from the big board. It starts from the actual pick owners, then chooses among high-ranked available prospects using a broad fit heuristic. Fit can break ties, but it should not justify passing on a materially better talent tier."
            ),
            mock_table(mock),
            r"\section{Discussion}",
            tex(
                "The top of the class is strong but not perfectly separated. AJ Dybantsa, Darryn Peterson, and Cameron Boozer are the safest star-bet tier because consensus, model value, age, and comps all point in the same direction. Keaton Wagler is the highest meaningful model-over-market riser: his statistical profile and bootstrapped model value push him into the same quantitative band as the consensus top three. Caleb Wilson and Kingston Flemings round out the next tier because the model likes their production/age context while the consensus still leaves room for interpretation."
            ),
            tex(
                "The largest disagreements are more instructive than the exact order. Prospects with older age, thin shooting samples, incomplete combine data, or high public spread are intentionally pushed down unless the model and comps provide a strong counterweight. Conversely, several guards with strong creation indicators rise because assist production and market rank show up as meaningful predictors in historical validation."
            ),
            r"\section{Limitations and Threats to Validity}",
            r"\begin{itemize}[leftmargin=*]",
            r"\item " + tex("Official NBA stats combine endpoints timed out from this environment; hand size, body fat, some height-with-shoes fields, and official drill completeness are therefore incomplete."),
            r"\item " + tex("Basketball Reference pages were blocked for bulk direct fetches, so the primary historical target is NBA MPG-equivalent rather than a fully refreshed VORP or win-shares target."),
            r"\item " + tex("International and alternative-pathway statistics are not perfectly comparable with NCAA BPM, usage, and per-40 rates. Median imputation avoids crashes but cannot create missing information."),
            r"\item " + tex("The film study is still-frame sampled. It supports static posture/mechanics observations only and should not be read as full live scouting."),
            r"\item " + tex("Team context uses broad roster/timeline inference. It is not a cap-sheet optimizer and does not model private workouts, medicals, or trade conversations."),
            r"\item " + tex("The public consensus is itself partly endogenous with team intel and scouting reputation. The model can validate or challenge the market, but it cannot fully disentangle why the market ranked a player where it did."),
            r"\end{itemize}",
            r"\section{Reproducibility}",
            tex("The reproducible pipeline lives in src/. To rerun the project from the repository root, execute the following scripts in order. Network-dependent fetch steps may change if sites modify markup or access rules."),
            """\\begin{verbatim}
python3 src/fetch_live_data.py
python3 src/fetch_historical_data.py
python3 src/fetch_additional_sources.py
python3 src/build_live_datasets.py
python3 src/build_historical_dataset.py
python3 src/run_modeling_and_comps.py
python3 src/import_film_archive.py
python3 src/generate_report.py
python3 src/generate_latex_report.py
\\end{verbatim}""",
            r"\section{References}",
            source_reference_list(sources),
            r"\section{Appendix: Data Dictionary}",
            latex_table(
                ["Artifact", "Purpose"],
                [
                    ["data/processed/prospects_2026.csv", "Cleaned 2026 prospect table with consensus, measurements, and production."],
                    ["data/processed/prospect_model_scores_2026.csv", "Final 2026 model predictions, probabilities, board score, tiers, and comps summary."],
                    ["data/processed/historical.csv", "Historical pre-draft features and NBA MPG-equivalent outcomes for modeling."],
                    ["data/processed/historical_comps_2026.csv", "Five nearest historical statistical comps for every 2026 prospect."],
                    ["models/metrics.json", "Leave-one-draft-class-out regression metrics and tier-classifier matrix."],
                    ["models/feature_importance.csv", "Permutation importance from the final gradient boosting model."],
                    ["film/notes/", "Per-prospect film notes separating frame observations from sourced human scouting."],
                    ["figures/", "Generated charts and shareable graphics used in the report."],
                ],
                widths=[0.36, 0.55],
            ),
            r"\end{document}",
        ]
    )
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    TEX_PATH.write_text("\n\n".join(report_parts), encoding="utf-8")


def compile_pdf() -> None:
    if not shutil.which("tectonic"):
        raise RuntimeError("tectonic was not found; cannot compile LaTeX report.")
    subprocess.run(["tectonic", "--outdir", str(REPORT_DIR), str(TEX_PATH)], cwd=BASE_DIR, check=True)
    generated = REPORT_DIR / "report.pdf"
    if generated.exists():
        shutil.copyfile(generated, PDF_PATH)
        shutil.copyfile(generated, LATEX_PDF_PATH)
        generated.unlink()


def update_progress() -> None:
    progress = BASE_DIR / "progress.md"
    text = progress.read_text(encoding="utf-8") if progress.exists() else "# Progress\n\n"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M IST")
    text = re.sub(r"Last updated: .*", f"Last updated: {stamp}", text, count=1)
    if "LaTeX research report" not in text:
        text = text.replace(
            "| Share graphics | Complete | 16:9 full-round PNG, three vertical story PNGs, and a three-page story PDF deck rendered in `figures/`. |\n",
            "| Share graphics | Complete | 16:9 full-round PNG, three vertical story PNGs, and a three-page story PDF deck rendered in `figures/`. |\n"
            "| LaTeX research report | Complete | `report/report.tex`, `report/final_report.pdf`, and `report/final_report_latex.pdf` generated with a full methods/modeling/comps/film writeup. |\n",
        )
    progress.write_text(text, encoding="utf-8")


def main() -> None:
    write_tex()
    compile_pdf()
    update_progress()
    print(f"wrote {TEX_PATH}")
    print(f"wrote {PDF_PATH}")
    print(f"wrote {LATEX_PDF_PATH}")


if __name__ == "__main__":
    main()
