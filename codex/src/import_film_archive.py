from __future__ import annotations

import re
import shutil
from pathlib import Path

import pandas as pd

from common import BASE_DIR, append_source_log, normalize_name, slugify


SOURCE_FILM_DIR = BASE_DIR.parent / "nba_draft_claude" / "film"
DEST_FILM_DIR = BASE_DIR / "film"

REPORT_PICK_FRAMES = {
    "wagler": ["frame_0103.jpg", "frame_0206.jpg", "frame_0308.jpg", "frame_0411.jpg"],
    "wilson": ["frame_0145.jpg", "frame_0290.jpg", "frame_0434.jpg", "frame_0579.jpg"],
    "burries": ["frame_0141.jpg", "frame_0281.jpg", "frame_0422.jpg", "frame_0562.jpg"],
    "philon": ["frame_0058.jpg", "frame_0115.jpg", "frame_0172.jpg", "frame_0229.jpg"],
}

SLUG_TO_NAME = {
    "acuff": "Darius Acuff Jr.",
    "ament": "Nate Ament",
    "boozer": "Cameron Boozer",
    "brown_mikel": "Mikel Brown Jr.",
    "burries": "Brayden Burries",
    "carr": "Cameron Carr",
    "dybantsa": "AJ Dybantsa",
    "flemings": "Kingston Flemings",
    "graves": "Allen Graves",
    "johnson_morez": "Morez Johnson Jr.",
    "lendeborg": "Yaxel Lendeborg",
    "lopez": "Karim Lopez",
    "mara": "Aday Mara",
    "okorie": "Ebuka Okorie",
    "peterson": "Darryn Peterson",
    "philon": "Labaron Philon Jr.",
    "steinbach": "Hannes Steinbach",
    "stirtz": "Bennett Stirtz",
    "wagler": "Keaton Wagler",
    "wilson": "Caleb Wilson",
}

FRAME_OBS = {
    "wagler": [
        "The selected wide broadcast frames show Wagler functioning around the arc rather than as an interior finisher: one half-court frame has him spaced above the break, another near the strong-side wing/corner area, and another in early offense. These frames support role context and spacing discipline more than shot-mechanics detail.",
        "Because the frames are distant, I do not make claims about release speed, handle tightness, or defensive processing. The useful still-frame evidence is mostly alignment, frame/build in game context, and how often he is used as a perimeter connector.",
    ],
    "wilson": [
        "The selected frames show Wilson used from several frontcourt alignments: operating near the slot, catching or screening around the elbows, and flowing into actions from the wing. His body frame reads long and wiry in ACC broadcast context, with clear vertical size but room to add strength.",
        "The frames support broad usage variety but not burst or decision speed. Any claim about advantage creation, defensive timing, or touch remains sourced-scouting territory rather than my still-frame observation.",
    ],
    "burries": [
        "The selected frames show Burries in guard/wing floor positions: spacing in the corner/slot, advancing in early offense, and defending within a compact shell. He appears sturdy for a guard prospect in the broadcast angles, with a low-enough stance in half-court possessions.",
        "The stills do not support claims about jumper repeatability or first-step pop. They are best used as context for role, body type, and floor geography.",
    ],
    "philon": [
        "The selected frames show Philon primarily initiating or advancing the ball, including transition and early-clock half-court contexts. His posture in the ballhandling frames is low and forward-leaning, consistent with a point-guard usage profile.",
        "The still-frame archive cannot establish live passing windows or pace manipulation. Those claims are left to sourced human scouting and the statistical profile.",
    ],
}


def copy_tree_contents(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        return
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def clip_youtube_id(path: Path, slug: str) -> str:
    stem = path.stem
    prefix = f"{slug}_"
    if stem.startswith(prefix):
        return stem[len(prefix) :]
    parts = stem.split("_", 1)
    return parts[1] if len(parts) > 1 else ""


def write_missing_note(slug: str, scouting: pd.DataFrame) -> None:
    path = DEST_FILM_DIR / "notes" / f"{slug}.md"
    if path.exists():
        return
    name = SLUG_TO_NAME.get(slug, slug.replace("_", " ").title())
    norm = normalize_name(name)
    snippets = scouting[scouting["norm_name"] == norm].head(3)
    lines = [f"# {name}\n", "\n", "## Frame-based observations (mine)\n", "\n"]
    for obs in FRAME_OBS.get(slug, ["Frame archive present, but Codex did not complete a detailed still-frame audit for this prospect."]):
        lines.append(f"- {obs}\n")
    lines.extend(["\n", "## Sourced scouting observations (human scouts, cited)\n", "\n"])
    if snippets.empty:
        lines.append("- No prospect-specific sourced scouting snippet was extractable from the fetched scouting tables; see consensus ranks and dossiers for data-backed context.\n")
    else:
        for _, row in snippets.iterrows():
            text = str(row.get("scouting_text", "")).strip()
            comp = str(row.get("pro_comp", "")).strip()
            source = row.get("source", "fetched scouting source")
            if text and text.lower() != "nan":
                lines.append(f"- {source}: {text}\n")
            if comp and comp.lower() != "nan":
                lines.append(f"- {source} listed pro comp: {comp}.\n")
    lines.extend(["\n", "## Report picks (frames/_report_picks/)\n", "\n"])
    for i, frame in enumerate(REPORT_PICK_FRAMES.get(slug, []), start=1):
        lines.append(f"- {slug}_pick{i}.jpg copied from `{slug}/{frame}`.\n")
    path.write_text("".join(lines), encoding="utf-8")


def create_report_picks() -> None:
    picks_dir = DEST_FILM_DIR / "frames" / "_report_picks"
    picks_dir.mkdir(parents=True, exist_ok=True)
    for slug, frames in REPORT_PICK_FRAMES.items():
        for idx, frame in enumerate(frames, start=1):
            src = DEST_FILM_DIR / "frames" / slug / frame
            if src.exists():
                shutil.copy2(src, picks_dir / f"{slug}_pick{idx}.jpg")


def build_manifest() -> pd.DataFrame:
    rows = []
    for slug, name in sorted(SLUG_TO_NAME.items()):
        frame_dir = DEST_FILM_DIR / "frames" / slug
        clips = sorted((DEST_FILM_DIR / "clips").glob(f"{slug}_*"))
        rows.append(
            {
                "slug": slug,
                "prospect": name,
                "clip_files": ";".join(str(p.relative_to(BASE_DIR)) for p in clips),
                "youtube_urls": ";".join(
                    f"https://www.youtube.com/watch?v={clip_youtube_id(p, slug)}"
                    for p in clips
                    if clip_youtube_id(p, slug)
                ),
                "frame_count": len(list(frame_dir.glob("*.jpg"))) if frame_dir.exists() else 0,
                "note_file": str((DEST_FILM_DIR / "notes" / f"{slug}.md").relative_to(BASE_DIR)),
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(DEST_FILM_DIR / "film_manifest.csv", index=False)
    return manifest


def log_video_sources(manifest: pd.DataFrame) -> None:
    for _, row in manifest.iterrows():
        for url in str(row["youtube_urls"]).split(";"):
            if not url:
                continue
            append_source_log(
                f"film_{row['slug']}_{url.rsplit('=', 1)[-1]}",
                url,
                Path(str(row["clip_files"]).split(";")[0]) if row["clip_files"] else None,
                f"Public video clip used for {row['prospect']} frame archive; imported from local yt-dlp/ffmpeg film archive.",
                "LOCAL ARCHIVE IMPORT",
                "Clip/frame archive imported from sibling project directory in same workspace; notes preserve frame-based vs sourced scouting distinction.",
            )


def main() -> None:
    if not SOURCE_FILM_DIR.exists():
        raise SystemExit(f"source film archive missing: {SOURCE_FILM_DIR}")
    copy_tree_contents(SOURCE_FILM_DIR / "clips", DEST_FILM_DIR / "clips")
    copy_tree_contents(SOURCE_FILM_DIR / "frames", DEST_FILM_DIR / "frames")
    copy_tree_contents(SOURCE_FILM_DIR / "notes", DEST_FILM_DIR / "notes")
    create_report_picks()
    scouting_path = BASE_DIR / "data/processed/sourced_scouting_notes.csv"
    scouting = pd.read_csv(scouting_path) if scouting_path.exists() else pd.DataFrame()
    for slug in REPORT_PICK_FRAMES:
        write_missing_note(slug, scouting)
    manifest = build_manifest()
    log_video_sources(manifest)
    print(manifest[["slug", "prospect", "frame_count", "youtube_urls"]].to_string(index=False))


if __name__ == "__main__":
    main()
