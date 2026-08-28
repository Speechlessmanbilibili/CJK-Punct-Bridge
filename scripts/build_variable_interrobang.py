#!/usr/bin/env python3
"""CJK Punct Bridge ?! 可变字体构建：从 fonts-interrobang/static 的 9 个静态 master 构建。

用法：
    python scripts/build_variable_interrobang.py              # 正体 VF
    CJK_PUNCT_ITALIC=1 python scripts/build_variable_interrobang.py  # 斜体 VF
"""
from copy import deepcopy
from pathlib import Path
import os
from fontTools.designspaceLib import (
    AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor,
)
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont
from font_metadata import apply_binary_metadata, project_names
from build_interrobang import INTER_LEGAL

REPO = Path(__file__).resolve().parents[1]
STATIC = REPO / "fonts-interrobang" / "static"
OUT = REPO / "fonts-interrobang" / "variable"
WEB_OUT = REPO / "fonts-interrobang" / "web"
WORK = REPO / "build" / "interrobang-vf"
OUT.mkdir(parents=True, exist_ok=True)
WEB_OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)

FAMILY = "CJK Punct Bridge ?!"
PS = "CJKPunctBridgeInterrobang"
ITALIC = os.environ.get("CJK_PUNCT_ITALIC") == "1"
WEIGHTS = {
    100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
    500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
    900: "Black",
}


def setname(table, name_id, value):
    table.names = [r for r in table.names if r.nameID != name_id]
    table.setName(value, name_id, 3, 1, 0x409)
    try:
        value.encode("mac_roman")
        table.setName(value, name_id, 1, 0, 0)
    except Exception:
        pass


def set_names(font):
    names = font["name"]
    sub = "Italic" if ITALIC else "Regular"
    unique = f"{PS}-Italic-VF" if ITALIC else f"{PS}-VF"
    values = {
        **project_names(unique),
        **INTER_LEGAL,
        1: FAMILY, 2: sub, 4: FAMILY + (f" {sub}" if ITALIC else ""),
        6: f"{PS}{'-Italic' if ITALIC else ''}", 16: FAMILY, 17: sub, 25: PS,
    }
    for nid, val in values.items():
        setname(names, nid, val)
    apply_binary_metadata(font)
    os2 = font["OS/2"]
    os2.usWeightClass = 400
    for bit in (0, 5, 6, 9):
        os2.fsSelection &= ~(1 << bit)
    if ITALIC:
        os2.fsSelection |= 1 << 0
    else:
        os2.fsSelection |= 1 << 6
    font["head"].macStyle &= ~3
    if ITALIC:
        font["head"].macStyle |= 2


def style_names():
    return [
        ("Italic" if (ITALIC and weight == 400) else style + (" Italic" if ITALIC else ""))
        for weight, style in WEIGHTS.items()
    ]


def validate_literal_mapping(output, paths):
    variable = TTFont(output)
    signatures = []
    for weight, path in paths.items():
        static = TTFont(path)
        static_glyph = static.getBestCmap().get(0x203D)
        assert static_glyph == "interrobang.uni203D", (weight, "static U+203D cmap mismatch")
        signatures.append(static["hmtx"].metrics[static_glyph])
        if weight in (100, 400, 900):
            instance = instantiateVariableFont(
                variable, {"wght": weight}, inplace=False, optimize=True, static=True
            )
            assert instance.getBestCmap().get(0x203D) == static_glyph, (
                weight, "variable instance U+203D cmap mismatch"
            )
            instance.close()
        static.close()
    assert len(set(signatures)) > 1, "U+203D metrics do not vary across weights"
    variable.close()


def main():
    paths = {
        weight: STATIC / (f"{PS}-Italic.ttf" if (ITALIC and weight == 400) else f"{PS}-{style}{'Italic' if ITALIC else ''}.ttf")
        for weight, style in WEIGHTS.items()
    }
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise SystemExit("Missing static masters:\n" + "\n".join(missing))

    orders = []
    for path in paths.values():
        font = TTFont(path, lazy=True)
        orders.append(font.getGlyphOrder())
        font.close()
    if not all(o == orders[0] for o in orders[1:]):
        raise SystemExit("Static master glyph orders differ")

    ds = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.name = "Weight"
    axis.tag = "wght"
    axis.minimum = 100
    axis.default = 400
    axis.maximum = 900
    ds.addAxis(axis)
    for (weight, style), style_name in zip(WEIGHTS.items(), style_names()):
        src = SourceDescriptor()
        src.path = str(paths[weight])
        src.name = f"master.{weight}"
        src.familyName = FAMILY
        src.styleName = style_name
        src.location = {"Weight": weight}
        if weight == 400:
            src.copyInfo = True
            src.copyLib = True
            src.copyGroups = True
            src.copyFeatures = True
        ds.addSource(src)
        ins = InstanceDescriptor()
        ins.name = style_name
        ins.familyName = FAMILY
        ins.styleName = style_name
        ins.location = {"Weight": weight}
        ds.addInstance(ins)
    dsp = WORK / f"{PS}{'-Italic' if ITALIC else ''}.designspace"
    ds.write(dsp)

    variable, _, _ = varlib_build(str(dsp), exclude=["BASE", "GDEF", "GPOS", "GSUB"])
    reg = TTFont(paths[400])
    for tag in ("GDEF", "GPOS", "GSUB", "prep"):
        if tag in reg:
            table = deepcopy(reg[tag])
            if hasattr(table, "VarStore") and table.VarStore is not None:
                table.VarStore = None
            variable[tag] = table
    reg.close()

    set_names(variable)
    names = variable["name"]
    for inst, style_name in zip(variable["fvar"].instances, style_names()):
        inst.subfamilyNameID = names.addName(style_name, platforms=((3, 1, 0x409), (1, 0, 0)))
    stat_values = [dict(tag="wght", name="Weight", values=[
        dict(value=w, name=n, flags=0x2 if w == 400 else 0)
        for (w, s), n in zip(WEIGHTS.items(), style_names())
    ])]
    if ITALIC:
        stat_values.append(dict(tag="ital", name="Italic", values=[dict(value=1, name="Italic")]))
    try:
        buildStatTable(variable, stat_values)
    except Exception as e:
        print("STAT warning", e, flush=True)

    output = OUT / f"{PS}{'-Italic' if ITALIC else ''}-Variable.ttf"
    variable.save(output, reorderTables=True)
    variable.flavor = "woff2"
    variable.save(WEB_OUT / output.with_suffix(".woff2").name, reorderTables=True)
    variable.close()
    print("saved", output, output.stat().st_size / 1048576, "MiB", flush=True)
    validate_literal_mapping(output, paths)


if __name__ == "__main__":
    main()
