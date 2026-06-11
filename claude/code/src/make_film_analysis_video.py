"""Render the split-screen film-analysis video for the release thread
(release/images/tweet1_fable_film_study.mp4). Left side plays the real
clip segments Fable cited in film/notes/boozer.md; right side shows its
actual notes. Frame numbers are seconds (stills were cut at 1 fps), so
each cited frame maps to an exact clip timestamp. Audio is dropped
(reel music is copyrighted). Requires ffmpeg and PIL.
"""
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[3]
CLIP = REPO / "claude/code/film/clips/boozer_KwEliYUNeUg.webm"
OUT = REPO / "release/images/tweet1_fable_film_study.mp4"
TMP = Path("/tmp/fable_film_video")
TMP.mkdir(exist_ok=True)

BG = (16, 20, 24)
PANEL = (26, 32, 39)
FG = (242, 242, 242)
MUTED = (138, 148, 158)
CYAN = (94, 200, 229)
GOLD = (245, 197, 66)


def font(size, bold=False):
    name = "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold \
        else "/System/Library/Fonts/Supplemental/Arial.ttf"
    return ImageFont.truetype(name, size)


def draw_wrapped(d, text, xy, f, fill, width, leading=1.35):
    x, y = xy
    for para in text.split("\n"):
        for line in textwrap.wrap(para, width=width) or [""]:
            d.text((x, y), line, font=f, fill=fill)
            y += int(f.size * leading)
    return y


SEGMENTS = [
    {
        "start": 283, "dur": 12,
        "title": "Post seal into rim finish",
        "game": "vs Texas Tech, Madison Square Garden",
        "body": ("Wide, low post seal on the right block, defender pinned "
                 "on his hip (frame 0289). One frame later he is airborne "
                 "at the rim with the ball carried high and away from the "
                 "swipe (frame 0290).\n"
                 "The stills support a strong wide-base seal and a high "
                 "ball position on the finish. They cannot show how "
                 "quickly he elevated."),
    },
    {
        "start": 556, "dur": 12,
        "title": "Full extension in traffic",
        "game": "vs Louisville",
        "body": ("In a crowded paint he rises off two feet and reaches "
                 "full arm extension above the rim line with his torso "
                 "still vertical rather than drifting (frames 0562-0563).\n"
                 "Body control and extension at the catch point of the "
                 "play. Takeoff speed is not claimable from stills."),
    },
    {
        "start": 604, "dur": 12,
        "title": "Faceup iso posture",
        "game": "at Virginia Tech",
        "body": ("Bent-knee faceup stance with the ball shielded on the "
                 "outside hip, not in front of his body (frame 0610). By "
                 "frame 0612 he has shifted toward the middle with the "
                 "defender still attached.\n"
                 "A deliberate, shielded approach. Separation quickness "
                 "is not visible at 1 fps."),
    },
]

# Intro card, full 1280x720
img = Image.new("RGB", (1280, 720), BG)
d = ImageDraw.Draw(img)
d.text((640, 200), "AN AI SCOUT WATCHES FILM", font=font(58, True),
       fill=FG, anchor="mm")
d.text((640, 290), "Claude Fable 5 studied 685 stills, cut at 1 fps from a public season reel",
       font=font(26), fill=MUTED, anchor="mm")
d.text((640, 340), "Cameron Boozer, PF, Duke", font=font(34, True),
       fill=CYAN, anchor="mm")
d.text((640, 430), "Its actual film notes appear beside the footage, frame references and all",
       font=font(24), fill=FG, anchor="mm")
d.text((640, 560), "Stills cannot show speed, burst, or timing. The notes never pretend otherwise.",
       font=font(22), fill=GOLD, anchor="mm")
img.save(TMP / "intro.png")

# Right-side note panels, 480x720
for i, seg in enumerate(SEGMENTS):
    img = Image.new("RGB", (480, 720), PANEL)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 480, 86], fill=BG)
    d.text((24, 22), "CLAUDE FABLE 5", font=font(26, True), fill=CYAN)
    d.text((24, 56), "film notes, from stills only", font=font(18), fill=MUTED)
    d.text((24, 116), f"{i+1} / 3", font=font(20, True), fill=GOLD)
    d.text((24, 150), seg["title"], font=font(27, True), fill=FG)
    d.text((24, 188), seg["game"], font=font(20), fill=MUTED)
    y = draw_wrapped(d, seg["body"], (24, 240), font(21), FG, width=38)
    d.rectangle([0, 648, 480, 720], fill=BG)
    d.text((24, 668), "1 fps frame study. No claims about speed,",
           font=font(17), fill=MUTED)
    d.text((24, 692), "burst, or timing. Full notes in the repo.",
           font=font(17), fill=MUTED)
    img.save(TMP / f"panel{i}.png")

# Build segment videos, left footage 800x720 (clip 800x450 centered), right panel
parts = []
intro_mp4 = TMP / "part_intro.mp4"
subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", "3", "-i", TMP / "intro.png",
                "-f", "lavfi", "-t", "3", "-i", "anullsrc=r=44100:cl=stereo",
                "-vf", "format=yuv420p", "-r", "30", "-c:v", "libx264",
                "-c:a", "aac", "-shortest", intro_mp4],
               check=True, capture_output=True)
parts.append(intro_mp4)

for i, seg in enumerate(SEGMENTS):
    out = TMP / f"part{i}.mp4"
    fc = ("[0:v]scale=800:450,pad=800:720:0:135:0x101418[clip];"
          "[1:v]scale=480:720[panel];[clip][panel]hstack=inputs=2,"
          "format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-ss", str(seg["start"]), "-t", str(seg["dur"]),
                    "-i", CLIP, "-loop", "1", "-t", str(seg["dur"]),
                    "-i", TMP / f"panel{i}.png",
                    "-f", "lavfi", "-t", str(seg["dur"]),
                    "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
                    "-r", "30", "-c:v", "libx264", "-c:a", "aac",
                    "-shortest", out],
                   check=True, capture_output=True)
    parts.append(out)

concat = TMP / "list.txt"
concat.write_text("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat,
                "-c", "copy", OUT], check=True, capture_output=True)
print(f"wrote {OUT}")
