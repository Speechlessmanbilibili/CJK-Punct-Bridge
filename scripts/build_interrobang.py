#!/usr/bin/env python3
"""Build the CJK Punct Bridge ?! static and variable families.

The base punctuation VF is instantiated at nine weights. Inter U+203D is
instantiated at the same weight for every master before varLib rebuilds the
output, preventing one default outline from being reused across the axis.
"""
from array import array
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import os

from fontTools.designspaceLib import (
    AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor,
)
from fontTools.misc.roundTools import otRound
from fontTools.otlLib.builder import (
    buildLigatureSubstSubtable, buildLookup, buildStatTable,
)
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.ttLib.tables import otTables
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont

from font_metadata import (
    COPYRIGHT, DESIGNER, TRADEMARK, apply_binary_metadata, project_names,
)

REPO = Path(__file__).resolve().parents[1]
ITALIC = os.environ.get("CJK_PUNCT_ITALIC") == "1"
BASE_DEFAULT = REPO / "fonts" / "variable" / (
    "CJKPunctBridge-Italic-Variable.ttf" if ITALIC else "CJKPunctBridge-Variable.ttf"
)
BASE_VF = Path(os.environ.get("CJK_PUNCT_BASE_VF", BASE_DEFAULT))
INTER_DEFAULT = REPO / "upstream" / (
    "InterVariable-Italic.ttf" if ITALIC else "InterVariable.ttf"
)
INTER_VF = Path(os.environ.get("INTER_VF", INTER_DEFAULT))
STATIC_OUT = REPO / "fonts-interrobang" / "static"
VARIABLE_OUT = REPO / "fonts-interrobang" / "variable"
WORK = REPO / "build" / "interrobang"
for directory in (STATIC_OUT, VARIABLE_OUT, WORK):
    directory.mkdir(parents=True, exist_ok=True)

FAMILY = "CJK Punct Bridge ?!"
PS = "CJKPunctBridgeInterrobang"
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
    0: COPYRIGHT + " Portions Copyright 2016 The Inter Project Authors.",
    7: TRADEMARK + " Inter UI and Inter is a trademark of rsms.",
    9: DESIGNER + "; Rasmus Andersson (Inter).",
    10: "CJK Punct Bridge ?! is the interrobang ligature variant of CJK Punct Bridge. "
        "Question mark + exclamation mark and their full-width forms use a "
        "weight-matched Inter U+203D outline.",
    11: "https://github.com/Speechlessmanbilibili/CJK-Punct-Bridge",
}
MAX_GLYPHS = 60_000
MAX_GVAR_BYTES = 64 * 1024 * 1024


def setname(table, name_id, value):
    table.names = [record for record in table.names if record.nameID != name_id]
    table.setName(value, name_id, 3, 1, 0x409)
    try:
        value.encode("mac_roman")
        table.setName(value, name_id, 1, 0, 0)
    except Exception:
        pass


def style_name(weight, style):
    if ITALIC:
        return "Italic" if weight == 400 else f"{style} Italic"
    return style


def static_path(weight, style):
    name = f"{PS}-Italic.ttf" if ITALIC and weight == 400 else (
        f"{PS}-{style}{'Italic' if ITALIC else ''}.ttf"
    )
    return STATIC_OUT / name


def set_static_names(font, weight, style):
    if ITALIC:
        typographic_sub = style_name(weight, style)
        legacy_family = FAMILY if weight in (400, 700) else f"{FAMILY} {style}"
        legacy_sub = "Bold Italic" if weight == 700 else "Italic"
        full = (FAMILY if weight == 400 else f"{FAMILY} {style}") + " Italic"
        unique = f"{PS}-Italic" if weight == 400 else f"{PS}-{style}Italic"
    else:
        typographic_sub = style
        legacy_family = FAMILY if weight in (400, 700) else f"{FAMILY} {style}"
        legacy_sub = "Bold" if weight == 700 else "Regular"
        full = FAMILY if weight == 400 else f"{FAMILY} {style}"
        unique = f"{PS}-{style}"
    values = {
        **project_names(unique), **INTER_LEGAL,
        1: legacy_family, 2: legacy_sub, 4: full, 6: unique,
        16: FAMILY, 17: typographic_sub, 25: PS,
    }
    for name_id, value in values.items():
        setname(font["name"], name_id, value)
    apply_binary_metadata(font)
    os2 = font["OS/2"]
    os2.usWeightClass = weight
    for bit in (0, 5, 6, 9):
        os2.fsSelection &= ~(1 << bit)
    if ITALIC:
        os2.fsSelection |= 1 << 0
    if weight == 400 and not ITALIC:
        os2.fsSelection |= 1 << 6
    if weight == 700:
        os2.fsSelection |= 1 << 5
    font["head"].macStyle &= ~3
    if weight == 700:
        font["head"].macStyle |= 1
    if ITALIC:
        font["head"].macStyle |= 2


def set_variable_names(font):
    sub = "Italic" if ITALIC else "Regular"
    unique = f"{PS}-Italic-VF" if ITALIC else f"{PS}-VF"
    values = {
        **project_names(unique), **INTER_LEGAL,
        1: FAMILY, 2: sub, 4: FAMILY + (" Italic" if ITALIC else ""),
        6: f"{PS}{'-Italic' if ITALIC else ''}",
        16: FAMILY, 17: sub, 25: PS,
    }
    for name_id, value in values.items():
        setname(font["name"], name_id, value)
    apply_binary_metadata(font)
    os2 = font["OS/2"]
    os2.usWeightClass = 400
    for bit in (0, 5, 6, 9):
        os2.fsSelection &= ~(1 << bit)
    if not ITALIC:
        os2.fsSelection |= 1 << 6
    if ITALIC:
        os2.fsSelection |= 1 << 0
    font["head"].macStyle &= ~3
    if ITALIC:
        font["head"].macStyle |= 2


def validate_inputs():
    if not BASE_VF.exists():
        raise SystemExit(f"Missing base CJK Punct Bridge VF: {BASE_VF}")
    if not INTER_VF.exists():
        raise SystemExit(f"Missing Inter VF: {INTER_VF}; set INTER_VF")
    digest = sha256(INTER_VF.read_bytes()).hexdigest()
    if digest != INTER_SHA256[ITALIC]:
        raise SystemExit(
            f"Inter SHA-256 mismatch: {digest}\nexpected: {INTER_SHA256[ITALIC]}\n{INTER_VF}"
        )
    for path, needs_opsz in ((BASE_VF, False), (INTER_VF, True)):
        font = TTFont(path, lazy=True)
        axes = {axis.axisTag: (axis.minValue, axis.defaultValue, axis.maxValue)
                for axis in font["fvar"].axes}
        if axes.get("wght") != (100.0, 400.0, 900.0):
            raise SystemExit(f"Unexpected wght axis in {path}: {axes}")
        if needs_opsz and "opsz" not in axes:
            raise SystemExit(f"Missing Inter opsz axis: {path}")
        if needs_opsz and 0x203D not in font.getBestCmap():
            raise SystemExit(f"Inter source has no U+203D: {path}")
        font.close()
    print(f"verified Inter source {INTER_VF.name} {digest}", flush=True)


def import_interrobang(font, weight):
    variable = TTFont(INTER_VF)
    source = instantiateVariableFont(
        variable, {"opsz": 14, "wght": weight},
        inplace=False, optimize=True, static=True,
    )
    variable.close()
    glyph_name = source.getBestCmap()[0x203D]
    glyph = source["glyf"][glyph_name]
    coords, end_points, flags = glyph.getCoordinates(source["glyf"])
    scale = 1000 / source["head"].unitsPerEm
    imported = Glyph()
    imported.numberOfContours = glyph.numberOfContours
    imported.coordinates = GlyphCoordinates([
        (otRound(x * scale), otRound(y * scale)) for x, y in coords
    ])
    imported.endPtsOfContours = list(end_points)
    imported.flags = array("B", flags)
    imported.program = ttProgram.Program()
    imported.recalcBounds(font["glyf"])
    advance = otRound(source["hmtx"].metrics[glyph_name][0] * scale)
    lsb = imported.xMin
    font["glyf"]["interrobang.uni203D"] = imported
    font["hmtx"].metrics["interrobang.uni203D"] = (advance, lsb)
    font["glyf"]["interrobang.full"] = deepcopy(imported)
    font["hmtx"].metrics["interrobang.full"] = (1000, lsb)
    if "vmtx" in font:
        font["vmtx"].metrics["interrobang.uni203D"] = (1000, 0)
        font["vmtx"].metrics["interrobang.full"] = (1000, 0)
    source.close()


def locl_variants(font, glyph_name):
    table = font["GSUB"].table
    variants = {glyph_name}
    language_systems = []
    for script_record in table.ScriptList.ScriptRecord:
        if script_record.Script.DefaultLangSys is not None:
            language_systems.append(script_record.Script.DefaultLangSys)
        language_systems.extend(
            record.LangSys for record in script_record.Script.LangSysRecord
        )
    for language_system in language_systems:
        for feature_index in language_system.FeatureIndex:
            feature = table.FeatureList.FeatureRecord[feature_index]
            if feature.FeatureTag != "locl":
                continue
            for lookup_index in feature.Feature.LookupListIndex:
                lookup = table.LookupList.Lookup[lookup_index]
                for subtable in lookup.SubTable:
                    lookup_type = lookup.LookupType
                    if lookup_type == 7:
                        lookup_type = subtable.ExtensionLookupType
                        subtable = subtable.ExtSubTable
                    if lookup_type == 1 and hasattr(subtable, "mapping"):
                        if glyph_name in subtable.mapping:
                            variants.add(subtable.mapping[glyph_name])
    return variants


def add_ligatures(font):
    cmap = font.getBestCmap()
    question_variants = locl_variants(font, cmap[0x003F])
    exclam_variants = locl_variants(font, cmap[0x0021])
    mapping = {}
    glyph_order = set(font.getGlyphOrder())
    for question in question_variants:
        for exclam in exclam_variants:
            if question in glyph_order and exclam in glyph_order:
                mapping[(question, exclam)] = "interrobang.uni203D"
                mapping[(exclam, question)] = "interrobang.uni203D"
    mapping[(cmap[0xFF1F], cmap[0xFF01])] = "interrobang.full"
    mapping[(cmap[0xFF01], cmap[0xFF1F])] = "interrobang.full"
    lookup = buildLookup([buildLigatureSubstSubtable(mapping)], table="GSUB")
    table = font["GSUB"].table
    table.LookupList.Lookup.append(lookup)
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    lookup_index = len(table.LookupList.Lookup) - 1
    attached = 0
    for feature in table.FeatureList.FeatureRecord:
        if feature.FeatureTag == "liga":
            feature.Feature.LookupListIndex.insert(0, lookup_index)
            feature.Feature.LookupCount = len(feature.Feature.LookupListIndex)
            attached += 1
    if not attached:
        record = otTables.FeatureRecord()
        record.FeatureTag = "liga"
        record.Feature = otTables.Feature()
        record.Feature.FeatureParams = None
        record.Feature.LookupListIndex = [lookup_index]
        record.Feature.LookupCount = 1
        table.FeatureList.FeatureRecord.append(record)
        table.FeatureList.FeatureCount = len(table.FeatureList.FeatureRecord)
        old_index = len(table.FeatureList.FeatureRecord) - 1
        language_systems = []
        for script_record in table.ScriptList.ScriptRecord:
            if script_record.Script.DefaultLangSys is not None:
                language_systems.append(script_record.Script.DefaultLangSys)
            language_systems.extend(
                item.LangSys for item in script_record.Script.LangSysRecord
            )
        for language_system in language_systems:
            language_system.FeatureIndex.append(old_index)
            language_system.FeatureCount = len(language_system.FeatureIndex)

        indexed = list(enumerate(table.FeatureList.FeatureRecord))
        indexed.sort(key=lambda item: item[1].FeatureTag)
        remap = {old: new for new, (old, _) in enumerate(indexed)}
        table.FeatureList.FeatureRecord = [record for _, record in indexed]
        for language_system in language_systems:
            language_system.FeatureIndex = sorted(
                remap[index] for index in language_system.FeatureIndex
            )
            if language_system.ReqFeatureIndex != 0xFFFF:
                language_system.ReqFeatureIndex = remap[language_system.ReqFeatureIndex]


def glyph_signature(font, glyph_name):
    glyph = font["glyf"][glyph_name]
    coords, end_points, flags = glyph.getCoordinates(font["glyf"])
    return (
        tuple(coords), tuple(end_points), bytes(flags),
        font["hmtx"].metrics[glyph_name],
    )


def interrobang_targets(font):
    cmap = font.getBestCmap()
    pairs = ((cmap[0x003F], cmap[0x0021]), (cmap[0xFF1F], cmap[0xFF01]))
    targets = []
    for first, second in pairs:
        target = None
        for lookup in reversed(font["GSUB"].table.LookupList.Lookup):
            for subtable in lookup.SubTable:
                lookup_type = lookup.LookupType
                if lookup_type == 7:
                    lookup_type = subtable.ExtensionLookupType
                    subtable = subtable.ExtSubTable
                if lookup_type != 4 or not hasattr(subtable, "ligatures"):
                    continue
                for ligature in subtable.ligatures.get(first, []):
                    if ligature.Component == [second]:
                        target = ligature.LigGlyph
                        break
                if target is not None:
                    break
            if target is not None:
                break
        if target is None:
            raise AssertionError((first, second, "missing interrobang ligature"))
        targets.append(target)
    return tuple(targets)


def build_static_masters():
    paths = {}
    for weight, style in WEIGHTS.items():
        variable = TTFont(BASE_VF)
        font = instantiateVariableFont(
            variable, {"wght": weight}, inplace=False, optimize=True, static=True
        )
        variable.close()
        import_interrobang(font, weight)
        glyph_order = list(font["glyf"].glyphs)
        font.setGlyphOrder(glyph_order)
        font["glyf"].glyphOrder = glyph_order
        add_ligatures(font)
        set_static_names(font, weight, style)
        try:
            buildStatTable(font, [dict(
                tag="wght", name="Weight",
                values=[dict(value=weight, name=style, flags=0x2 if weight == 400 else 0)],
            )])
        except Exception as error:
            print("STAT warning", error, flush=True)
        output = static_path(weight, style)
        font.save(output, reorderTables=True)
        font.close()
        paths[weight] = output
        print(f"saved {output.name} {output.stat().st_size / 1048576:.2f} MiB", flush=True)
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
    for weight, style in WEIGHTS.items():
        current_style = style_name(weight, style)
        source = SourceDescriptor()
        source.path = str(paths[weight])
        source.name = f"master.{weight}"
        source.familyName = FAMILY
        source.styleName = current_style
        source.location = {"Weight": weight}
        if weight == 400:
            source.copyInfo = True
            source.copyLib = True
            source.copyGroups = True
            source.copyFeatures = True
        designspace.addSource(source)
        instance = InstanceDescriptor()
        instance.name = current_style
        instance.familyName = FAMILY
        instance.styleName = current_style
        instance.location = {"Weight": weight}
        designspace.addInstance(instance)
    designspace_path = WORK / f"{PS}{'-Italic' if ITALIC else ''}.designspace"
    designspace.write(designspace_path)
    variable, _, _ = varlib_build(
        str(designspace_path), exclude=["BASE", "GDEF", "GPOS", "GSUB"]
    )
    regular = TTFont(paths[400])
    for tag in ("GDEF", "GPOS", "GSUB", "prep"):
        if tag in regular:
            variable[tag] = deepcopy(regular[tag])
    regular.close()
    set_variable_names(variable)
    names = variable["name"]
    style_names = [style_name(weight, style) for weight, style in WEIGHTS.items()]
    for instance, current_style in zip(variable["fvar"].instances, style_names):
        instance.subfamilyNameID = names.addName(
            current_style, platforms=((3, 1, 0x409), (1, 0, 0))
        )
    stat_axes = [dict(tag="wght", name="Weight", values=[
        dict(value=weight, name=current_style, flags=0x2 if weight == 400 else 0)
        for (weight, _), current_style in zip(WEIGHTS.items(), style_names)
    ])]
    if ITALIC:
        stat_axes.append(dict(
            tag="ital", name="Italic", values=[dict(value=1, name="Italic")]
        ))
    buildStatTable(variable, stat_axes)
    output = VARIABLE_OUT / f"{PS}{'-Italic' if ITALIC else ''}-Variable.ttf"
    variable.save(output, reorderTables=True)
    variable.close()
    return output


def validate_output(output, paths):
    variable = TTFont(output)
    axis = next(item for item in variable["fvar"].axes if item.axisTag == "wght")
    assert (axis.minValue, axis.defaultValue, axis.maxValue) == (100.0, 400.0, 900.0)
    assert len(variable["fvar"].instances) == 9
    glyph_count = variable["maxp"].numGlyphs
    gvar_bytes = variable.reader.tables["gvar"].length
    assert glyph_count < MAX_GLYPHS, ("glyph guard", glyph_count, MAX_GLYPHS)
    assert gvar_bytes < MAX_GVAR_BYTES, ("gvar guard", gvar_bytes, MAX_GVAR_BYTES)
    signatures = []
    for weight in WEIGHTS:
        static = TTFont(paths[weight])
        half_static, full_static = interrobang_targets(static)
        signatures.append(glyph_signature(static, half_static))
        if weight in (100, 400, 900):
            instance = instantiateVariableFont(
                variable, {"wght": weight}, inplace=False, optimize=True, static=True
            )
            half_instance, full_instance = interrobang_targets(instance)
            for variable_name, static_name in (
                (half_instance, half_static), (full_instance, full_static),
            ):
                assert glyph_signature(instance, variable_name) == glyph_signature(static, static_name), (
                    weight, variable_name, "variable/static mismatch"
                )
            instance.close()
        static.close()
    assert len(set(signatures)) == len(WEIGHTS), "Inter U+203D does not vary by weight"
    variable.close()
    print(
        f"validated {output.name}: 9 distinct interrobang weights; "
        f"glyphs={glyph_count}; gvar={gvar_bytes} bytes",
        flush=True,
    )


def main():
    validate_inputs()
    paths = build_static_masters()
    output = build_variable(paths)
    validate_output(output, paths)


if __name__ == "__main__":
    main()
