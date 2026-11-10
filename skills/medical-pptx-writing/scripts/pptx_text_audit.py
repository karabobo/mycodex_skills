#!/usr/bin/env python3
"""Audit and repair text properties inside a .pptx package: proofing language
and whole-point font sizes.

Why this exists: PowerPoint takes the proofing language from every text run
(`<a:rPr lang="...">`), not from one document-wide setting. A deck assembled by
a script inherits the package default (usually en-US), so Chinese runs are then
checked by an English dictionary and show up as misspelled. The same files often
keep stale spell-check error flags (`err="1"`) from earlier edits. The correct
repair is to set the language per run and clear the old flags inside the file —
not to switch off proofing for the whole presentation.

Usage:
  python3 scripts/pptx_text_audit.py deck.pptx
  python3 scripts/pptx_text_audit.py deck.pptx --json
  python3 scripts/pptx_text_audit.py deck.pptx --fix --output deck.fixed.pptx
  python3 scripts/pptx_text_audit.py --self-test

Two defects are covered:
  * proofing language — see above;
  * fractional font sizes — human decks use whole points (12, 14, 18), while
    scaled/auto-fit runs end up at 10.5, 13.13 or 8.63 pt. Round to the nearest
    whole point and keep the title and reference-list floors intact.

Exit codes: 0 clean (or fixed), 1 findings without --fix, 2 the file could not be read.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

CJK_RE = re.compile(
    "[\u2e80-\u2fff\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff"
    "\uf900-\ufaff\uff00-\uffef]"
)
TEXT_PART_RE = re.compile(
    r"^ppt/(?:slides/slide|notesSlides/notesSlide|slideLayouts/slideLayout|"
    r"slideMasters/slideMaster|notesMasters/notesMaster)\d+\.xml$"
)
RUN_RE = re.compile(r"<a:r>(.*?)</a:r>", re.S)
PARA_RE = re.compile(r"<a:p>(.*?)</a:p>", re.S)
T_RE = re.compile(r"(<a:t\b[^>]*>)(.*?)(</a:t>)", re.S)
RPR_OPEN_RE = re.compile(r"<a:rPr\b[^>]*?(?:/>|>)")
LANG_ATTR_RE = re.compile(r'\blang="([^"]*)"')
ERR_ATTR_RE = re.compile(r'\s+err="1"')
ENDPARA_RE = re.compile(r"<a:endParaRPr\b[^>]*?(?:/>|>)")
SZ_ATTR_RE = re.compile(r'\bsz="(\d+)"')
SZ_TAG_RE = re.compile(r"<a:(?:rPr|endParaRPr|defRPr)\b[^>]*?(?:/>|>)")

ZH = "zh-CN"
EN = "en-US"


def expected_lang(text):
    """Chinese text (including mixed CJK/Latin runs) is proofed as Chinese."""
    return ZH if CJK_RE.search(text) else EN


def _tag_without_err(tag, stats):
    if ERR_ATTR_RE.search(tag):
        stats["err_removed"] += 1
        return ERR_ATTR_RE.sub("", tag)
    return tag


def _set_lang(tag, lang, stats):
    current = LANG_ATTR_RE.search(tag)
    if current and current.group(1) == lang:
        return tag
    if current:
        stats["lang_changed"] += 1
        return LANG_ATTR_RE.sub('lang="%s"' % lang, tag, count=1)
    stats["lang_added"] += 1
    closed = "/>" if tag.endswith("/>") else ">"
    return tag[: -len(closed)] + ' lang="%s"%s' % (lang, closed)


def _fix_run(body, stats):
    text_match = T_RE.search(body)
    if not text_match:
        return body
    text = (
        text_match.group(2)
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
    )
    lang = expected_lang(text)
    rpr = RPR_OPEN_RE.search(body)
    if rpr:
        tag = _tag_without_err(rpr.group(0), stats)
        tag = _set_lang(tag, lang, stats)
        return body[: rpr.start()] + tag + body[rpr.end():]
    stats["lang_added"] += 1
    return '<a:rPr lang="%s"/>' % lang + body


def _fix_paragraph(body, stats):
    body = RUN_RE.sub(lambda m: "<a:r>" + _fix_run(m.group(1), stats) + "</a:r>", body)
    texts = re.findall(r"<a:t\b[^>]*>(.*?)</a:t>", body, re.S)
    lang = expected_lang("".join(texts))

    def fix_end(match):
        tag = _tag_without_err(match.group(0), stats)
        return _set_lang(tag, lang, stats)

    return ENDPARA_RE.sub(fix_end, body)


def round_size(value):
    """Whole points only, half up: 10.5 pt -> 11 pt, 13.13 pt -> 13 pt, floor 1 pt."""
    rounded = int((value / 100.0) + 0.5) * 100
    return max(100, rounded)


def fix_sizes(xml, stats):
    def fix_tag(match):
        tag = match.group(0)

        def repl(attr):
            value = int(attr.group(1))
            if value % 100 == 0:
                return attr.group(0)
            stats["size_rounded"] += 1
            return 'sz="%d"' % round_size(value)

        return SZ_ATTR_RE.sub(repl, tag)

    return SZ_TAG_RE.sub(fix_tag, xml)


def audit_sizes(xml):
    counts = {}
    for tag in SZ_TAG_RE.findall(xml):
        for raw in SZ_ATTR_RE.findall(tag):
            value = int(raw)
            counts[value] = counts.get(value, 0) + 1
    fractional = {value: count for value, count in counts.items() if value % 100}
    return counts, fractional


def fix_xml(xml):
    stats = {"lang_added": 0, "lang_changed": 0, "err_removed": 0, "size_rounded": 0}
    new_xml = PARA_RE.sub(lambda m: "<a:p>" + _fix_paragraph(m.group(1), stats) + "</a:p>", xml)
    new_xml = fix_sizes(new_xml, stats)
    return new_xml, stats


def audit_xml(xml):
    report = {
        "runs": 0,
        "missing_lang": 0,
        "wrong_lang": 0,
        "err_flags": 0,
        "non_integer_sizes": 0,
        "size_examples": [],
        "examples": [],
    }
    for para in PARA_RE.findall(xml):
        for body in RUN_RE.findall(para):
            text_match = T_RE.search(body)
            if not text_match:
                continue
            report["runs"] += 1
            text = (
                text_match.group(2)
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
            )
            want = expected_lang(text)
            rpr = RPR_OPEN_RE.search(body)
            lang = LANG_ATTR_RE.search(rpr.group(0)) if rpr else None
            if lang is None:
                report["missing_lang"] += 1
                if len(report["examples"]) < 10:
                    report["examples"].append(
                        {"text": text[:40], "issue": "missing lang", "expected": want}
                    )
            elif lang.group(1) != want:
                report["wrong_lang"] += 1
                if len(report["examples"]) < 10:
                    report["examples"].append(
                        {
                            "text": text[:40],
                            "issue": "lang mismatch",
                            "found": lang.group(1),
                            "expected": want,
                        }
                    )
        report["err_flags"] += len(ERR_ATTR_RE.findall(para))
    _, fractional = audit_sizes(xml)
    report["non_integer_sizes"] = sum(fractional.values())
    report["size_examples"] = sorted(
        ("%.2f pt x%d" % (value / 100.0, count)) for value, count in fractional.items()
    )[:12]
    return report


def _text_parts(names):
    return [name for name in names if TEXT_PART_RE.match(name)]


def _merge(reports):
    total = {
        "runs": 0,
        "missing_lang": 0,
        "wrong_lang": 0,
        "err_flags": 0,
        "non_integer_sizes": 0,
        "size_examples": [],
        "examples": [],
    }
    for part, rep in reports.items():
        for key in ("runs", "missing_lang", "wrong_lang", "err_flags", "non_integer_sizes"):
            total[key] += rep[key]
        for item in rep["size_examples"]:
            value_key = item.split(" pt")[0]
            if any(existing.startswith(value_key + " pt") for existing in total["size_examples"]):
                continue
            if len(total["size_examples"]) < 12:
                total["size_examples"].append(item)
        for item in rep["examples"]:
            if len(total["examples"]) < 10:
                total["examples"].append(dict(item, part=part))
    return total


def audit(path):
    with zipfile.ZipFile(path) as archive:
        reports = {name: audit_xml(archive.read(name).decode("utf-8")) for name in _text_parts(archive.namelist())}
    total = _merge(reports)
    total["file"] = path
    total["parts"] = len(reports)
    total["ok"] = (
        total["missing_lang"] == 0
        and total["wrong_lang"] == 0
        and total["err_flags"] == 0
        and total["non_integer_sizes"] == 0
    )
    return total


def repair(path, output):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        text_parts = set(_text_parts(names))
        changed = {}
        stats = {
            "lang_added": 0,
            "lang_changed": 0,
            "err_removed": 0,
            "size_rounded": 0,
            "parts_changed": 0,
        }
        for name in text_parts:
            original = archive.read(name).decode("utf-8")
            fixed, part_stats = fix_xml(original)
            for key in ("lang_added", "lang_changed", "err_removed", "size_rounded"):
                stats[key] += part_stats[key]
            if fixed != original:
                changed[name] = fixed
                stats["parts_changed"] += 1

        if not changed:
            if os.path.abspath(path) != os.path.abspath(output):
                shutil.copyfile(path, output)
            result = audit(output)
            result["fix"] = stats
            return result

        handle, temp_path = tempfile.mkstemp(suffix=".pptx")
        os.close(handle)
        try:
            with zipfile.ZipFile(temp_path, "w") as target:
                for name in names:
                    info = archive.getinfo(name)
                    data = changed[name].encode("utf-8") if name in changed else archive.read(name)
                    target.writestr(info, data)
            shutil.move(temp_path, output)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    result = audit(output)
    result["fix"] = stats
    return result


SLIDE_SAMPLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody>
    <a:p><a:r><a:t>中文标题没有写语言</a:t></a:r><a:endParaRPr lang="en-US"/></a:p>
    <a:p><a:r><a:rPr lang="en-US" err="1"/><a:t>mOS 延长 6.2 个月</a:t></a:r></a:p>
    <a:p><a:r><a:rPr lang="en-US"/><a:t>Objective response rate 68%</a:t></a:r></a:p>
    <a:p><a:r><a:rPr lang="zh-CN" sz="1050"/><a:t>十分之十点五号字</a:t></a:r></a:p>
  </p:sp></p:spTree></p:cSld>
</p:sld>
"""


def self_test():
    checks = []
    with tempfile.TemporaryDirectory() as workdir:
        source = os.path.join(workdir, "sample.pptx")
        fixed = os.path.join(workdir, "fixed.pptx")
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("ppt/slides/slide1.xml", SLIDE_SAMPLE)

        report = audit(source)
        checks.append(("detects missing lang", report["missing_lang"] == 1))
        checks.append(("detects wrong lang", report["wrong_lang"] == 1))
        checks.append(("detects err flag", report["err_flags"] == 1))
        checks.append(("detects fractional size", report["non_integer_sizes"] == 1))
        checks.append(("not ok before fix", report["ok"] is False))

        result = repair(source, fixed)
        checks.append(("clean after fix", result["ok"] is True))
        checks.append(("kept run count", result["runs"] == 4))

        text = zipfile.ZipFile(fixed).read("ppt/slides/slide1.xml").decode("utf-8")
        checks.append(("no err left", 'err="1"' not in text))
        checks.append(("chinese run is zh-CN", 'lang="zh-CN"' in text))
        checks.append(("latin run stays en-US", text.count('lang="en-US"') >= 1))
        checks.append(("text preserved", "中文标题没有写语言" in text and "Objective response rate 68%" in text))
        checks.append(("endParaRPr re-languaged", '<a:endParaRPr lang="zh-CN"' in text))
        checks.append(("fractional size rounded", 'sz="1100"' in text and 'sz="1050"' not in text))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    print(json.dumps({"ok": not failed, "checks": len(checks), "failed": failed}, ensure_ascii=False))
    return 0 if not failed else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description="Audit or repair per-run proofing language in a .pptx file."
    )
    parser.add_argument("deck", nargs="?", help="path to the .pptx file")
    parser.add_argument("--output", help="write the repaired deck here (default: in place with --fix)")
    parser.add_argument("--fix", action="store_true", help="rewrite the deck with corrected languages")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--self-test", action="store_true", help="run the built-in checks")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.deck:
        parser.error("a .pptx path is required (or use --self-test)")

    try:
        if args.fix:
            output = args.output or args.deck
            report = repair(args.deck, output)
        else:
            report = audit(args.deck)
    except (OSError, zipfile.BadZipFile, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            "runs={runs} missing_lang={missing_lang} wrong_lang={wrong_lang} "
            "err_flags={err_flags} non_integer_sizes={non_integer_sizes}".format(**report)
        )
        for item in report.get("size_examples", []):
            print("  - fractional size: %s" % item)
        for item in report["examples"]:
            print("  - {issue}: {text!r}".format(**item))
        if report.get("fix"):
            print(
                "fixed: {lang_added} lang added, {lang_changed} changed, "
                "{err_removed} err flags removed, {size_rounded} sizes rounded".format(**report["fix"])
            )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
