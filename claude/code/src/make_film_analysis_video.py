"""Render the split-screen film-analysis launch video
(release/images/tweet1_fable_film_study.mp4).

A 1 second title frame (doubles as the thumbnail) cuts straight into
three film sessions. Left side plays the real clip segments Fable cited
in film/notes/boozer.md inside a framed slot; right side shows its
actual notes plus a FABLE SIGNALS row of evaluation chips (green for
what the stills support, gold for what they cannot show). A short
public-release outro closes. Frame numbers map to clip seconds (stills
were cut at 1 fps). Audio is dropped (reel music is copyrighted).
Needs ffmpeg and PIL.
"""
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[3]
CLIP = REPO / "claude/code/film/clips/boozer_KwEliYUNeUg.webm"
OUT = REPO / "release/images/tweet1_fable_film_study.mp4"
TMP = Path("/tmp/fable_film_video3")
TMP.mkdir(exist_ok=True)

BG = (5, 6, 8)
PANEL = (10, 13, 17)
CARD = (16, 20, 26)
FG = (240, 242, 244)
MUTED = (125, 135, 146)
DIM = (66, 75, 84)
CYAN = (94, 200, 229)
GOLD = (235, 188, 80)
GREEN = (127, 209, 127)

HN = "/System/Library/Fonts/HelveticaNeue.ttc"


def font(size, weight="regular"):
    idx = {"regular": 0, "bold": 1, "italic": 2}[weight]
    return ImageFont.truetype(HN, size, index=idx)


def wrap_text(d, text, xy, f, fill, width, leading=1.42):
    x, y = xy
    for line in textwrap.wrap(text, width=width):
        d.text((x, y), line, font=f, fill=fill)
        y += int(f.size * leading)
    return y


def chip(d, x, y, text, color, f):
    pad_x, pad_y = 12, 7
    bbox = d.textbbox((0, 0), text, font=f)
    w = bbox[2] - bbox[0] + 2 * pad_x
    h = bbox[3] - bbox[1] + 2 * pad_y + 4
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2,
                        outline=color, width=1)
    d.text((x + pad_x, y + pad_y - bbox[1] + 2), text, font=f, fill=color)
    return x + w + 10, h


SEGMENTS = [
    {
        "start": 283, "dur": 11,
        "session": "FILM SESSION 01",
        "title": "Post seal into rim finish",
        "game": "vs Texas Tech, Madison Square Garden",
        "body": ("Wide, low post seal on the right block with the defender "
                 "pinned on his hip (frame 0289). One frame later he is "
                 "airborne at the rim, ball carried high and away from the "
                 "swipe (frame 0290)."),
        "signals": [("NBA-ready frame", GREEN), ("high finish point", GREEN),
                    ("elevation speed n/a", GOLD)],
    },
    {
        "start": 556, "dur": 11,
        "session": "FILM SESSION 02",
        "title": "Full extension in traffic",
        "game": "vs Louisville",
        "body": ("In a crowded paint he rises off two feet to full arm "
                 "extension above the rim line, torso staying vertical "
                 "rather than drifting (frames 0562-0563)."),
        "signals": [("body control", GREEN), ("vertical extension", GREEN),
                    ("takeoff speed n/a", GOLD)],
    },
    {
        "start": 604, "dur": 11,
        "session": "FILM SESSION 03",
        "title": "Faceup iso posture",
        "game": "at Virginia Tech",
        "body": ("Bent-knee faceup stance with the ball shielded on the "
                 "outside hip, not in front of the body (frame 0610). By "
                 "frame 0612 he has worked middle with the defender still "
                 "attached."),
        "signals": [("shielded handle", GREEN), ("deliberate approach", GREEN),
                    ("separation burst n/a", GOLD)],
    },
]

W, H = 1280, 720

# ---------- title frame (1s, doubles as the thumbnail) ----------
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 3], fill=CYAN)
d.text((W // 2, 250), "AN AI SCOUT", font=font(78, "bold"), fill=FG, anchor="mm")
d.text((W // 2, 338), "WATCHES FILM", font=font(78, "bold"), fill=CYAN, anchor="mm")
d.text((W // 2, 432), "a fully autonomous 2026 draft big board, built by Claude Fable 5",
       font=font(26), fill=MUTED, anchor="mm")
d.text((W // 2, 500), "subject of this session   Cameron Boozer, PF, Duke",
       font=font(22, "bold"), fill=GOLD, anchor="mm")
d.rectangle([0, H - 3, W, H], fill=CYAN)
img.save(TMP / "title.png")

# ---------- outro card ----------
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 3], fill=CYAN)
d.text((W // 2, 226), "EVERYTHING IS PUBLIC", font=font(64, "bold"),
       fill=FG, anchor="mm")
d.line([W // 2 - 170, 290, W // 2 + 170, 290], fill=DIM, width=1)
d.text((W // 2, 346), "two detailed research papers, both big boards, every dossier,",
       font=font(25), fill=FG, anchor="mm")
d.text((W // 2, 390), "the models, the film notes, and all of the code",
       font=font(25), fill=FG, anchor="mm")
d.text((W // 2, 478), "github.com/arcAman07/nba-draft-2026-ai-big-board",
       font=font(28, "bold"), fill=CYAN, anchor="mm")
d.text((W // 2, 580), "Claude Fable 5 vs Codex GPT 5.5, same prompt, zero hints. The draft decides.",
       font=font(21, "italic"), fill=GOLD, anchor="mm")
d.rectangle([0, H - 3, W, H], fill=CYAN)
img.save(TMP / "outro.png")

# ---------- left backgrounds and right panels ----------
SLOT_X, SLOT_Y, SLOT_W, SLOT_H = 20, 146, 760, 428
for i, seg in enumerate(SEGMENTS):
    img = Image.new("RGB", (800, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 800, 3], fill=CYAN)
    d.text((SLOT_X + 2, 78), seg["session"], font=font(18, "bold"), fill=GOLD)
    d.text((SLOT_X + 2, 108), "Cameron Boozer, PF, Duke", font=font(22, "bold"), fill=FG)
    d.rectangle([SLOT_X - 2, SLOT_Y - 2, SLOT_X + SLOT_W + 2, SLOT_Y + SLOT_H + 2],
                outline=(48, 58, 68), width=2)
    d.text((SLOT_X + 2, SLOT_Y + SLOT_H + 18),
           "source, public season reel studied as 1 fps stills",
           font=font(18), fill=MUTED)
    d.rectangle([0, H - 3, 800, H], fill=CYAN)
    img.save(TMP / f"left{i}.png")

    img = Image.new("RGB", (480, H), PANEL)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 480, 3], fill=CYAN)
    d.rectangle([0, 3, 480, 96], fill=CARD)
    d.rectangle([0, 3, 5, 96], fill=CYAN)
    d.text((28, 24), "FABLE FILM NOTES", font=font(27, "bold"), fill=FG)
    d.text((28, 62), "written from stills only, verbatim from the repo",
           font=font(17), fill=MUTED)
    for j in range(3):
        cx = 36 + j * 30
        d.ellipse([cx - 6, 128, cx + 6, 140], fill=GOLD if j == i else DIM)
    d.text((28, 168), seg["title"], font=font(29, "bold"), fill=FG)
    d.text((28, 212), seg["game"], font=font(18), fill=MUTED)
    y = wrap_text(d, seg["body"], (28, 262), font(22), FG, width=36)
    y += 14
    d.line([28, y, 452, y], fill=(48, 58, 68), width=1)
    y += 22
    d.text((28, y), "FABLE SIGNALS", font=font(16, "bold"), fill=CYAN)
    y += 34
    x = 28
    rows_h = 0
    for text, color in seg["signals"]:
        f = font(17, "bold")
        bbox = d.textbbox((0, 0), text, font=f)
        w = bbox[2] - bbox[0] + 24
        if x + w > 452:
            x = 28
            y += rows_h + 10
        x, rows_h = chip(d, x, y, text, color, f)
    y += rows_h + 18
    d.text((28, y), "from its notes. green, supported. gold, not claimable at 1 fps.",
           font=font(15, "italic"), fill=MUTED)
    d.rectangle([0, 654, 480, H], fill=CARD)
    d.text((28, 674), "full notes, frames, and the paper are in the repo",
           font=font(17), fill=MUTED)
    d.rectangle([0, H - 3, 480, H], fill=CYAN)
    img.save(TMP / f"panel{i}.png")


def render_card(name, png, dur, fade_in=0.0, fade_out=0.5):
    out = TMP / f"part_{name}.mp4"
    vf = []
    if fade_in:
        vf.append(f"fade=t=in:st=0:d={fade_in}")
    if fade_out:
        vf.append(f"fade=t=out:st={dur - fade_out}:d={fade_out}")
    vf.append("format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", png,
                    "-vf", ",".join(vf), "-r", "30",
                    "-c:v", "libx264", "-an", out], check=True, capture_output=True)
    return out


parts = [render_card("title", TMP / "title.png", 1.0, fade_in=0.0, fade_out=0.3)]

for i, seg in enumerate(SEGMENTS):
    out = TMP / f"part{i}.mp4"
    dur = seg["dur"]
    fc = (f"[0:v]scale={SLOT_W}:{SLOT_H}[clip];"
          f"[1:v][clip]overlay={SLOT_X}:{SLOT_Y}[left];"
          f"[left][2:v]hstack=inputs=2,"
          f"fade=t=in:st=0:d=0.35,fade=t=out:st={dur - 0.35}:d=0.35,"
          f"format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y",
                    "-ss", str(seg["start"]), "-t", str(dur), "-i", CLIP,
                    "-loop", "1", "-t", str(dur), "-i", TMP / f"left{i}.png",
                    "-loop", "1", "-t", str(dur), "-i", TMP / f"panel{i}.png",
                    "-filter_complex", fc, "-map", "[v]", "-r", "30",
                    "-c:v", "libx264", "-an", out], check=True, capture_output=True)
    parts.append(out)

parts.append(render_card("outro", TMP / "outro.png", 4, fade_in=0.4, fade_out=0.6))

concat = TMP / "list.txt"
concat.write_text("".join(f"file '{p}'\n" for p in parts))
silent = TMP / "silent.mp4"
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat,
                "-c", "copy", silent], check=True, capture_output=True)

# quiet generated ambient pad (A major drone, slow swells), royalty free
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", silent],
                           check=True, capture_output=True, text=True).stdout.strip())
expr = ("0.045*sin(2*PI*110*t)*(0.55+0.45*sin(2*PI*0.05*t))"
        "+0.035*sin(2*PI*164.81*t)*(0.55+0.45*sin(2*PI*0.073*t+1.3))"
        "+0.028*sin(2*PI*220*t)*(0.5+0.5*sin(2*PI*0.041*t+2.1))"
        "+0.02*sin(2*PI*329.63*t)*(0.4+0.6*sin(2*PI*0.027*t+0.7))")
subprocess.run(["ffmpeg", "-y", "-i", silent,
                "-f", "lavfi", "-t", f"{dur:.2f}",
                "-i", f"aevalsrc={expr}:s=44100",
                "-af", f"lowpass=f=2800,afade=t=in:st=0:d=1.5,"
                       f"afade=t=out:st={dur - 2.5:.2f}:d=2.5,volume=0.9",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "96k",
                "-shortest", OUT], check=True, capture_output=True)
print(f"wrote {OUT}")
