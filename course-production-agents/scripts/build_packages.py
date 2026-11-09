#!/usr/bin/env python3
"""
build_packages.py: package rendered topics as Brightspace uploads, ONE package
per module or per week. It never builds a whole-course package.

    python3 build_packages.py build/course.json --out dist/

For every unit in course.json (written by render_topics.py) it produces:

  dist/<code>-<module|week>-NN-scorm12.zip
      SCORM 1.2. One <organization> whose single <item> is the unit, with one
      nested <item> per topic, so Brightspace shows the unit as its own module
      with one page per topic. The SCORM wrapper is injected into the packaged
      copy only (sources stay JavaScript-free). Completion: end of page plus
      dwell_seconds. No score is ever reported.

  dist/<code>-<module|week>-NN-html.zip
      The same pages without the wrapper, for upload through Brightspace
      Manage Files when the course is a Purdue course and Brightspace should
      track completion natively.

Then it validates every archive: manifest at the zip root, well-formed XML,
unique identifiers, every identifierref resolves, every href exists, nesting
is unit > topics, one SCO per page, wrapper injected, no bundled media.

Standard library only. Exit code 1 on any error.
"""

import argparse
import json
import pathlib
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

# Wrapper copied verbatim from the modular-scorm-course standard.
WRAPPER = r"""/* SCORM 1.2 completion wrapper. Injected at packaging time only.
   Marks the SCO incomplete on open, completed after the learner reaches the
   end of the page AND stays MIN_DWELL_SECONDS. Reports no score. */
(function () {
  "use strict";
  var MIN_DWELL_SECONDS = __DWELL__;
  var SCROLL_SLACK_PX = 120;
  var api = null, live = false, marked = false, dwell = false, end = false;
  function findAPI(win) {
    var depth = 0;
    while (win && depth < 10) {
      if (win.API) { return win.API; }
      if (!win.parent || win.parent === win) { break; }
      win = win.parent; depth += 1;
    }
    return null;
  }
  function getAPI() {
    var f = null;
    try { f = findAPI(window); } catch (e) { f = null; }
    if (!f && window.opener) { try { f = findAPI(window.opener); } catch (e2) { f = null; } }
    return f;
  }
  function init() {
    api = getAPI();
    if (!api) { return false; }
    try { live = String(api.LMSInitialize("")) === "true"; } catch (e) { live = false; }
    if (!live) { return false; }
    try {
      var s = api.LMSGetValue("cmi.core.lesson_status");
      if (!s || s === "not attempted") { api.LMSSetValue("cmi.core.lesson_status", "incomplete"); api.LMSCommit(""); }
      else if (s === "completed" || s === "passed") { marked = true; }
    } catch (e3) {}
    return true;
  }
  function complete() {
    if (!live || marked) { return; }
    try { api.LMSSetValue("cmi.core.lesson_status", "completed"); api.LMSCommit(""); marked = true; } catch (e) {}
  }
  function check() { if (dwell && end) { complete(); } }
  function atEnd() {
    var d = document.documentElement, b = document.body;
    var h = Math.max(b.scrollHeight, d.scrollHeight, b.offsetHeight, d.offsetHeight);
    var v = window.innerHeight || d.clientHeight;
    var y = window.pageYOffset || d.scrollTop || b.scrollTop || 0;
    if (h <= v + SCROLL_SLACK_PX) { return true; }
    return (y + v) >= (h - SCROLL_SLACK_PX);
  }
  function onScroll() { if (!end && atEnd()) { end = true; check(); } }
  function teardown() { if (!live) { return; } try { api.LMSCommit(""); api.LMSFinish(""); } catch (e) {} live = false; }
  if (!init()) { return; }
  window.setTimeout(function () { dwell = true; check(); }, MIN_DWELL_SECONDS * 1000);
  window.addEventListener("scroll", onScroll, false);
  window.addEventListener("resize", onScroll, false);
  window.addEventListener("load", onScroll, false);
  window.addEventListener("pagehide", teardown, false);
  window.addEventListener("unload", teardown, false);
  onScroll();
})();
"""

CP = "http://www.imsproject.org/xsd/imscp_rootv1p1p2"
ADL = "http://www.adlnet.org/xsd/adlcp_rootv1p2"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
MEDIA_EXT = ("mp4", "mov", "m4v", "webm", "mp3", "wav", "avi", "mkv")

errors, warnings = [], []


def check_source(text, rel):
    if re.search(r"<script\b", text, re.I):
        errors.append("script tag in source: %s" % rel)
    if "</body>" not in text:
        errors.append("no closing body tag: %s" % rel)
    if 'lang="' not in text.split("<head", 1)[0]:
        errors.append("missing lang on <html>: %s" % rel)
    if len(re.findall(r"<h1\b", text)) != 1:
        errors.append("expected exactly one <h1>: %s" % rel)
    if re.search(r"<(link|iframe|object|embed)\b", text, re.I):
        errors.append("external asset or frame in source: %s" % rel)
    if chr(0x2014) in text:
        errors.append("em-dash in source: %s" % rel)
    levels = [int(m) for m in re.findall(r"<h([1-6])\b", text)]
    for a, b in zip(levels, levels[1:]):
        if b > a + 1:
            errors.append("skipped heading level h%d to h%d: %s" % (a, b, rel))
            break
    for m in re.finditer(r"<img\b[^>]*>", text, re.I):
        if "alt=" not in m.group(0):
            errors.append("img without alt: %s" % rel)


def write_manifest(pkg, ident, unit, title, n_offset=0):
    ET.register_namespace("", CP)
    ET.register_namespace("adlcp", ADL)
    ET.register_namespace("xsi", XSI)
    man = ET.Element("{%s}manifest" % CP, {
        "identifier": ident, "version": "1.0",
        "{%s}schemaLocation" % XSI:
            "http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd "
            "http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd "
            "http://www.imsglobal.org/xsd/imsmd_rootv1p2p1 imsmd_rootv1p2p1.xsd"})
    meta = ET.SubElement(man, "{%s}metadata" % CP)
    ET.SubElement(meta, "{%s}schema" % CP).text = "ADL SCORM"
    ET.SubElement(meta, "{%s}schemaversion" % CP).text = "1.2"
    orgs = ET.SubElement(man, "{%s}organizations" % CP, {"default": "ORG-1"})
    org = ET.SubElement(orgs, "{%s}organization" % CP, {"identifier": "ORG-1"})
    ET.SubElement(org, "{%s}title" % CP).text = title
    resources = ET.SubElement(man, "{%s}resources" % CP)
    for i, tp in enumerate(unit["topics"], start=1):
        rid = "RES-%02d-%03d" % (unit["number"], i)
        href = "content/%s/%s" % (unit["folder"], tp["file"])
        it = ET.SubElement(org, "{%s}item" % CP, {"identifier": "ITEM-%02d-%03d" % (unit["number"], i), "identifierref": rid, "isvisible": "true"})
        ET.SubElement(it, "{%s}title" % CP).text = tp["title"]
        res = ET.SubElement(resources, "{%s}resource" % CP, {"identifier": rid, "type": "webcontent", "{%s}scormtype" % ADL: "sco", "href": href})
        ET.SubElement(res, "{%s}file" % CP, {"href": href})
        ET.SubElement(res, "{%s}file" % CP, {"href": "scorm-wrapper.js"})
        for img in sorted((pkg / "content" / unit["folder"] / "images").glob("**/*")):
            if img.is_file():
                ET.SubElement(res, "{%s}file" % CP, {"href": img.relative_to(pkg).as_posix()})
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(man, encoding="unicode")
    (pkg / "imsmanifest.xml").write_text(xml, encoding="utf-8")


def zipdir(src, target):
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(src).as_posix())


def validate_scorm(target, unit):
    """Structural validation of a SCORM 1.2 package against what Brightspace needs."""
    found = []
    with zipfile.ZipFile(target) as z:
        names = set(z.namelist())
        if z.testzip():
            found.append("corrupt entry")
        if "imsmanifest.xml" not in names:
            return ["imsmanifest.xml is not at the archive root"]
        try:
            root = ET.fromstring(z.read("imsmanifest.xml"))
        except ET.ParseError as exc:
            return ["manifest not well-formed: %s" % exc]
        ns = {"cp": CP}
        if root.tag != "{%s}manifest" % CP:
            found.append("root element is not an IMS CP 1.1.2 manifest")
        if root.findtext("cp:metadata/cp:schemaversion", namespaces=ns) != "1.2":
            found.append("schemaversion is not 1.2")
        ids = [e.get("identifier") for e in root.iter() if e.get("identifier")]
        if len(ids) != len(set(ids)):
            found.append("duplicate identifiers in manifest")
        orgs = root.findall("cp:organizations/cp:organization", ns)
        default = root.find("cp:organizations", ns).get("default")
        if len(orgs) != 1 or orgs[0].get("identifier") != default:
            found.append("expected exactly one organization matching the default")
        # One module per unit: the organization is the module and each topic sits directly under it.
        top = orgs[0].findall("cp:item", ns) if orgs else []
        if len(top) != len(unit["topics"]):
            found.append("expected %d topic items directly under the organization, found %d" % (len(unit["topics"]), len(top)))
        for k in top:
            if k.findall("cp:item", ns):
                found.append("topic item %s has nested items; Brightspace would import a submodule" % k.get("identifier"))
            if not k.get("identifierref"):
                found.append("topic item %s does not launch a page" % k.get("identifier"))
        res = {r.get("identifier"): r for r in root.findall("cp:resources/cp:resource", ns)}
        for it in root.iter("{%s}item" % CP):
            ref = it.get("identifierref")
            if ref and ref not in res:
                found.append("identifierref %s does not resolve" % ref)
        for r in res.values():
            if r.get("{%s}scormtype" % ADL) != "sco":
                found.append("resource %s is not scormtype sco" % r.get("identifier"))
            for f in [r.get("href")] + [f.get("href") for f in r.findall("cp:file", ns)]:
                if f not in names:
                    found.append("href %s is not in the archive" % f)
        html = [x for x in names if x.endswith(".html")]
        if len(html) != len(unit["topics"]):
            found.append("expected %d html files, archive has %d" % (len(unit["topics"]), len(html)))
        for x in html:
            if 'src="../../scorm-wrapper.js"' not in z.read(x).decode("utf-8"):
                found.append("wrapper not injected into %s" % x)
        media = [x for x in names if x.rsplit(".", 1)[-1].lower() in MEDIA_EXT]
        if media:
            found.append("media bundled in the package (stream it instead): %s" % media)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course_json")
    ap.add_argument("--out", default="dist")
    ap.add_argument("--units", help="comma list of unit numbers to package, default all")
    a = ap.parse_args()

    cfg_path = pathlib.Path(a.course_json).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if cfg.get("unit_format") not in ("module", "week"):
        print("ERROR unit_format must be module or week. Whole-course packages are refused by design.")
        sys.exit(1)
    content = cfg_path.parent / "content"
    out = pathlib.Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    stage = out / ".stage"
    want = {int(x) for x in a.units.split(",")} if a.units else None
    word = "week" if cfg["unit_format"] == "week" else "module"
    code = re.sub(r"[^a-z0-9]+", "-", cfg["code"].lower()).strip("-")
    summary = []

    for unit in cfg["units"]:
        if want and unit["number"] not in want:
            continue
        n = unit["number"]
        for kind in ("scorm12", "html"):
            pkg = stage / ("%s-%02d-%s" % (word, n, kind))
            if pkg.exists():
                shutil.rmtree(pkg)
            dst = pkg / "content" / unit["folder"] if kind == "scorm12" else pkg / unit["folder"]
            dst.mkdir(parents=True)
            for tp in unit["topics"]:
                src = content / unit["folder"] / tp["file"]
                if not src.exists():
                    errors.append("missing rendered file %s" % src)
                    continue
                text = src.read_text(encoding="utf-8")
                if kind == "scorm12":
                    check_source(text, "%s/%s" % (unit["folder"], tp["file"]))
                    text = text.replace("</body>", '<script src="../../scorm-wrapper.js"></script>\n</body>', 1)
                (dst / tp["file"]).write_text(text, encoding="utf-8")
            imgs = content / unit["folder"] / "images"
            if imgs.is_dir():
                shutil.copytree(imgs, dst / "images")
            if kind == "scorm12":
                (pkg / "scorm-wrapper.js").write_text(WRAPPER.replace("__DWELL__", str(int(cfg.get("dwell_seconds", 45)))), encoding="utf-8")
                write_manifest(pkg, "%s-%s-%02d" % (cfg["code"].upper().replace(" ", ""), word.upper(), n), unit,
                               "%s %s" % (cfg["code"], unit["title"]))
            target = out / ("%s-%s-%02d-%s.zip" % (code, word, n, kind))
            zipdir(pkg, target)
            if kind == "scorm12":
                problems = validate_scorm(target, unit)
                errors.extend("%s: %s" % (target.name, p) for p in problems)
                summary.append({"unit": unit["title"], "package": target.name, "pages": len(unit["topics"]),
                                "kb": round(target.stat().st_size / 1024, 1), "manifest_valid": not problems})
            else:
                summary.append({"unit": unit["title"], "package": target.name, "pages": len(unit["topics"]),
                                "kb": round(target.stat().st_size / 1024, 1), "manifest_valid": None})
    shutil.rmtree(stage, ignore_errors=True)
    (out / "package-report.json").write_text(json.dumps({"packages": summary, "errors": errors, "warnings": warnings}, indent=2), encoding="utf-8")
    for s in summary:
        flag = "" if s["manifest_valid"] is None else ("  manifest OK" if s["manifest_valid"] else "  MANIFEST FAILED")
        print("%-42s %2d pages %7.1f KB%s" % (s["package"], s["pages"], s["kb"], flag))
    for w in warnings:
        print("WARNING " + w)
    for e in errors:
        print("ERROR " + e)
    if errors:
        sys.exit(1)
    print("All package checks passed. %d %s package(s), one per %s." % (len([s for s in summary if s["manifest_valid"] is not None]), "SCORM 1.2", word))


if __name__ == "__main__":
    main()
