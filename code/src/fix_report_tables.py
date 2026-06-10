"""Rewrite pipe-table delimiter rows in report/report.md so each column's
dash count is proportional to its real content width. With pandoc
--columns=80, wide tables then get proportional p{} columns in LaTeX
instead of equal-width columns (which squeezed long rationale text and
wrapped player names mid-name). Idempotent.
"""
import re
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "report" / "report.md"
lines = path.read_text().splitlines()

DELIM = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")


def is_row(s):
    return s.lstrip().startswith("|")


def cells(s):
    return [c.strip() for c in s.strip().strip("|").split("|")]


out, i = [], 0
while i < len(lines):
    line = lines[i]
    if (is_row(line) and i + 1 < len(lines) and is_row(lines[i + 1])
            and DELIM.match(lines[i + 1]) and "-" in lines[i + 1]):
        header = cells(line)
        ncol = len(header)
        # gather body rows
        j = i + 2
        body = []
        while j < len(lines) and is_row(lines[j]):
            body.append(cells(lines[j]))
            j += 1
        widths = [len(h) for h in header]
        for row in body:
            for k in range(min(ncol, len(row))):
                widths[k] = max(widths[k], len(row[k]))
        # cap a single runaway column at 60 percent of the total
        total = sum(widths)
        widths = [min(w, max(8, int(total * 0.6))) for w in widths]
        delim = "|" + "|".join("-" * max(3, w) for w in widths) + "|"
        out.append(line)
        out.append(delim)
        out.extend(lines[i + 2:j])
        i = j
    else:
        out.append(line)
        i += 1

path.write_text("\n".join(out) + "\n")
print(f"rewrote delimiter rows in {path}")
