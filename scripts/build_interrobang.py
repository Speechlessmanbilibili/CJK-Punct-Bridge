#!/usr/bin/env python3
"""CJK Punct Bridge ?! —— interrobang 连字变体构建。

从审计过的 CJK Punct Bridge 静态字体出发，每权重：
1. 合成 ?! / !? -> ‽（半角，经典叠加）与 ？！/！？-> 全宽 ‽
2. 双向连字挂 liga（默认开启），覆盖 locl 变体字形
3. 家族名 CJK Punct Bridge ?! / PS CJKPunctBridgeInterrobang
4. HANLINK_ITALIC=1 时生成斜体（新字形补 10° 斜切）

可变字体由 build_variable_interrobang.py 构建。
"""
from array import array
from copy import deepcopy
from pathlib import Path
import os
import math
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.otlLib.builder import buildLookup, buildLigatureSubstSubtable
from fontTools.otlLib.builder import buildStatTable

REPO = Path(__file__).resolve().parents[1]
STATIC_IN = Path(os.environ.get("BRIDGE_STATIC_DIR", REPO / "fonts" / "static"))
OUT = REPO / "fonts-interrobang" / "static"
OUT.mkdir(parents=True, exist_ok=True)

FAMILY = "CJK Punct Bridge ?!"
PS = "CJKPunctBridgeInterrobang"
WEIGHTS = {
    100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
    500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
    900: "Black",
}
ITALIC = os.environ.get("CJK_PUNCT_ITALIC") == "1"
SLANT_DEG = 10.0
SLANT = math.tan(math.radians(SLANT_DEG))
# 现成 ‽ 字形源：Inter 的 U+203D（interrobang），提取后按 UPM 缩放。
INTER_VF = Path(os.environ.get("INTER_VF", REPO.parent / "interrobang-sources" / "inter-var.ttf"))

COPYRIGHT = (
    "Portions Copyright 2021 The Hanken Grotesk Project Authors. "
    "Portions Copyright 2014-2021 Adobe, with Reserved Font Name 'Source'. "
    "Portions Copyright 2015 Google Inc. "
    "Portions Copyright 2022 Buernia, with Reserved Font Names 'Zhudou' and '煮豆'. "
    "Modifications copyright 2026 SilentPerson (Speechlessmanbilibili)."
)
LEGAL = {
    0: COPYRIGHT,
    7: "Source is a trademark of Adobe in the United States and/or other countries.",
    8: "SilentPerson (Speechlessmanbilibili)",
    9: "SilentPerson (font engineering and integration) with CJK Punct Bridge contributors",
    10: "CJK Punct Bridge ?! is a ligature variant of CJK Punct Bridge. "
        "Question/exclamation pairs form interrobangs (U+203D and a full-width form), enabled by default.",
    11: "https://github.com/Speechlessmanbilibili/CJK-Punct-Bridge",
    12: "https://github.com/Speechlessmanbilibili",
    13: "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
        "See the bundled OFL.txt and THIRD_PARTY_NOTICES.md for full terms and attribution.",
    14: "https://openfontlicense.org",
}


def setname(font, nid, val):
    nt = font["name"]
    nt.names = [r for r in nt.names if r.nameID != nid]
    nt.setName(val, nid, 3, 1, 0x409)
    try:
        val.encode("mac_roman")
        nt.setName(val, nid, 1, 0, 0)
    except Exception:
        pass


def set_names(font, weight, style):
    nt = font["name"]
    if ITALIC:
        sub = "Italic" if weight == 400 else f"{style} Italic"
        legacy_family = FAMILY if weight in (400, 700) else f"{FAMILY} {style}"
        legacy_sub = "Bold Italic" if weight == 700 else "Italic"
        full = (FAMILY if weight == 400 else f"{FAMILY} {style}") + " Italic"
        unique = f"{PS}-Italic" if weight == 400 else f"{PS}-{style}Italic"
    else:
        sub = "Bold" if weight == 700 else "Regular"
        legacy_family = FAMILY if weight in (400, 700) else f"{FAMILY} {style}"
        legacy_sub = sub
        full = FAMILY if weight == 400 else f"{FAMILY} {style}"
        unique = f"{PS}-{style}"
    vals = {**LEGAL,
            1: legacy_family, 2: sub, 3: f"1.000;SilentPerson;{unique}",
            4: full, 5: "Version 1.000", 6: unique,
            16: FAMILY, 17: (sub if ITALIC else style), 25: PS}
    for k, v in vals.items():
        setname(font, k, v)
    o = font["OS/2"]
    o.usWeightClass = weight
    o.achVendID = "    "
    fs = o.fsSelection
    for bit in (0, 5, 6, 9):
        fs &= ~(1 << bit)
    if ITALIC:
        fs |= 1 << 0
    if weight == 400:
        fs |= 1 << 6
    if weight == 700:
        fs |= 1 << 5
    o.fsSelection = fs
    font["head"].macStyle &= ~3
    if weight == 700:
        font["head"].macStyle |= 1
    if ITALIC:
        font["head"].macStyle |= 2
    font["head"].fontRevision = 1.0


def merge_glyphs(font, base, overlay, scale, dx, dy):
    gb = font["glyf"][base]
    go = font["glyf"][overlay]
    b_coords, b_endpts, b_flags = gb.getCoordinates(font["glyf"])
    o_coords, o_endpts, o_flags = go.getCoordinates(font["glyf"])
    if o_coords:
        xs = [p[0] for p in o_coords]
        ys = [p[1] for p in o_coords]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        new_o = [(dx + (x - cx) * scale, dy + (y - cy) * scale) for x, y in o_coords]
    else:
        new_o = []
    new_coords = list(b_coords) + new_o
    off = len(b_coords)
    new_endpts = list(b_endpts) + [off + e for e in o_endpts]
    new_flags = list(b_flags) + list(o_flags)
    g = Glyph()
    g.numberOfContours = len(new_endpts)
    g.coordinates = GlyphCoordinates(new_coords)
    g.endPtsOfContours = new_endpts
    g.flags = array("B", new_flags)
    g.program = ttProgram.Program()
    return g


def shear_glyph(font, name):
    g = font["glyf"][name]
    if g.numberOfContours > 0:
        coords = g.coordinates
        for i, (x, y) in enumerate(coords):
            coords[i] = (x + y * SLANT, y)
    g.recalcBounds(font["glyf"])
    adv = font["hmtx"].metrics[name][0]
    font["hmtx"].metrics[name] = (adv, getattr(g, "xMin", 0))


def import_interrobang(font):
    """从 Inter 提取 U+203D 字形（半宽）与全宽版（同轮廓，advance 1000 靠左）。

    全宽与半宽只差两侧留白，字形轮廓相同；全宽按中文全角惯例靠左，
    右侧留白。直接提取源字形坐标并缩放，不经过 pen（避免懒加载污染）。
    """
    from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
    if not INTER_VF.exists():
        raise SystemExit(f"缺少 Inter 源（U+203D 字形）: {INTER_VF}，请设置 INTER_VF")
    src = TTFont(INTER_VF)
    if "uni203D" not in src["glyf"]:
        raise SystemExit("Inter 源没有 U+203D 字形")
    scale = 1000 / src["head"].unitsPerEm
    g = src["glyf"]["uni203D"]
    coords, endpts, flags = g.getCoordinates(src["glyf"])
    new_coords = [(x * scale, y * scale) for x, y in coords]
    new = Glyph()
    new.numberOfContours = g.numberOfContours
    new.coordinates = GlyphCoordinates(new_coords)
    new.endPtsOfContours = list(endpts)
    new.flags = array("B", flags)
    new.program = ttProgram.Program()
    new.recalcBounds(font["glyf"])
    adv_half = int(src["hmtx"].metrics["uni203D"][0] * scale)
    xmin = getattr(new, "xMin", 0)
    font["glyf"]["interrobang.uni203D"] = new
    font["hmtx"].metrics["interrobang.uni203D"] = (adv_half, xmin)
    font["glyf"]["interrobang.full"] = deepcopy(new)
    font["hmtx"].metrics["interrobang.full"] = (1000, xmin)  # 全宽靠左
    for n in ("interrobang.uni203D", "interrobang.full"):
        if "vmtx" in font:
            font["vmtx"].metrics[n] = (1000, 0)
    src.close()
    return ["interrobang.uni203D", "interrobang.full"]


def build_weight(weight, style):
    src_path = STATIC_IN / (f"CJKPunctBridge-Italic.ttf" if (ITALIC and weight == 400) else
                            f"CJKPunctBridge-{style}{'Italic' if ITALIC else ''}.ttf")
    font = TTFont(src_path)
    glyf = font["glyf"]
    order = list(font.getGlyphOrder())

    new_names = import_interrobang(font)
    for name in new_names:
        order.append(name)
        if ITALIC:
            shear_glyph(font, name)
    font.setGlyphOrder(order)
    glyf.glyphOrder = order

    gsub = font["GSUB"].table

    def locl_variants(glyph):
        out = {glyph}
        for sr in gsub.ScriptList.ScriptRecord:
            for lr in sr.Script.LangSysRecord:
                for fi in lr.LangSys.FeatureIndex:
                    fr = gsub.FeatureList.FeatureRecord[fi]
                    if fr.FeatureTag != "locl":
                        continue
                    for li in fr.Feature.LookupListIndex:
                        lk = gsub.LookupList.Lookup[li]
                        for st in lk.SubTable:
                            typ = lk.LookupType
                            if typ == 7:
                                typ = st.ExtensionLookupType
                                st = st.ExtSubTable
                            if typ == 1 and hasattr(st, "mapping") and glyph in st.mapping:
                                out.add(st.mapping[glyph])
        return out

    q_variants = locl_variants("question")
    e_variants = locl_variants("exclam")
    liga_mapping = {}
    for q in q_variants:
        for e in e_variants:
            if q in order and e in order:
                liga_mapping[(q, e)] = "interrobang.uni203D"
                liga_mapping[(e, q)] = "interrobang.uni203D"
    liga_mapping[("uniFF1F", "uniFF01")] = "interrobang.full"
    liga_mapping[("uniFF01", "uniFF1F")] = "interrobang.full"

    st = buildLigatureSubstSubtable(liga_mapping)
    lk = buildLookup([st], table="GSUB")
    gsub.LookupList.Lookup.append(lk)
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)
    new_li = len(gsub.LookupList.Lookup) - 1
    attached = False
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == "liga":
            fr.Feature.LookupListIndex.insert(0, new_li)
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
            attached = True
    if not attached:
        # 桥接字体没有 liga feature（标点源只有 ccmp/dlig/locl/vert），
        # 新建一个并挂到所有语言系统。
        from fontTools.ttLib.tables import otTables
        fr = otTables.FeatureRecord()
        fr.FeatureTag = "liga"
        feat = otTables.Feature()
        feat.FeatureParams = None
        feat.LookupListIndex = [new_li]
        feat.LookupCount = 1
        fr.Feature = feat
        gsub.FeatureList.FeatureRecord.append(fr)
        gsub.FeatureList.FeatureCount = len(gsub.FeatureList.FeatureRecord)
        new_fi = len(gsub.FeatureList.FeatureRecord) - 1
        for sr in gsub.ScriptList.ScriptRecord:
            systems = []
            if sr.Script.DefaultLangSys is not None:
                systems.append(sr.Script.DefaultLangSys)
            systems.extend(lr.LangSys for lr in sr.Script.LangSysRecord)
            for ls in systems:
                ls.FeatureIndex.append(new_fi)
                ls.FeatureIndex.sort()
                ls.FeatureCount = len(ls.FeatureIndex)

    set_names(font, weight, style)
    try:
        buildStatTable(font, [dict(tag="wght", name="Weight",
                                   values=[dict(value=weight, name=style, flags=0x2 if weight == 400 else 0)])])
    except Exception:
        pass

    out = OUT / (f"{PS}-Italic.ttf" if (ITALIC and weight == 400) else f"{PS}-{style}{'Italic' if ITALIC else ''}.ttf")
    font.save(out, reorderTables=True)
    font.close()
    print(f"done {style}{' Italic' if ITALIC else ''} {out.stat().st_size/1048576:.2f} MiB", flush=True)
    return out


if __name__ == "__main__":
    only = os.environ.get("BRIDGE_ONLY_WEIGHT")
    selected = WEIGHTS if not only else {int(only): WEIGHTS[int(only)]}
    for w, s in selected.items():
        build_weight(w, s)
    print("CJK Punct Bridge ?! static build complete")
