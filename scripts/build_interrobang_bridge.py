#!/usr/bin/env python3
"""Build the Interrobang Bridge Western companion family from pinned Inter VFs.

The font intentionally encodes only U+0021, U+003F, and U+203D. Its default
liga feature maps ?! and !? to the encoded interrobang glyph. Upright and italic
passes each emit nine static weights plus one wght variable font.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import os

from fontTools.designspaceLib import (
    AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor,
)
from fontTools.otlLib.builder import buildLigatureSubstSubtable, buildLookup, buildStatTable
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont

from font_metadata import apply_binary_metadata, project_names

REPO = Path(__file__).resolve().parents[1]
ITALIC = os.environ.get("INTERROBANG_BRIDGE_ITALIC") == "1"
INTER_DEFAULT = REPO / "upstream" / (
    "InterVariable-Italic.ttf" if ITALIC else "InterVariable.ttf"
)
INTER_VF = Path(os.environ.get("INTER_VF", INTER_DEFAULT))
STATIC_OUT = REPO / "fonts-interrobang-bridge" / "static"
VARIABLE_OUT = REPO / "fonts-interrobang-bridge" / "variable"
WEB_OUT = REPO / "fonts-interrobang-bridge" / "web"
WORK = REPO / "build" / "interrobang-bridge"
for directory in (STATIC_OUT, VARIABLE_OUT, WEB_OUT, WORK):
    directory.mkdir(parents=True, exist_ok=True)

FAMILY = "Interrobang Bridge"
PS = "InterrobangBridge"
CODEPOINTS = (0x0021, 0x003F, 0x203D)
WEIGHTS = {
    100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
    500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
    900: "Black",
}
INTER_SHA256 = {
    False: "4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf",
    True: "d6f1f6a172d9e588438db9f986fd5cfad7b30f644374080a8a9d4d91e344586f",
}
INTER_LEGAL = {
    0: "Copyright 2016 The Inter Project Authors. Modifications copyright 2026 SilentPerson (Speechlessmanbilibili).",
    7: "Inter UI and Inter is a trademark of rsms.",
    8: "SilentPerson (Speechlessmanbilibili)",
    9: "Rasmus Andersson (Inter); SilentPerson (subset and OpenType engineering).",
    10: "Minimal Western companion font: Inter question mark, exclamation mark, and interrobang; ?! and !? ligate to U+203D by default.",
    11: "https://github.com/Speechlessmanbilibili/CJK-Punct-Bridge",
    12: "https://github.com/Speechlessmanbilibili",
    13: "This Font Software is licensed under the SIL Open Font License, Version 1.1. See OFL.txt.",
    14: "https://openfontlicense.org",
}


def setname(font, name_id, value):
    table = font["name"]
    table.names = [record for record in table.names if record.nameID != name_id]
    table.setName(value, name_id, 3, 1, 0x409)
    try:
        value.encode("mac_roman")
        table.setName(value, name_id, 1, 0, 0)
    except UnicodeEncodeError:
        pass


def style_name(weight, style):
    return ("Italic" if weight == 400 else f"{style} Italic") if ITALIC else style


def static_path(weight, style):
    suffix = "Italic" if ITALIC else ""
    name = f"{PS}-Italic.ttf" if ITALIC and weight == 400 else f"{PS}-{style}{suffix}.ttf"
    return STATIC_OUT / name


def set_names(font, weight=None):
    variable = weight is None
    current_weight = 400 if variable else weight
    style = WEIGHTS[current_weight]
    typographic_sub = "Italic" if variable and ITALIC else (
        "Regular" if variable else style_name(current_weight, style)
    )
    if variable:
        legacy_family = FAMILY
        legacy_sub = "Italic" if ITALIC else "Regular"
        full = FAMILY + (" Italic" if ITALIC else "")
        unique = f"{PS}-Italic-VF" if ITALIC else f"{PS}-VF"
        postscript = f"{PS}-Italic" if ITALIC else PS
    elif ITALIC:
        legacy_family = FAMILY if current_weight in (400, 700) else f"{FAMILY} {style}"
        legacy_sub = "Bold Italic" if current_weight == 700 else "Italic"
        full = (FAMILY if current_weight == 400 else f"{FAMILY} {style}") + " Italic"
        unique = f"{PS}-Italic" if current_weight == 400 else f"{PS}-{style}Italic"
        postscript = unique
    else:
        legacy_family = FAMILY if current_weight in (400, 700) else f"{FAMILY} {style}"
        legacy_sub = "Bold" if current_weight == 700 else "Regular"
        full = FAMILY if current_weight == 400 else f"{FAMILY} {style}"
        unique = f"{PS}-{style}"
        postscript = unique
    values = {
        **project_names(unique), **INTER_LEGAL,
        1: legacy_family, 2: legacy_sub, 4: full, 6: postscript,
        16: FAMILY, 17: typographic_sub, 25: PS,
    }
    for name_id, value in values.items():
        setname(font, name_id, value)
    apply_binary_metadata(font)
    os2 = font["OS/2"]
    os2.usWeightClass = current_weight
    for bit in (0, 5, 6, 9):
        os2.fsSelection &= ~(1 << bit)
    if ITALIC:
        os2.fsSelection |= 1 << 0
    if current_weight == 400 and not ITALIC:
        os2.fsSelection |= 1 << 6
    if current_weight == 700 and not variable:
        os2.fsSelection |= 1 << 5
    font["head"].macStyle &= ~3
    if current_weight == 700 and not variable:
        font["head"].macStyle |= 1
    if ITALIC:
        font["head"].macStyle |= 2


def validate_source():
    if not INTER_VF.exists():
        raise SystemExit(f"Missing Inter source: {INTER_VF}")
    digest = sha256(INTER_VF.read_bytes()).hexdigest()
    if digest != INTER_SHA256[ITALIC]:
        raise SystemExit(f"Inter SHA-256 mismatch: {digest}\nexpected: {INTER_SHA256[ITALIC]}")
    font = TTFont(INTER_VF, lazy=True)
    cmap = font.getBestCmap()
    assert set(CODEPOINTS) <= set(cmap)
    axes = {axis.axisTag: (axis.minValue, axis.defaultValue, axis.maxValue) for axis in font["fvar"].axes}
    assert axes.get("wght") == (100.0, 400.0, 900.0)
    assert "opsz" in axes
    font.close()
    print(f"verified {INTER_VF.name} {digest}", flush=True)


def subset_characters(font):
    options = Options()
    options.layout_features = []
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 25]
    options.name_languages = [0x409]
    options.recalc_average_width = True
    subsetter = Subsetter(options=options)
    subsetter.populate(unicodes=CODEPOINTS)
    subsetter.subset(font)


def add_ligatures(font):
    cmap = font.getBestCmap()
    mapping = {
        (cmap[0x003F], cmap[0x0021]): cmap[0x203D],
        (cmap[0x0021], cmap[0x003F]): cmap[0x203D],
    }
    lookup = buildLookup([buildLigatureSubstSubtable(mapping)], table="GSUB")
    gsub = otTables.GSUB()
    gsub.Version = 0x00010000
    gsub.ScriptList = otTables.ScriptList()
    script_record = otTables.ScriptRecord()
    script_record.ScriptTag = "DFLT"
    script_record.Script = otTables.Script()
    script_record.Script.DefaultLangSys = otTables.LangSys()
    script_record.Script.DefaultLangSys.LookupOrder = None
    script_record.Script.DefaultLangSys.ReqFeatureIndex = 0xFFFF
    script_record.Script.DefaultLangSys.FeatureIndex = [0]
    script_record.Script.DefaultLangSys.FeatureCount = 1
    script_record.Script.LangSysRecord = []
    script_record.Script.LangSysCount = 0
    gsub.ScriptList.ScriptRecord = [script_record]
    gsub.ScriptList.ScriptCount = 1
    gsub.FeatureList = otTables.FeatureList()
    feature_record = otTables.FeatureRecord()
    feature_record.FeatureTag = "liga"
    feature_record.Feature = otTables.Feature()
    feature_record.Feature.FeatureParams = None
    feature_record.Feature.LookupListIndex = [0]
    feature_record.Feature.LookupCount = 1
    gsub.FeatureList.FeatureRecord = [feature_record]
    gsub.FeatureList.FeatureCount = 1
    gsub.LookupList = otTables.LookupList()
    gsub.LookupList.Lookup = [lookup]
    gsub.LookupList.LookupCount = 1
    from fontTools.ttLib import newTable
    font["GSUB"] = newTable("GSUB")
    font["GSUB"].table = gsub


def build_static():
    paths = {}
    for weight, style in WEIGHTS.items():
        variable = TTFont(INTER_VF)
        font = instantiateVariableFont(
            variable, {"opsz": 14, "wght": weight}, inplace=False, optimize=True, static=True
        )
        variable.close()
        subset_characters(font)
        add_ligatures(font)
        set_names(font, weight)
        buildStatTable(font, [dict(
            tag="wght", name="Weight",
            values=[dict(value=weight, name=style, flags=0x2 if weight == 400 else 0)],
        )])
        output = static_path(weight, style)
        font.save(output, reorderTables=True)
        font.flavor = "woff2"
        font.save(WEB_OUT / output.with_suffix(".woff2").name, reorderTables=True)
        font.close()
        paths[weight] = output
        print(f"saved {output.name}", flush=True)
    return paths


def build_variable(paths):
    designspace = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.name = "Weight"
    axis.tag = "wght"
    axis.minimum = 100
    axis.default = 400
    axis.maximum = 900
    designspace.addAxis(axis)
    styles = [style_name(weight, style) for weight, style in WEIGHTS.items()]
    for (weight, _), current_style in zip(WEIGHTS.items(), styles):
        source = SourceDescriptor()
        source.path = str(paths[weight])
        source.name = f"master.{weight}"
        source.familyName = FAMILY
        source.styleName = current_style
        source.location = {"Weight": weight}
        if weight == 400:
            source.copyInfo = source.copyLib = source.copyGroups = source.copyFeatures = True
        designspace.addSource(source)
        instance = InstanceDescriptor()
        instance.name = current_style
        instance.familyName = FAMILY
        instance.styleName = current_style
        instance.location = {"Weight": weight}
        designspace.addInstance(instance)
    designspace_path = WORK / f"{PS}{'-Italic' if ITALIC else ''}.designspace"
    designspace.write(designspace_path)
    variable, _, _ = varlib_build(str(designspace_path), exclude=["GDEF", "GPOS", "GSUB"])
    regular = TTFont(paths[400])
    for tag in ("GDEF", "GPOS", "GSUB", "prep"):
        if tag in regular:
            variable[tag] = deepcopy(regular[tag])
    regular.close()
    set_names(variable)
    names = variable["name"]
    for instance, current_style in zip(variable["fvar"].instances, styles):
        instance.subfamilyNameID = names.addName(current_style, platforms=((3, 1, 0x409), (1, 0, 0)))
    axes = [dict(tag="wght", name="Weight", values=[
        dict(value=weight, name=current_style, flags=0x2 if weight == 400 else 0)
        for (weight, _), current_style in zip(WEIGHTS.items(), styles)
    ])]
    if ITALIC:
        axes.append(dict(tag="ital", name="Italic", values=[dict(value=1, name="Italic")]))
    buildStatTable(variable, axes)
    output = VARIABLE_OUT / f"{PS}{'-Italic' if ITALIC else ''}-Variable.ttf"
    variable.save(output, reorderTables=True)
    variable.flavor = "woff2"
    variable.save(WEB_OUT / output.with_suffix(".woff2").name, reorderTables=True)
    variable.close()
    print(f"saved {output.name}", flush=True)
    return output


def ligature_target(font, first, second):
    cmap = font.getBestCmap()
    lookup = font["GSUB"].table.LookupList.Lookup[0]
    for ligature in lookup.SubTable[0].ligatures[cmap[first]]:
        if ligature.Component == [cmap[second]]:
            return ligature.LigGlyph
    raise AssertionError((first, second, "missing liga"))


def glyph_signature(font, glyph_name):
    glyph = font["glyf"][glyph_name]
    coordinates, end_points, flags = glyph.getCoordinates(font["glyf"])
    return tuple(coordinates), tuple(end_points), bytes(flags), font["hmtx"].metrics[glyph_name]


def validate(output, paths):
    variable = TTFont(output)
    axis = next(axis for axis in variable["fvar"].axes if axis.axisTag == "wght")
    assert (axis.minValue, axis.defaultValue, axis.maxValue) == (100.0, 400.0, 900.0)
    assert len(variable["fvar"].instances) == 9
    signatures = []
    for weight, path in paths.items():
        static = TTFont(path)
        assert set(static.getBestCmap()) == set(CODEPOINTS)
        literal = static.getBestCmap()[0x203D]
        assert ligature_target(static, 0x003F, 0x0021) == literal
        assert ligature_target(static, 0x0021, 0x003F) == literal
        signatures.append(glyph_signature(static, literal))
        if weight in (100, 400, 900):
            instance = instantiateVariableFont(variable, {"wght": weight}, inplace=False, optimize=True, static=True)
            assert set(instance.getBestCmap()) == set(CODEPOINTS)
            assert glyph_signature(instance, instance.getBestCmap()[0x203D]) == glyph_signature(static, literal)
            instance.close()
        static.close()
    assert len(set(signatures)) == len(WEIGHTS), "Interrobang outline does not vary across weights"
    variable.close()
    print(f"validated {output.name}: cmap=3; 9 distinct Inter weights", flush=True)


def main():
    validate_source()
    paths = build_static()
    output = build_variable(paths)
    validate(output, paths)


if __name__ == "__main__":
    main()
