"""Render the split-screen film-analysis launch video
(release/images/tweet1_fable_film_study.mp4).

Left side plays the real clip segments Fable cited in
film/notes/boozer.md inside a framed slot; right side shows its actual
notes in a dark UI panel. Frame numbers map to clip seconds (stills
were cut at 1 fps). Intro and outro cards bookend the piece, every part
fades, audio is dropped (reel music is copyrighted). Needs ffmpeg, PIL.
"""
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[3]
CLIP = REPO / "claude/code/film/clips/boozer_KwEliYUNeUg.webm"
OUT = REPO / "release/images/tweet1_fable_film_study.mp4"
TMP = Path("/tmp/fable_film_video2")
TMP.mkdir(exist_ok=True)

BG = (8, 10, 13)
PANEL = (15, 19, 24)
CARD = (20, 25, 31)
FG = (240, 242, 244)
MUTED = (122, 132, 142)
DIM = (70, 78, 86)
CYAN = (94, 200, 229)
GOLD = (235, 188, 80)


def font(size, weight="regular"):
    paths = {
        "regular": "/System/Library/Fonts/Supplemental/Arial.ttf",
        "bold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "black": "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "italic": "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
    }
    return ImageFont.truetype(paths[weight], size)


def spaced(s):
    return " ".join(s)


def wrap_text(d, text, xy, f, fill, width, leading=1.42):
    x, y = xy
    for para in text.split("\n"):
        for line in textwrap.wrap(para, width=width) or [""]:
            d.text((x, y), line, font=f, fill=fill)
            y += int(f.size * leading)
        y += int(f.size * 0.35)
    return y


SEGMENTS = [
    {
        "start": 283, "dur": 11,
        "session": "FILM SESSION 01",
        "title": "Post seal into rim finish",
        "game": "vs Texas Tech, Madison Square Garden",
        "body": ("Wide, low post seal on the right block, defender pinned "
                 "on his hip (frame 0289). One frame later he is airborne "
                 "at the rim, ball carried high and away from the swipe "
                 "(frame 0290)."),
        "limit": "Stills support the seal and ball position. They cannot show how quickly he elevated.",
    },
    {
        "start": 556, "dur": 11,
        "session": "FILM SESSION 02",
        "title": "Full extension in traffic",
        "game": "vs Louisville",
        "body": ("In a crowded paint he rises off two feet to full arm "
                 "extension above the rim line, torso vertical rather "
                 "than drifting (frames 0562-0563)."),
        "limit": "Body control and extension are visible. Takeoff speed is not claimable from stills.",
    },
    {
        "start": 604, "dur": 11,
        "session": "FILM SESSION 03",
        "title": "Faceup iso posture",
        "game": "at Virginia Tech",
        "body": ("Bent-knee faceup stance, ball shielded on the outside "
                 "hip rather than in front of the body (frame 0610). By "
                 "frame 0612 he has worked middle with the defender "
                 "still attached."),
        "limit": "A deliberate, shielded approach. Separation quickness is invisible at 1 fps.",
    },
]

W, H = 1280, 720

# ---------- intro card ----------
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 3], fill=CYAN)
d.text((W // 2, 132), spaced("FULLY AUTONOMOUS RUN"), font=font(19, "bold"),
       fill=GOLD, anchor="mm")
d.text((W // 2, 212), "AN AI SCOUT", font=font(74, "black"), fill=FG, anchor="mm")
d.text((W // 2, 292), "WATCHES FILM", font=font(74, "black"), fill=CYAN, anchor="mm")
d.line([W // 2 - 170, 352, W // 2 + 170, 352], fill=DIM, width=1)
d.text((W // 2, 396), "Claude Fable 5 built a complete 2026 NBA Draft big board on its own",
       font=font(25), fill=FG, anchor="mm")
d.text((W // 2, 438), "zero hints, live data, real game footage",
       font=font(22), fill=MUTED, anchor="mm")
d.text((W // 2, 516), "685 stills at 1 fps   |   Cameron Boozer, PF, Duke",
       font=font(24, "bold"), fill=CYAN, anchor="mm")
d.text((W // 2, 612), "Stills cannot show speed, burst, or timing. Its notes never pretend otherwise.",
       font=font(19, "italic"), fill=GOLD, anchor="mm")
d.rectangle([0, H - 3, W, H], fill=CYAN)
img.save(TMP / "intro.png")

# ---------- outro card ----------
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 3], fill=CYAN)
d.text((W // 2, 150), spaced("THE FULL RELEASE"), font=font(19, "bold"),
       fill=GOLD, anchor="mm")
d.text((W // 2, 232), "EVERYTHING IS PUBLIC", font=font(62, "black"),
       fill=FG, anchor="mm")
d.line([W // 2 - 170, 292, W // 2 + 170, 292], fill=DIM, width=1)
d.text((W // 2, 344), "Two detailed research papers, 32 and 59 pages",
       font=font(25), fill=FG, anchor="mm")
d.text((W // 2, 388), "both big boards, every dossier, the models, the film notes, all the code",
       font=font(22), fill=MUTED, anchor="mm")
d.text((W // 2, 480), "github.com/arcAman07/nba-draft-2026-ai-big-board",
       font=font(27, "bold"), fill=CYAN, anchor="mm")
d.text((W // 2, 588), "Claude Fable 5 vs Codex GPT 5.5, same prompt, zero hints. The draft decides.",
       font=font(20, "italic"), fill=GOLD, anchor="mm")
d.rectangle([0, H - 3, W, H], fill=CYAN)
img.save(TMP / "outro.png")

# ---------- left backgrounds and right panels ----------
SLOT_X, SLOT_Y, SLOT_W, SLOT_H = 20, 146, 760, 428
for i, seg in enumerate(SEGMENTS):
    # left background 800x720 with framed slot and labels
    img = Image.new("RGB", (800, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 800, 3], fill=CYAN)
    d.text((SLOT_X + 2, 84), spaced(seg["session"]), font=font(17, "bold"), fill=GOLD)
    d.text((SLOT_X + 2, 114), "Cameron Boozer, PF, Duke", font=font(20, "bold"), fill=FG)
    d.rectangle([SLOT_X - 2, SLOT_Y - 2, SLOT_X + SLOT_W + 2, SLOT_Y + SLOT_H + 2],
                outline=(45, 55, 64), width=2)
    d.text((SLOT_X + 2, SLOT_Y + SLOT_H + 18), spaced("SOURCE"),
           font=font(14, "bold"), fill=DIM)
    d.text((SLOT_X + 92, SLOT_Y + SLOT_H + 16), "public season reel, studied as 1 fps stills",
           font=font(17), fill=MUTED)
    d.rectangle([0, H - 3, 800, H], fill=CYAN)
    img.save(TMP / f"left{i}.png")

    # right panel 480x720
    img = Image.new("RGB", (480, H), PANEL)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 480, 3], fill=CYAN)
    d.rectangle([0, 3, 480, 92], fill=CARD)
    d.rectangle([0, 3, 5, 92], fill=CYAN)
    d.text((28, 26), "FABLE FILM NOTES", font=font(25, "black"), fill=FG)
    d.text((28, 62), "written from stills only, verbatim from the repo",
           font=font(16), fill=MUTED)
    for j in range(3):
        cx = 36 + j * 30
        color = GOLD if j == i else DIM
        d.ellipse([cx - 6, 126, cx + 6, 138], fill=color)
    d.text((28, 166), seg["title"], font=font(28, "bold"), fill=FG)
    bbox = d.textbbox((0, 0), seg["game"], font=font(17))
    d.rounded_rectangle([28, 210, 28 + bbox[2] + 24, 242], radius=6,
                        outline=(58, 71, 84), width=1)
    d.text((40, 218), seg["game"], font=font(17), fill=MUTED)
    y = wrap_text(d, seg["body"], (28, 276), font(21), FG, width=37)
    d.line([28, y + 8, 452, y + 8], fill=(45, 55, 64), width=1)
    d.text((28, y + 26), spaced("WHAT STILLS CANNOT SHOW"), font=font(13, "bold"), fill=GOLD)
    wrap_text(d, seg["limit"], (28, y + 52), font(19, "italic"), GOLD, width=42)
    d.rectangle([0, 654, 480, H], fill=CARD)
    d.text((28, 672), "full notes, frames, and paper in the repo",
           font=font(16), fill=MUTED)
    d.rectangle([0, H - 3, 480, H], fill=CYAN)
    img.save(TMP / f"panel{i}.png")


def render_card(name, png, dur):
    out = TMP / f"part_{name}.mp4"
    fade = f"fade=t=in:st=0:d=0.5,fade=t=out:st={dur - 0.5}:d=0.5"
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", png,
                    "-vf", f"{fade},format=yuv420p", "-r", "30",
                    "-c:v", "libx264", "-an", out], check=True, capture_output=True)
    return out


parts = [render_card("intro", TMP / "intro.png", 3.5)]

for i, seg in enumerate(SEGMENTS):
    out = TMP / f"part{i}.mp4"
    dur = seg["dur"]
    fc = (f"[0:v]scale={SLOT_W}:{SLOT_H}[clip];"
          f"[1:v][clip]overlay={SLOT_X}:{SLOT_Y}[left];"
          f"[left][2:v]hstack=inputs=2,"
          f"fade=t=in:st=0:d=0.5,fade=t=out:st={dur - 0.5}:d=0.5,"
          f"format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y",
                    "-ss", str(seg["start"]), "-t", str(dur), "-i", CLIP,
                    "-loop", "1", "-t", str(dur), "-i", TMP / f"left{i}.png",
                    "-loop", "1", "-t", str(dur), "-i", TMP / f"panel{i}.png",
                    "-filter_complex", fc, "-map", "[v]", "-r", "30",
                    "-c:v", "libx264", "-an", out], check=True, capture_output=True)
    parts.append(out)

parts.append(render_card("outro", TMP / "outro.png", 4))

concat = TMP / "list.txt"
concat.write_text("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat,
                "-c", "copy", OUT], check=True, capture_output=True)
print(f"wrote {OUT}")
