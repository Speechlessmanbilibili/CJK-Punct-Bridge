#!/usr/bin/env python3
"""Structural regression check for horizontal/vertical CJK dash shaping.

Requires fontTools. It intentionally implements only the GSUB lookup types used by
ccmp/locl/vert/vrt2 in these fonts, so it can run without HarfBuzz.
"""
from pathlib import Path
from fontTools.ttLib import TTFont
import sys


def _langsys(gsub, script_tag, lang_tag):
    for sr in gsub.ScriptList.ScriptRecord:
        if sr.ScriptTag == script_tag:
            if lang_tag is None:
                return sr.Script.DefaultLangSys
            for lr in sr.Script.LangSysRecord:
                if lr.LangSysTag == lang_tag:
                    return lr.LangSys
    return None


def _apply_lookup(glyphs, lookup):
    out = glyphs[:]
    for st in lookup.SubTable:
        lookup_type = lookup.LookupType
        if lookup_type == 7:
            st = st.ExtSubTable
            lookup_type = st.ExtensionLookupType
        if lookup_type == 1 and hasattr(st, "mapping"):
            out = [st.mapping.get(g, g) for g in out]
        elif lookup_type == 4:
            ligatures = getattr(st, "ligatures", {})
            result = []
            i = 0
            while i < len(out):
                hit = None
                for lig in ligatures.get(out[i], []):
                    seq = [out[i], *lig.Component]
                    if out[i:i + len(seq)] == seq and (hit is None or len(seq) > hit[0]):
                        hit = (len(seq), lig.LigGlyph)
                if hit:
                    result.append(hit[1])
                    i += hit[0]
                else:
                    result.append(out[i])
                    i += 1
            out = result
    return out


def _shape(font, text, script, lang, vertical):
    cmap = font.getBestCmap()
    gsub = font["GSUB"].table
    glyphs = [cmap[ord(ch)] for ch in text]
    ls = _langsys(gsub, script, lang) or _langsys(gsub, script, None)
    for feature_index in ls.FeatureIndex:
        feature_record = gsub.FeatureList.FeatureRecord[feature_index]
        tag = feature_record.FeatureTag
        if tag not in ("ccmp", "locl", "vert", "vrt2"):
            continue
        if tag in ("vert", "vrt2") and not vertical:
            continue
        for lookup_index in feature_record.Feature.LookupListIndex:
            glyphs = _apply_lookup(glyphs, gsub.LookupList.Lookup[lookup_index])
    return glyphs


def _orientation(font, glyph_name):
    glyph = font["glyf"][glyph_name]
    glyph.recalcBounds(font["glyf"])
    width = getattr(glyph, "xMax", 0) - getattr(glyph, "xMin", 0)
    height = getattr(glyph, "yMax", 0) - getattr(glyph, "yMin", 0)
    return "horizontal" if width > height else "vertical" if height > width else "square"


def check_font(path):
    font = TTFont(path)
    assert "GSUB" in font and "vhea" in font and "vmtx" in font, f"missing layout/vertical tables: {path}"
    for count, text in enumerate(("—", "——", "———"), 1):
        for script, lang in (("hani", "ZHS "), ("DFLT", None)):
            horizontal = _shape(font, text, script, lang, False)
            vertical = _shape(font, text, script, lang, True)
            assert len(horizontal) == 1 and _orientation(font, horizontal[0]) == "horizontal", (path, text, "horizontal", horizontal)
            assert len(vertical) == 1 and _orientation(font, vertical[0]) == "vertical", (path, text, "vertical", vertical)
        english = _shape(font, text, "latn", "ENG ", False)
        assert len(english) == count, (path, text, "ENG unexpectedly ligated", english)
        assert all(_orientation(font, g) == "horizontal" for g in english), (path, text, "ENG orientation", english)
    font.close()


def main():
    targets = [Path(p) for p in sys.argv[1:]]
    if not targets:
        root = Path(__file__).resolve().parents[1]
        targets = sorted((root / "fonts").rglob("*.ttf")) + sorted((root / "fonts").rglob("*.woff2"))
    if not targets:
        raise SystemExit("No font files found")
    for target in targets:
        check_font(target)
    print(f"PASS: {len(targets)} font file(s)")


if __name__ == "__main__":
    main()
