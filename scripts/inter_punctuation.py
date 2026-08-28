"""Inter-sourced punctuation and contextual two-slot pair substitutions."""
from array import array
from copy import deepcopy

from fontTools.misc.roundTools import otRound
from fontTools.otlLib.builder import (
    buildCoverage,
    buildLookup,
    buildSingleSubstSubtable,
)
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables, ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.varLib.instancer import instantiateVariableFont

HALF_SOURCE = {0x0021: 0x0021, 0x003F: 0x003F, 0x00A1: 0x00A1, 0x00BF: 0x00BF}
FULL_SOURCE = {0xFF01: 0x0021, 0xFF1F: 0x003F}


def _unicode_tables(font):
    return [table for table in font["cmap"].tables if table.isUnicode()]


def _locl_variants(font, glyph_name):
    variants = {glyph_name}
    if "GSUB" not in font:
        return variants
    table = font["GSUB"].table
    mappings = []
    for script_record in table.ScriptList.ScriptRecord:
        systems = []
        if script_record.Script.DefaultLangSys is not None:
            systems.append(script_record.Script.DefaultLangSys)
        systems.extend(record.LangSys for record in script_record.Script.LangSysRecord)
        for system in systems:
            for feature_index in system.FeatureIndex:
                feature = table.FeatureList.FeatureRecord[feature_index]
                if feature.FeatureTag not in {"locl", "vert", "vrt2", "fwid", "hwid", "pwid"}:
                    continue
                for lookup_index in feature.Feature.LookupListIndex:
                    lookup = table.LookupList.Lookup[lookup_index]
                    for subtable in lookup.SubTable:
                        lookup_type = lookup.LookupType
                        if lookup_type == 7:
                            lookup_type = subtable.ExtensionLookupType
                            subtable = subtable.ExtSubTable
                        if lookup_type == 1 and hasattr(subtable, "mapping"):
                            mappings.append(subtable.mapping)
    changed = True
    while changed:
        changed = False
        for mapping in mappings:
            for current in tuple(variants):
                target = mapping.get(current)
                if target is not None and target not in variants:
                    variants.add(target)
                    changed = True
    return variants


def _simple_glyph(source, glyph_name, target_upm):
    glyph = source["glyf"][glyph_name]
    coords, end_points, flags = glyph.getCoordinates(source["glyf"])
    scale = target_upm / source["head"].unitsPerEm
    output = Glyph()
    output.numberOfContours = len(end_points)
    output.coordinates = GlyphCoordinates([
        (otRound(x * scale), otRound(y * scale)) for x, y in coords
    ])
    output.endPtsOfContours = list(end_points)
    output.flags = array("B", flags)
    output.program = ttProgram.Program()
    return output, scale


def _install(font, source, source_cp, targets, advance=None):
    source_name = source.getBestCmap()[source_cp]
    glyph, scale = _simple_glyph(source, source_name, font["head"].unitsPerEm)
    natural_advance = otRound(source["hmtx"].metrics[source_name][0] * scale)
    for target_name in targets:
        copied = deepcopy(glyph)
        copied.recalcBounds(font["glyf"])
        font["glyf"][target_name] = copied
        font["hmtx"].metrics[target_name] = (
            natural_advance if advance is None else advance,
            getattr(copied, "xMin", 0),
        )
        if "vmtx" in font:
            font["vmtx"].metrics[target_name] = (font["head"].unitsPerEm, 0)


def replace_public_punctuation(font, inter_path, weight):
    """Replace ! ? inverted forms and full-width forms with matched Inter outlines."""
    variable = TTFont(inter_path)
    source = instantiateVariableFont(
        variable, {"opsz": 14, "wght": weight}, inplace=False, optimize=True, static=True
    )
    variable.close()
    cmap = font.getBestCmap()
    order = list(font.getGlyphOrder())
    for cp, source_cp in {**HALF_SOURCE, **FULL_SOURCE}.items():
        target = cmap.get(cp)
        if target is None:
            target = f"interpunct.uni{cp:04X}"
            if target not in font["glyf"].glyphs:
                font["glyf"][target] = Glyph()
                font["hmtx"].metrics[target] = (0, 0)
                if "vmtx" in font:
                    font["vmtx"].metrics[target] = (font["head"].unitsPerEm, 0)
                order.append(target)
            for table in _unicode_tables(font):
                table.cmap[cp] = target
        targets = _locl_variants(font, target)
        _install(
            font, source, source_cp, targets,
            advance=font["head"].unitsPerEm if cp in FULL_SOURCE else None,
        )
    font.setGlyphOrder(list(dict.fromkeys(order)))
    font["glyf"].glyphOrder = font.getGlyphOrder()
    source.close()


def import_interrobang(font, inter_path, weight):
    variable = TTFont(inter_path)
    source = instantiateVariableFont(
        variable, {"opsz": 14, "wght": weight}, inplace=False, optimize=True, static=True
    )
    variable.close()
    half_name = "interrobang.uni203D"
    full_name = "interrobang.full"
    zero_name = "interrobang.zero"
    _install(font, source, 0x203D, [half_name], advance=500)
    _install(font, source, 0x203D, [full_name], advance=font["head"].unitsPerEm)
    empty = Glyph()
    empty.numberOfContours = 0
    empty.program = ttProgram.Program()
    font["glyf"][zero_name] = empty
    font["hmtx"].metrics[zero_name] = (0, 0)
    if "vmtx" in font:
        font["vmtx"].metrics[zero_name] = (0, 0)
    order = list(font["glyf"].glyphs.keys())
    if ".notdef" in order:
        order.remove(".notdef")
        order.insert(0, ".notdef")
    font.setGlyphOrder(order)
    font["glyf"].glyphOrder = order
    for table in _unicode_tables(font):
        table.cmap[0x203D] = half_name
    source.close()
    return half_name, full_name, zero_name


def _context_subtable(firsts, seconds, visible_lookup, zero_lookup, glyph_map):
    subtable = otTables.ChainContextSubst()
    subtable.Format = 3
    subtable.BacktrackGlyphCount = 0
    subtable.BacktrackCoverage = []
    subtable.InputGlyphCount = 2
    subtable.InputCoverage = [
        buildCoverage(firsts, glyph_map), buildCoverage(seconds, glyph_map)
    ]
    subtable.LookAheadGlyphCount = 0
    subtable.LookAheadCoverage = []
    first_record = otTables.SubstLookupRecord()
    first_record.SequenceIndex = 0
    first_record.LookupListIndex = visible_lookup
    second_record = otTables.SubstLookupRecord()
    second_record.SequenceIndex = 1
    second_record.LookupListIndex = zero_lookup
    subtable.SubstLookupRecord = [first_record, second_record]
    subtable.SubstCount = 2
    return subtable


def _direct_variants(font, glyph_name):
    """Only variants reachable through one substitution; avoids cmap aliases."""
    variants = {glyph_name}
    if "GSUB" not in font:
        return variants
    for lookup in font["GSUB"].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            lookup_type = lookup.LookupType
            if lookup_type == 7:
                lookup_type = subtable.ExtensionLookupType
                subtable = subtable.ExtSubTable
            if lookup_type == 1 and hasattr(subtable, "mapping") and glyph_name in subtable.mapping:
                variants.add(subtable.mapping[glyph_name])
    return variants


def add_pair_substitutions(font, half_name, full_name, zero_name):
    """Add ?!/!? -> [500,0] and full-width pairs -> [1000,0]."""
    cmap = font.getBestCmap()
    q = sorted(_direct_variants(font, cmap[0x003F]))
    e = sorted(_direct_variants(font, cmap[0x0021]))
    fq = sorted(_direct_variants(font, cmap[0xFF1F]))
    fe = sorted(_direct_variants(font, cmap[0xFF01]))
    visible_map = {glyph: half_name for glyph in set(q + e)}
    visible_map.update({glyph: full_name for glyph in set(fq + fe)})
    zero_map = {glyph: zero_name for glyph in set(q + e + fq + fe)}
    table = font["GSUB"].table
    visible_index = len(table.LookupList.Lookup)
    table.LookupList.Lookup.append(buildLookup([
        buildSingleSubstSubtable(visible_map)
    ], table="GSUB"))
    zero_index = len(table.LookupList.Lookup)
    table.LookupList.Lookup.append(buildLookup([
        buildSingleSubstSubtable(zero_map)
    ], table="GSUB"))
    glyph_map = font.getReverseGlyphMap()
    context = buildLookup([
        _context_subtable(q, e, visible_index, zero_index, glyph_map),
        _context_subtable(e, q, visible_index, zero_index, glyph_map),
        _context_subtable(fq, fe, visible_index, zero_index, glyph_map),
        _context_subtable(fe, fq, visible_index, zero_index, glyph_map),
    ], table="GSUB")
    table.LookupList.Lookup.append(context)
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    context_index = len(table.LookupList.Lookup) - 1
    attached = 0
    for feature_record in table.FeatureList.FeatureRecord:
        if feature_record.FeatureTag == "liga":
            feature_record.Feature.LookupListIndex.append(context_index)
            feature_record.Feature.LookupCount = len(feature_record.Feature.LookupListIndex)
            attached += 1
    if not attached:
        record = otTables.FeatureRecord()
        record.FeatureTag = "liga"
        record.Feature = otTables.Feature()
        record.Feature.FeatureParams = None
        record.Feature.LookupListIndex = [context_index]
        record.Feature.LookupCount = 1
        table.FeatureList.FeatureRecord.append(record)
        table.FeatureList.FeatureCount = len(table.FeatureList.FeatureRecord)
        old_index = len(table.FeatureList.FeatureRecord) - 1
        language_systems = []
        for script_record in table.ScriptList.ScriptRecord:
            if script_record.Script.DefaultLangSys is not None:
                language_systems.append(script_record.Script.DefaultLangSys)
            language_systems.extend(item.LangSys for item in script_record.Script.LangSysRecord)
        for language_system in language_systems:
            language_system.FeatureIndex.append(old_index)
            language_system.FeatureCount = len(language_system.FeatureIndex)
        indexed = list(enumerate(table.FeatureList.FeatureRecord))
        indexed.sort(key=lambda item: item[1].FeatureTag)
        remap = {old: new for new, (old, _) in enumerate(indexed)}
        table.FeatureList.FeatureRecord = [feature for _, feature in indexed]
        for language_system in language_systems:
            language_system.FeatureIndex = sorted(remap[index] for index in language_system.FeatureIndex)
            if language_system.ReqFeatureIndex != 0xFFFF:
                language_system.ReqFeatureIndex = remap[language_system.ReqFeatureIndex]


def glyph_signature(font, glyph_name):
    glyph = font["glyf"][glyph_name]
    coords, end_points, flags = glyph.getCoordinates(font["glyf"])
    return tuple(coords), tuple(end_points), bytes(flags), font["hmtx"].metrics[glyph_name]


