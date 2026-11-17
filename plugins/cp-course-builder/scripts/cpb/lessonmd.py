"""Parse cp-course-builder lesson Markdown into a block list.

A lesson file is front matter (a small YAML subset) followed by Markdown with
block directives:

    :::type key=value key="two words" Optional title
    ...content...
    :::

`+++` on its own line is a continue divider. The full grammar is in
skills/cp-build/references/lesson-format.md. Standard library only.
"""

import re

# ---------------------------------------------------------------- front matter

def _scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.lower() in ("true", "yes"):
        return True
    if v.lower() in ("false", "no"):
        return False
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    if v.startswith("[") and v.endswith("]"):
        return [_scalar(x) for x in v[1:-1].split(",") if x.strip()]
    return v


def parse_front_matter(text):
    """Return (meta, body). Supports key: value, lists of scalars, and lists of
    one-level maps (`- key: value` followed by indented `key: value`)."""
    if not text.startswith("---"):
        return {}, text
    end = re.search(r"^---\s*$", text[3:], re.M)
    if not end:
        return {}, text
    block = text[3:3 + end.start()]
    body = text[3 + end.end():].lstrip("\n")
    meta, key, item = {}, None, None
    for raw in block.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if indent == 0 and ":" in line and not line.startswith("- "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            meta[key] = _scalar(val) if val else []
            item = None
        elif line.startswith("- ") and key is not None:
            rest = line[2:]
            m = re.match(r"([A-Za-z_][\w-]*):\s*(.*)$", rest)
            if m and not rest.startswith(("\"", "'")):
                item = {m.group(1): _scalar(m.group(2))}
                meta[key].append(item)
            else:
                meta[key].append(_scalar(rest))
                item = None
        elif item is not None and ":" in line:
            k, _, v = line.partition(":")
            item[k.strip()] = _scalar(v)
    return meta, body

# ---------------------------------------------------------------- directives

ARG_RE = re.compile(r'([A-Za-z_][\w-]*)=("([^"]*)"|\S+)')


def parse_args(rest):
    args = {}
    for m in ARG_RE.finditer(rest):
        args[m.group(1)] = m.group(3) if m.group(3) is not None else m.group(2)
    title = ARG_RE.sub("", rest).strip()
    return args, title


def split_blocks(body):
    """Split the body into top-level chunks: ('md', lines) runs, ('dir', type,
    args, title, lines, line_no) directives and ('continue',)."""
    out, buf = [], []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^:::\s*([a-z][\w-]*)\s*(.*)$", line)
        if m:
            if buf:
                out.append(("md", buf, i - len(buf) + 1))
                buf = []
            start = i + 1
            inner = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                inner.append(lines[i])
                i += 1
            if i >= len(lines):
                raise ValueError(f"line {start}: block :::{m.group(1)} is never closed with :::")
            args, title = parse_args(m.group(2))
            out.append(("dir", m.group(1), args, title, inner, start))
            i += 1
            continue
        if line.strip() == "+++":
            if buf:
                out.append(("md", buf, i - len(buf) + 1))
                buf = []
            out.append(("continue", i + 1))
            i += 1
            continue
        buf.append(line)
        i += 1
    if buf:
        out.append(("md", buf, len(lines) - len(buf) + 1))
    return out

# ---------------------------------------------------------------- markdown

def md_elements(lines):
    """Very small Markdown block parser: headings, paragraphs, lists, tables."""
    els, para = [], []

    def flush():
        if para:
            els.append({"t": "p", "text": " ".join(s.strip() for s in para)})
            para.clear()

    i = 0
    caption = None
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
            continue
        h = re.match(r"^(#{2,4})\s+(.*)$", s)
        if h:
            flush()
            els.append({"t": "h", "level": len(h.group(1)), "text": h.group(2).strip()})
            i += 1
            continue
        if s.startswith("Table:"):
            flush()
            caption = s[6:].strip()
            i += 1
            continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            els.append({"t": "table", "caption": caption, "rows": rows})
            caption = None
            continue
        lm = re.match(r"^(\d+\.|[-*])\s+(.*)$", s)
        if lm:
            flush()
            ordered = lm.group(1)[0].isdigit()
            items = []
            while i < len(lines):
                cur = lines[i]
                cs = cur.strip()
                m2 = re.match(r"^(\d+\.|[-*])\s+(.*)$", cs)
                if m2 and (m2.group(1)[0].isdigit()) == ordered and len(cur) - len(cur.lstrip()) < 2:
                    items.append(m2.group(2))
                    i += 1
                elif cs and items and (len(cur) - len(cur.lstrip()) >= 2):
                    items[-1] += " " + cs
                    i += 1
                else:
                    break
            els.append({"t": "ol" if ordered else "ul", "items": items})
            continue
        para.append(line)
        i += 1
    flush()
    return els


def sections_by_heading(lines, level=3):
    """Split lines into (heading, lines) at `###` (or given level) headings.
    Lines before the first heading are returned with heading None."""
    out = [(None, [])]
    mark = "#" * level + " "
    for line in lines:
        if line.strip().startswith(mark):
            out.append((line.strip()[len(mark):].strip(), []))
        else:
            out[-1][1].append(line)
    if not out[0][1] or not any(s.strip() for s in out[0][1]):
        out = out[1:]
    return out


def keyed(lines, keys):
    """Pull `key: value` lines from the top of a block; the rest is body.
    A key line may run on into following lines until a blank line."""
    vals, body, i = {}, [], 0
    while i < len(lines):
        s = lines[i].strip()
        m = re.match(r"^([a-z][\w-]*):\s*(.*)$", s)
        if m and m.group(1) in keys:
            val = [m.group(2)]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^([a-z][\w-]*):\s", lines[i].strip()):
                val.append(lines[i].strip())
                i += 1
            vals[m.group(1)] = " ".join(val).strip()
            continue
        if not s and not body:
            i += 1
            continue
        body = lines[i:]
        break
    return vals, body


def labeled_parts(lines, labels):
    """Split lines at lines that start with one of the labels ("Model answer:")."""
    parts, cur = {"": []}, ""
    for line in lines:
        s = line.strip()
        hit = next((lab for lab in labels if s.startswith(lab + ":")), None)
        if hit:
            cur = hit
            parts[cur] = [s[len(hit) + 1:].strip()]
        else:
            parts.setdefault(cur, []).append(line)
    return {k: "\n".join(v).strip() for k, v in parts.items()}


def options(lines):
    """Parse `- [ ] text` / `- [x] text` options with indented `Why:` or
    `Result:` lines. Returns (stem_lines, [ {text, correct, why} ])."""
    stem, opts = [], []
    for line in lines:
        s = line.strip()
        m = re.match(r"^-\s+\[( |x|X)\]\s+(.*)$", s)
        if m:
            opts.append({"text": m.group(2).strip(), "correct": m.group(1).lower() == "x", "why": ""})
            continue
        w = re.match(r"^(Why|Result):\s*(.*)$", s)
        if w and opts:
            opts[-1]["why"] = (opts[-1]["why"] + " " + w.group(2)).strip()
            continue
        if opts and s and line.startswith((" ", "\t")):
            opts[-1]["why"] = (opts[-1]["why"] + " " + s).strip()
            continue
        if not opts:
            stem.append(line)
    return stem, opts

# ---------------------------------------------------------------- lesson model

INTERACTIONS = {"accordion", "tabs", "flashcards", "process", "labeled-graphic", "sorting", "scenario", "check"}
ITEM_TYPES = {"check", "recall", "sorting", "scenario"}
KNOWN = INTERACTIONS | {"problem", "case", "term", "caution", "quote", "figure", "compare", "recall",
                        "reflect", "depth", "video", "synthesis", "practice", "worked", "statement"}


def parse_lesson(text, path="lesson.md"):
    meta, body = parse_front_matter(text)
    blocks = []
    section = None
    for chunk in split_blocks(body):
        if chunk[0] == "continue":
            blocks.append({"type": "continue", "line": chunk[1], "section": section})
            continue
        if chunk[0] == "md":
            for el in md_elements(chunk[1]):
                if el["t"] == "h" and el["level"] == 2:
                    section = el["text"]
                el["type"] = "md"
                el["section"] = section
                blocks.append(el)
            continue
        _, typ, args, title, inner, line = chunk
        if typ not in KNOWN:
            raise ValueError(f"{path} line {line}: unknown block :::{typ}")
        blocks.append({"type": typ, "args": args, "title": title, "lines": inner, "line": line, "section": section})
    return {"meta": meta, "blocks": blocks, "path": path}


def words(text):
    return len(re.findall(r"[A-Za-z0-9][\w'%-]*", re.sub(r"\[[^\]]*\]\([^)]*\)", lambda m: m.group(0).split("](")[0], text or "")))
