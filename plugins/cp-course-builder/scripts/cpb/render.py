"""Render a parsed lesson into one Rise-style HTML page.

Every component is complete as plain HTML: with scripts off, panels show,
answers sit in disclosures and nothing is lost. cp-lesson.js adds behavior
only. No inline styles are ever written; positions and widths use classes
from cp-lesson.css.
"""

import html
import re

from .lessonmd import (keyed, labeled_parts, md_elements, options, sections_by_heading)

esc = lambda s: html.escape(str(s or ""), quote=True)
CORRECT = ' data-correct="true"'
CURRENT = ' class="cp-current"'


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:48] or "section"


def inline(text):
    """Escape, then apply **bold**, *em*, `code` and [text](href)."""
    t = esc(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*\s][^*]*)\*(?!\w)", r"<em>\1</em>", t)

    def link(m):
        label, href = m.group(1), html.unescape(m.group(2))
        if not re.match(r"^(https://|\.{0,2}/|#|[\w./-]+\.(html|pdf|docx|xlsx|pptx)(#[\w-]+)?$)", href):
            return label
        return f'<a href="{esc(href)}">{label}</a>'

    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
    return t


class Ids:
    def __init__(self):
        self.used = set()

    def make(self, base):
        b = slug(base)
        cand, n = b, 2
        while cand in self.used:
            cand = f"{b}-{n}"
            n += 1
        self.used.add(cand)
        return cand


def md_html(lines, ids, base_level=2, heading_shift=0):
    out = []
    for el in md_elements(lines) if isinstance(lines, list) else lines:
        out.append(element_html(el, ids, heading_shift))
    return "\n".join(out)


def element_html(el, ids, shift=0):
    t = el["t"]
    if t == "h":
        lvl = min(el["level"] + shift, 6)
        hid = ids.make(el["text"])
        return f'<h{lvl} id="{hid}">{inline(el["text"])}</h{lvl}>'
    if t == "p":
        return f"<p>{inline(el['text'])}</p>"
    if t in ("ul", "ol"):
        items = "".join(f"<li>{inline(i)}</li>" for i in el["items"])
        return f"<{t}>{items}</{t}>"
    if t == "table":
        rows = el["rows"]
        if not rows:
            return ""
        cap = f"<caption>{inline(el['caption'])}</caption>" if el.get("caption") else ""
        head = "".join(f'<th scope="col">{inline(c)}</th>' for c in rows[0])
        body = ""
        for r in rows[1:]:
            cells = f'<th scope="row">{inline(r[0])}</th>' + "".join(f"<td>{inline(c)}</td>" for c in r[1:])
            body += f"<tr>{cells}</tr>"
        return (f'<div class="cp-table-wrap"><table>{cap}<thead><tr>{head}</tr></thead>'
                f"<tbody>{body}</tbody></table></div>")
    return ""


def label(text):
    return f'<p class="cp-label">{esc(text)}</p>'


def wrap(kind, inner, extra="", band=False, tag="section", labelled=None):
    cls = f"cp-block cp-{kind}" + (" cp-band" if band else "") + (f" {extra}" if extra else "")
    lab = f' aria-labelledby="{labelled}"' if labelled else ""
    return f'<{tag} class="{cls}"{lab}>\n{inner}\n</{tag}>'


# ---------------------------------------------------------------- components

def figure_html(vals, desc, ids, text_html="", fig_no=None):
    src, alt = vals.get("src", ""), vals.get("alt", "")
    cap = vals.get("caption", "")
    credit = vals.get("credit", "")
    fid = ids.make("figure-" + (str(fig_no) if fig_no else slug(alt)[:20]))
    num = f"Figure {fig_no}. " if fig_no else ""
    capline = f"{num}{inline(cap)}" + (f' <span class="cp-credit">{inline(credit)}</span>' if credit else "")
    img = f'<img src="{esc(src)}" alt="{esc(alt)}" loading="lazy">'
    if src.startswith("placeholder:") or not src:
        img = (f'<div class="cp-placeholder" role="img" aria-label="{esc(alt)}">'
               f'<p>Graphic needed: {esc(alt)}</p></div>')
    d = ""
    if desc:
        d = (f'<details class="cp-longdesc"><summary>Description of figure{" " + str(fig_no) if fig_no else ""}</summary>'
             f"\n{md_html(desc.splitlines(), ids, heading_shift=1)}\n</details>")
    fig = f'<figure id="{fid}">{img}<figcaption>{capline}</figcaption></figure>\n{d}'
    if text_html:
        return (f'<div class="cp-split"><div class="cp-split-media">{fig}</div>'
                f'<div class="cp-split-text">{text_html}</div></div>')
    return fig


class Renderer:
    def __init__(self, lesson, ctx):
        self.lesson = lesson
        self.ctx = ctx
        self.ids = Ids()
        self.fig_no = 0
        self.n = {}
        self.items = []  # retrieval items for the item bank

    def count(self, kind):
        self.n[kind] = self.n.get(kind, 0) + 1
        return self.n[kind]

    def item(self, b, kind, stem):
        a = b["args"]
        self.items.append({"lesson": self.lesson["meta"].get("id"), "kind": kind, "objective": a.get("objective"),
                           "bloom": a.get("bloom"), "spaced_from": a.get("spaced_from"),
                           "source": a.get("source"), "stem": stem})

    # each block type -------------------------------------------------------
    def b_problem(self, b):
        hid = self.ids.make(b["title"] or "the-problem")
        inner = (label(b["args"].get("label", "From the field")) +
                 f'<h2 id="{hid}">{inline(b["title"])}</h2>\n' + md_html(b["lines"], self.ids, heading_shift=1))
        return wrap("problem", inner, band=True, labelled=hid)

    def b_case(self, b):
        vals, body = keyed(b["lines"], {"facts"})
        parts = labeled_parts(body, ["Facts"])
        hid = self.ids.make(b["title"] or "case")
        facts = ""
        if parts.get("Facts"):
            rows = []
            for line in parts["Facts"].splitlines():
                m = re.match(r"^-\s+([^:]+):\s*(.*)$", line.strip())
                if m:
                    rows.append(f"<dt>{inline(m.group(1))}</dt><dd>{inline(m.group(2))}</dd>")
            facts = f'<dl class="cp-facts">{"".join(rows)}</dl>'
        inner = (label("Case") + f'<h2 id="{hid}">{inline(b["title"])}</h2>\n' +
                 md_html(parts.get("", "").splitlines(), self.ids, heading_shift=1) + facts)
        return wrap("case", inner, band=True, labelled=hid)

    def b_term(self, b):
        hid = self.ids.make("term-" + b["title"])
        inner = (label("Key term") + f'<h3 id="{hid}"><dfn>{inline(b["title"])}</dfn></h3>\n' +
                 md_html(b["lines"], self.ids))
        return wrap("term", inner, tag="aside", labelled=hid)

    def b_caution(self, b):
        hid = self.ids.make("caution-" + b["title"])
        inner = label("Caution") + f'<h3 id="{hid}">{inline(b["title"])}</h3>\n' + md_html(b["lines"], self.ids)
        return wrap("caution", inner, band=True, tag="aside", labelled=hid)

    def b_statement(self, b):
        return wrap("statement", md_html(b["lines"], self.ids), tag="div")

    def b_quote(self, b):
        who = f'<p class="cp-quote-by">{inline(b["title"])}</p>' if b["title"] else ""
        body = md_html(b["lines"], self.ids)
        return wrap("quote", f"<blockquote>{body}</blockquote>{who}", tag="div")

    def b_figure(self, b):
        vals, body = keyed(b["lines"], {"src", "alt", "caption", "credit", "layout", "kind"})
        parts = labeled_parts(body, ["Text", "Description"])
        self.fig_no += 1
        text_html = md_html(parts.get("Text", "").splitlines(), self.ids) if parts.get("Text") else ""
        if parts.get("", "").strip():
            text_html = md_html(parts[""].splitlines(), self.ids) + text_html
        return wrap("figure", figure_html(vals, parts.get("Description", ""), self.ids, text_html, self.fig_no),
                    extra="cp-wide" if vals.get("layout") == "full" else "", tag="div")

    def b_labeled_graphic(self, b):
        vals, body = keyed(b["lines"], {"src", "alt", "caption", "credit"})
        parts = labeled_parts(body, ["Description"])
        self.fig_no += 1
        n = self.count("lg")
        hid = self.ids.make(b["title"] or "labeled-graphic")
        marks, items = [], []
        for i, raw in enumerate([l for l in parts.get("", "").splitlines() if re.match(r"^\s*\d+\.", l)], 1):
            m = re.match(r"^\s*\d+\.\s+(?:\((\d{1,3})%?,\s*(\d{1,3})%?\)\s+)?(.*)$", raw)
            x, y, text = m.group(1), m.group(2), m.group(3)
            lab = re.match(r"\*\*([^*]+)\*\*:?\s*(.*)$", text)
            name = lab.group(1) if lab else text[:40]
            tid = f"lg{n}-part-{i}"
            items.append(f'<li id="{tid}">{inline(text)}</li>')
            if x and y:
                xc, yc = int(round(int(x) / 5.0) * 5), int(round(int(y) / 5.0) * 5)
                marks.append(f'<a class="cp-marker cp-x-{min(xc, 100)} cp-y-{min(yc, 100)}" href="#{tid}" '
                             f'aria-label="Part {i}: {esc(name)}">{i}</a>')
        img = f'<img src="{esc(vals.get("src", ""))}" alt="{esc(vals.get("alt", ""))}" loading="lazy">'
        cap = f"Figure {self.fig_no}. {inline(vals.get('caption', ''))}"
        if vals.get("credit"):
            cap += f' <span class="cp-credit">{inline(vals["credit"])}</span>'
        desc = ""
        if parts.get("Description"):
            desc = (f'<details class="cp-longdesc"><summary>Description of figure {self.fig_no}</summary>'
                    f'{md_html(parts["Description"].splitlines(), self.ids)}</details>')
        inner = (label("Labeled graphic") + f'<h3 id="{hid}">{inline(b["title"] or "Parts of the figure")}</h3>'
                 f'<figure class="cp-lg"><div class="cp-lg-stage">{img}{"".join(marks)}</div>'
                 f"<figcaption>{cap}</figcaption></figure>{desc}"
                 f'<ol class="cp-lg-parts" aria-label="Labeled parts">{"".join(items)}</ol>')
        return wrap("labeled-graphic", inner, tag="section", labelled=hid)

    def b_accordion(self, b):
        hid = self.ids.make(b["title"] or "accordion")
        panels = []
        for head, lines in sections_by_heading(b["lines"]):
            if head is None:
                continue
            pid = self.ids.make(head)
            panels.append(f'<h3 class="cp-acc-h" id="{pid}">{inline(head)}</h3>'
                          f'<div class="cp-acc-panel">{md_html(lines, self.ids, heading_shift=2)}</div>')
        lead = md_html(sections_by_heading(b["lines"])[0][1], self.ids) if sections_by_heading(b["lines"]) and sections_by_heading(b["lines"])[0][0] is None else ""
        title = f'<h3 id="{hid}" class="cp-group-title">{inline(b["title"])}</h3>' if b["title"] else ""
        return wrap("accordion", f'{title}{lead}<div class="cp-accordion" data-cp-accordion>{"".join(panels)}</div>', tag="div")

    def b_tabs(self, b):
        n = self.count("tabs")
        panels = []
        for head, lines in sections_by_heading(b["lines"]):
            if head is None:
                continue
            pid = self.ids.make(f"tab-{n}-{head}")
            panels.append(f'<section class="cp-tab-panel" id="{pid}"><h3 class="cp-tab-h">{inline(head)}</h3>'
                          f"{md_html(lines, self.ids, heading_shift=2)}</section>")
        return wrap("tabs", f'<div class="cp-tabs" data-cp-tabs data-label="{esc(b["title"] or "Options")}">'
                            f'{"".join(panels)}</div>', tag="div")

    def b_compare(self, b):
        hid = self.ids.make(b["title"] or "compare")
        cols = []
        for head, lines in sections_by_heading(b["lines"]):
            if head is None:
                continue
            cid = self.ids.make(head)
            cols.append(f'<div class="cp-compare-col"><h3 id="{cid}">{inline(head)}</h3>'
                        f"{md_html(lines, self.ids, heading_shift=2)}</div>")
        title = f'<h3 id="{hid}" class="cp-group-title">{inline(b["title"])}</h3>' if b["title"] else ""
        return wrap("compare", f'{title}<div class="cp-compare">{"".join(cols)}</div>', tag="div")

    def b_flashcards(self, b):
        hid = self.ids.make(b["title"] or "flashcards")
        cards, cur = [], None
        for line in b["lines"]:
            s = line.strip()
            if s.startswith("Q:"):
                cur = {"q": s[2:].strip(), "a": ""}
                cards.append(cur)
            elif s.startswith("A:") and cur:
                cur["a"] = s[2:].strip()
            elif s and cur:
                if cur["a"]:
                    cur["a"] += " " + s
                else:
                    cur["q"] += " " + s
        lis = "".join(
            f'<li class="cp-card"><p class="cp-card-front">{inline(c["q"])}</p>'
            f'<details class="cp-card-back"><summary>Turn the card</summary><p>{inline(c["a"])}</p></details></li>'
            for c in cards)
        intro = '<p class="cp-instruction">Answer each prompt before you turn the card.</p>'
        inner = label("Flashcards") + f'<h3 id="{hid}">{inline(b["title"] or "Test yourself")}</h3>{intro}<ul class="cp-cards" role="list">{lis}</ul>'
        return wrap("flashcards", inner, labelled=hid)

    def b_process(self, b):
        hid = self.ids.make(b["title"] or "process")
        steps = []
        for head, lines in sections_by_heading(b["lines"]):
            if head is None:
                continue
            steps.append(f'<li class="cp-step"><p class="cp-step-title">{inline(head)}</p>'
                         f"{md_html(lines, self.ids, heading_shift=2)}</li>")
        inner = (label("Step by step") + f'<h3 id="{hid}">{inline(b["title"] or "The steps")}</h3>'
                 f'<ol class="cp-steps" data-cp-process aria-labelledby="{hid}">{"".join(steps)}</ol>')
        return wrap("process", inner, labelled=hid)

    def _choice_item(self, b, kind):
        n = self.count("item")
        stem_lines, opts = options(b["lines"])
        stem = " ".join(s.strip() for s in stem_lines if s.strip())
        self.item(b, kind, stem)
        multi = sum(o["correct"] for o in opts) > 1
        itype = "checkbox" if multi else "radio"
        name = f"q{n}"
        hid = self.ids.make(b["title"] or f"{kind}-{n}")
        rows, keyrows = [], []
        for i, o in enumerate(opts, 1):
            oid = f"{name}-o{i}"
            data = ' data-correct="true"' if o["correct"] else ""
            verdict = ("Best choice." if o["correct"] else "Consider the cost.") if kind == "scenario" else ("Correct." if o["correct"] else "Not correct.")
            rows.append(f'<li><input type="{itype}" id="{oid}" name="{name}" value="{i}"{data}>'
                        f'<label for="{oid}">{inline(o["text"])}</label>'
                        f'<p class="cp-feedback" data-for="{oid}" hidden><strong>{verdict}</strong> {inline(o["why"])}</p></li>')
            keyrows.append(f'<li><strong>{inline(o["text"])}</strong> {verdict} {inline(o["why"])}</li>')
        hint = "Choose all that apply, then select Check." if multi else (
            "Choose what you would do." if kind == "scenario" else "Choose one answer, then select Check.")
        btn = "See what happens" if kind == "scenario" else "Check my answer"
        lab = "Scenario" if kind == "scenario" else "Knowledge check"
        title = f'<h3 id="{hid}">{inline(b["title"])}</h3>' if b["title"] else ""
        inner = (label(lab) + title +
                 f'<form class="cp-check" data-cp-check data-kind="{kind}"><fieldset><legend>{inline(stem)}</legend>'
                 f'<p class="cp-instruction">{hint}</p><ul class="cp-options" role="list">{"".join(rows)}</ul></fieldset>'
                 f'<div class="cp-actions" hidden><button type="submit" class="cp-btn">{btn}</button>'
                 f'<button type="reset" class="cp-btn cp-btn-quiet">Try again</button></div>'
                 f'<p class="cp-status" role="status" aria-live="polite"></p>'
                 f'<details class="cp-key"><summary>Show the answer and explanations</summary><ul>{"".join(keyrows)}</ul></details>'
                 f"</form>")
        return wrap("scenario" if kind == "scenario" else "check", inner, band=kind == "scenario",
                    labelled=hid if title else None)

    def b_check(self, b):
        return self._choice_item(b, "check")

    def b_scenario(self, b):
        # A scenario carries its situation before the choices.
        return self._choice_item(b, "scenario")

    def b_recall(self, b):
        n = self.count("item")
        parts = labeled_parts(b["lines"], ["Model answer", "Criteria"])
        prompt = parts.get("", "")
        self.item(b, "recall", prompt)
        hid = self.ids.make(b["title"] or f"recall-{n}")
        tid = f"recall-{n}-answer"
        crit = f'<p><strong>A strong answer:</strong> {inline(parts["Criteria"])}</p>' if parts.get("Criteria") else ""
        inner = (label("Free recall") + f'<h3 id="{hid}">{inline(b["title"] or "Explain it in your own words")}</h3>' +
                 md_html(prompt.splitlines(), self.ids) +
                 f'<label class="cp-note-label" for="{tid}">Your answer (not saved or submitted)</label>'
                 f'<textarea id="{tid}" rows="4"></textarea>'
                 f'<p class="cp-instruction">Write your answer before revealing.</p>'
                 f'<details class="cp-reveal"><summary>Reveal the model answer</summary>'
                 f'{md_html(parts.get("Model answer", "").splitlines(), self.ids)}{crit}</details>')
        return wrap("recall", inner, labelled=hid)

    def b_sorting(self, b):
        n = self.count("item")
        vals, body = keyed(b["lines"], {"categories"})
        cats = [c.strip() for c in vals.get("categories", "").split("|") if c.strip()]
        stem, rows, key = [], [], []
        for line in body:
            m = re.match(r"^-\s+(.*?)\s+=>\s+(.*)$", line.strip())
            if m:
                rows.append({"text": m.group(1), "cat": m.group(2).strip(), "why": ""})
            elif rows and line.strip().startswith("Why:"):
                rows[-1]["why"] = line.strip()[4:].strip()
            elif not rows and line.strip():
                stem.append(line.strip())
        self.item(b, "sorting", " ".join(stem))
        hid = self.ids.make(b["title"] or f"sorting-{n}")
        lis = []
        for i, r in enumerate(rows, 1):
            sid = f"s{n}-{i}"
            opts = '<option value="">Choose a category</option>' + "".join(
                f'<option value="{esc(c)}"{CORRECT if c == r["cat"] else ""}>{esc(c)}</option>' for c in cats)
            lis.append(f'<li><label for="{sid}">{inline(r["text"])}</label><select id="{sid}">{opts}</select>'
                       f'<p class="cp-feedback" data-for="{sid}" hidden></p></li>')
            key.append(f'<li><strong>{inline(r["text"])}</strong>: {esc(r["cat"])}. {inline(r["why"])}</li>')
        inner = (label("Sorting") + f'<h3 id="{hid}">{inline(b["title"] or "Sort these")}</h3>'
                 f'<form class="cp-sort" data-cp-sort><p>{inline(" ".join(stem))}</p>'
                 f'<ul class="cp-sort-items" role="list">{"".join(lis)}</ul>'
                 f'<div class="cp-actions" hidden><button type="submit" class="cp-btn">Check my sorting</button>'
                 f'<button type="reset" class="cp-btn cp-btn-quiet">Try again</button></div>'
                 f'<p class="cp-status" role="status" aria-live="polite"></p>'
                 f'<details class="cp-key"><summary>Show the answer key</summary><ul>{"".join(key)}</ul></details></form>')
        return wrap("sorting", inner, labelled=hid)

    def b_reflect(self, b):
        n = self.count("reflect")
        tid = f"reflect-{n}"
        hid = self.ids.make(b["title"] or "reflect")
        title = b["title"] or "Connect this to your work"
        inner = (label("Reflect") + f'<h3 id="{hid}">{inline(title)}</h3>' + md_html(b["lines"], self.ids) +
                 f'<label class="cp-note-label" for="{tid}">Your notes (not saved or submitted)</label>'
                 f'<textarea id="{tid}" rows="4"></textarea>')
        return wrap("reflect", inner, labelled=hid)

    def b_depth(self, b):
        title = b["title"] or "Optional: more depth"
        return wrap("depth", f'<details class="cp-depth"><summary>{inline(title)}</summary>'
                             f"{md_html(b['lines'], self.ids, heading_shift=1)}</details>", tag="div")

    def b_video(self, b):
        a = b["args"]
        hid = self.ids.make("video-" + (a.get("id") or b["title"]))
        mins = a.get("minutes", "")
        script = md_html(b["lines"], self.ids)
        meta = f'<p class="cp-meta">{esc(a.get("id", ""))}{", about " + esc(mins) + " minutes" if mins else ""}</p>'
        inner = (label("Video") + f'<h3 id="{hid}">{inline(b["title"])}</h3>{meta}'
                 f'<div class="cp-video-slot"><p>Video to be produced. The script and transcript below ship with the page.</p></div>'
                 f'<details class="cp-transcript"><summary>Script and transcript</summary>{script}</details>')
        return wrap("video", inner, labelled=hid)

    def b_synthesis(self, b):
        hid = self.ids.make(b["title"] or "bringing-it-together")
        return wrap("synthesis", f'<h2 id="{hid}">{inline(b["title"] or "Bringing it together")}</h2>'
                                 f"{md_html(b['lines'], self.ids, heading_shift=1)}", labelled=hid)

    def b_practice(self, b):
        hid = self.ids.make("practice")
        inner = (label("Practice") + f'<h2 id="{hid}">{inline(b["title"] or "Practice this")}</h2>'
                 + md_html(b["lines"], self.ids, heading_shift=1))
        return wrap("practice", inner, band=True, tag="aside", labelled=hid)

    def b_worked(self, b):
        faded = b["args"].get("faded") in ("true", "yes") or b["title"].lower().startswith("faded")
        hid = self.ids.make(b["title"] or "worked-example")
        lis = []
        for raw in [l for l in b["lines"] if l.strip()]:
            s = raw.strip()
            m = re.match(r"^\d+\.\s+(.*)$", s)
            if m:
                txt = m.group(1)
                if txt.startswith("?"):
                    lis.append({"blank": True, "text": txt[1:].strip(), "answer": ""})
                else:
                    step, _, why = txt.partition(" Why: ")
                    lis.append({"blank": False, "text": step, "why": why})
            elif s.startswith("Answer:") and lis:
                lis[-1]["answer"] = s[7:].strip()
        out = []
        for i, it in enumerate(lis, 1):
            if it["blank"]:
                out.append(f'<li class="cp-step-blank"><p><strong>Your turn.</strong> {inline(it["text"])}</p>'
                           f'<details class="cp-reveal"><summary>Reveal step {i}</summary><p>{inline(it["answer"])}</p></details></li>')
            else:
                why = f' <span class="cp-why">{inline(it["why"])}</span>' if it.get("why") else ""
                out.append(f"<li>{inline(it['text'])}{why}</li>")
        lab = "Faded example: finish the last steps yourself" if faded else "Worked example"
        inner = label(lab) + f'<h3 id="{hid}">{inline(b["title"] or "Work through it")}</h3><ol class="cp-worked">{"".join(out)}</ol>'
        return wrap("worked", inner, labelled=hid)

    # ------------------------------------------------------------------ page
    def body(self):
        out = []
        blocks = self.lesson["blocks"]
        for i, b in enumerate(blocks):
            if b["type"] == "md":
                out.append(element_html(b, self.ids))
                continue
            if b["type"] == "continue":
                nxt = next((x for x in blocks[i + 1:] if x["type"] != "continue"), None)
                target = None
                if nxt is not None and nxt["type"] == "md" and nxt["t"] == "h":
                    target = nxt["text"]
                elif nxt is not None:
                    target = nxt.get("title") or None
                out.append(("__CONTINUE__", target))
                continue
            fn = getattr(self, "b_" + b["type"].replace("-", "_"))
            out.append(fn(b))
        # resolve continue dividers to the id of the next heading
        html_out, pending = [], []
        for part in out:
            if isinstance(part, tuple):
                pending.append(part[1])
                html_out.append(None)
            else:
                html_out.append(part)
        final = []
        for idx, part in enumerate(html_out):
            if part is not None:
                final.append(part)
                continue
            nxt = next((p for p in html_out[idx + 1:] if p), "")
            m = re.search(r'id="([^"]+)"', nxt)
            hm = re.search(r"<h[23][^>]*>(.*?)</h[23]>", nxt)
            name = re.sub(r"<[^>]+>", "", hm.group(1)) if hm else "the next section"
            href = f"#{m.group(1)}" if m else "#cp-end"
            final.append(f'<div class="cp-continue"><a class="cp-continue-link" href="{href}">'
                         f'Continue to {esc(html.unescape(name))}</a></div>')
        return "\n".join(final)


def outline_html(ctx):
    lessons = ctx["lessons"]
    idx = ctx["index"]
    lis = []
    for i, (lid, title, fname) in enumerate(lessons):
        cur = ' aria-current="page"' if i == idx else ""
        mark = '<span class="cp-visually-hidden">Current lesson: </span>' if i == idx else ""
        if ctx.get("target") == "html":
            lis.append(f'<li><a href="{esc(fname)}"{cur}>{mark}{esc(title)}</a></li>')
        else:
            lis.append(f'<li{CURRENT if i == idx else ""}{cur}>{mark}{esc(title)}</li>')
    n = len(lessons)
    pos = idx + 1
    note = "" if ctx.get("target") == "html" else '<p class="cp-outline-note">Use the course navigation to move between lessons.</p>'
    return (f'<nav class="cp-outline" aria-label="Lessons in this module">'
            f'<p class="cp-outline-course">{esc(ctx.get("course", ""))}</p>'
            f'<p class="cp-outline-module">{esc(ctx.get("module_title", ""))}</p>'
            f'<p class="cp-progress-text" id="cp-progress-label">Lesson {pos} of {n}</p>'
            f'<progress class="cp-progress" max="{n}" value="{pos}" aria-labelledby="cp-progress-label"></progress>'
            f'<ol class="cp-outline-list">{"".join(lis)}</ol>{note}</nav>')


def objectives_html(meta, ids):
    objs = meta.get("objectives") or []
    if not objs:
        return ""
    texts = [o.get("text", "") if isinstance(o, dict) else str(o) for o in objs]
    hid = ids.make("what-you-will-be-able-to-do")
    if len(texts) == 1:
        body = f"<p>By the end of this lesson you will be able to {inline(texts[0])}</p>"
    else:
        body = "<p>By the end of this lesson you will be able to:</p><ul>" + "".join(f"<li>{inline(t)}</li>" for t in texts) + "</ul>"
    return wrap("outcome", label("Outcome") + f'<h2 id="{hid}">What you will be able to do</h2>{body}', labelled=hid)


def render_page(lesson, ctx):
    meta = lesson["meta"]
    r = Renderer(lesson, ctx)
    title = meta.get("title", "Untitled lesson")
    outcome = objectives_html(meta, r.ids)
    body = r.body()
    hero_img = ""
    if meta.get("header_image"):
        hero_img = (f'<div class="cp-hero-media"><img src="{esc(meta["header_image"])}" '
                    f'alt="{esc(meta.get("header_alt", ""))}"></div>')
    draft = ""
    if str(meta.get("draft", "ai")).lower() != "final" or not meta.get("finalized_by"):
        draft = '<p class="cp-draft-flag">Draft for ID review. Not final.</p>'
    minutes = meta.get("minutes")
    eyebrow = esc(ctx.get("module_title", ""))
    css, js = ctx.get("css_href", "cp-lesson.css"), ctx.get("js_href", "cp-lesson.js")
    profile = esc(ctx.get("theme", ""))
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="cp-lesson-id" content="{esc(meta.get('id', ''))}">
<meta name="cp-draft" content="{'final' if not draft else 'draft'}">
<title>{esc(title)} | {eyebrow}</title>
<link rel="stylesheet" href="{esc(css)}">
</head>
<body class="cp{' cp-theme-' + profile if profile else ''}">
<a class="cp-skip" href="#main">Skip to main content</a>
<div class="cp-shell">
{outline_html(ctx)}
<main id="main" class="cp-main">
{draft}
<header class="cp-hero">
{hero_img}
<div class="cp-hero-text">
<p class="cp-eyebrow">{eyebrow}</p>
<h1>{esc(title)}</h1>
{f'<p class="cp-meta">About {esc(minutes)} minutes</p>' if minutes else ''}
</div>
</header>
<div class="cp-column">
{outcome}
{body}
<p class="cp-end" id="cp-end">End of lesson.</p>
</div>
</main>
</div>
<footer class="cp-footer"><p>{esc(ctx.get('course', ''))} | Purdue University Online</p></footer>
<script src="{esc(js)}"></script>
</body>
</html>
"""
    return page, r.items
