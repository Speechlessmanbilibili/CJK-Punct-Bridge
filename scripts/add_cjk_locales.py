from pathlib import Path
from copy import deepcopy
import os
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
from fontTools.varLib import build as varlib_build
from fontTools.otlLib.builder import buildLookup, buildSingleSubstSubtable
from fontTools.ttLib.tables import otTables

REPO = Path(__file__).resolve().parents[1]
BASE = Path(os.environ['CJK_PUNCT_BASE_VARIABLE'])
REGIONS = {
    'tc': (Path(os.environ['CJK_PUNCT_TC_VARIABLE']), 'ZHT '),
    'jp': (Path(os.environ['CJK_PUNCT_JP_VARIABLE']), 'JAN '),
    'kr': (Path(os.environ['CJK_PUNCT_KR_VARIABLE']), 'KOR '),
}
OUT = Path(os.environ.get('CJK_PUNCT_LOCALE_BUILD_DIR', REPO / 'dist'))
OUT.mkdir(parents=True, exist_ok=True)
MASTER_WEIGHTS = {100:'Thin', 300:'Light', 400:'Regular', 700:'Bold', 900:'Black'}
ALL_WEIGHTS = {100:'Thin', 200:'ExtraLight', 300:'Light', 400:'Regular', 500:'Medium', 600:'SemiBold', 700:'Bold', 800:'ExtraBold', 900:'Black'}
DASHES = {0x2014, 0x2E3A, 0x2E3B}


def langsys(gsub, script_tag, lang_tag=None):
    for sr in gsub.ScriptList.ScriptRecord:
        if sr.ScriptTag != script_tag:
            continue
        if lang_tag is None:
            return sr.Script.DefaultLangSys
        for lr in sr.Script.LangSysRecord:
            if lr.LangSysTag == lang_tag:
                return lr.LangSys
    return None


def feature_map(font, feature_tag):
    gsub = font['GSUB'].table
    systems = []
    default = langsys(gsub, 'DFLT', None)
    if default:
        systems.append(default)
    for sr in gsub.ScriptList.ScriptRecord:
        if sr.Script.DefaultLangSys and sr.Script.DefaultLangSys not in systems:
            systems.append(sr.Script.DefaultLangSys)
    for system in systems:
        mapping = {}
        for feature_index in system.FeatureIndex:
            record = gsub.FeatureList.FeatureRecord[feature_index]
            if record.FeatureTag != feature_tag:
                continue
            for lookup_index in record.Feature.LookupListIndex:
                lookup = gsub.LookupList.Lookup[lookup_index]
                for subtable in lookup.SubTable:
                    lookup_type = lookup.LookupType
                    if lookup_type == 7:
                        subtable = subtable.ExtSubTable
                        lookup_type = subtable.ExtensionLookupType
                    if lookup_type == 1 and hasattr(subtable, 'mapping'):
                        mapping.update(subtable.mapping)
        if mapping:
            return mapping
    return {}


def get_script(gsub, tag):
    for sr in gsub.ScriptList.ScriptRecord:
        if sr.ScriptTag == tag:
            return sr.Script
    sr = otTables.ScriptRecord()
    sr.ScriptTag = tag
    sr.Script = otTables.Script()
    sr.Script.DefaultLangSys = None
    sr.Script.LangSysRecord = []
    sr.Script.LangSysCount = 0
    gsub.ScriptList.ScriptRecord.append(sr)
    gsub.ScriptList.ScriptRecord.sort(key=lambda record: record.ScriptTag)
    gsub.ScriptList.ScriptCount = len(gsub.ScriptList.ScriptRecord)
    return sr.Script


def set_langsys(script, tag, feature_indices):
    for lr in script.LangSysRecord:
        if lr.LangSysTag == tag:
            system = lr.LangSys
            break
    else:
        lr = otTables.LangSysRecord()
        lr.LangSysTag = tag
        lr.LangSys = otTables.LangSys()
        lr.LangSys.LookupOrder = None
        script.LangSysRecord.append(lr)
        script.LangSysRecord.sort(key=lambda record: record.LangSysTag)
        script.LangSysCount = len(script.LangSysRecord)
        system = lr.LangSys
    system.ReqFeatureIndex = 0xFFFF
    system.FeatureIndex = sorted(set(feature_indices))
    system.FeatureCount = len(system.FeatureIndex)


def add_feature(gsub, tag, mapping):
    subtable = buildSingleSubstSubtable(mapping)
    lookup = buildLookup([subtable], table='GSUB')
    gsub.LookupList.Lookup.append(lookup)
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)
    lookup_index = len(gsub.LookupList.Lookup) - 1
    record = otTables.FeatureRecord()
    record.FeatureTag = tag
    feature = otTables.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = [lookup_index]
    feature.LookupCount = 1
    record.Feature = feature
    gsub.FeatureList.FeatureRecord.append(record)
    gsub.FeatureList.FeatureCount = len(gsub.FeatureList.FeatureRecord)
    return len(gsub.FeatureList.FeatureRecord) - 1


def copy_glyph_recursive(dst, src, source_name, destination_name, prefix, cache):
    if source_name in cache:
        return cache[source_name]
    if destination_name in dst.getGlyphOrder():
        cache[source_name] = destination_name
        return destination_name
    glyph = deepcopy(src['glyf'][source_name])
    if glyph.isComposite():
        for component in glyph.components:
            dependency = f'{prefix}{component.glyphName}'
            component.glyphName = copy_glyph_recursive(
                dst, src, component.glyphName, dependency, prefix, cache
            )
    order = list(dst.getGlyphOrder())
    dst['glyf'][destination_name] = glyph
    dst['hmtx'].metrics[destination_name] = src['hmtx'].metrics[source_name]
    if 'vmtx' in dst and 'vmtx' in src and source_name in src['vmtx'].metrics:
        dst['vmtx'].metrics[destination_name] = src['vmtx'].metrics[source_name]
    order.append(destination_name)
    dst.setGlyphOrder(order)
    dst['glyf'].glyphOrder = order
    cache[source_name] = destination_name
    return destination_name


def patch_master(weight):
    variable = TTFont(BASE)
    bridge = instantiateVariableFont(variable, {'wght': weight}, inplace=False, optimize=True, static=True)
    variable.close()
    gsub = bridge['GSUB'].table
    bridge_cmap = bridge.getBestCmap()
    zhs = langsys(gsub, 'DFLT', 'ZHS ') or langsys(gsub, 'hani', 'ZHS ') or langsys(gsub, 'DFLT', None)
    base_features = list(zhs.FeatureIndex) if zhs else []

    for suffix, (source_path, lang_tag) in REGIONS.items():
        source_variable = TTFont(source_path)
        source = instantiateVariableFont(source_variable, {'wght': weight}, inplace=False, optimize=True, static=True)
        source_variable.close()
        source_cmap = source.getBestCmap()
        source_vert = feature_map(source, 'vert')
        source_vrt2 = feature_map(source, 'vrt2')
        locale_map, vert_map, vrt2_map, cache = {}, {}, {}, {}

        for codepoint, base_name in bridge_cmap.items():
            if codepoint in DASHES or codepoint not in source_cmap:
                continue
            source_name = source_cmap[codepoint]
            alt_name = copy_glyph_recursive(bridge, source, source_name, f'{base_name}.{suffix}', f'.{suffix}.', cache)
            locale_map[base_name] = alt_name
            vert_source = source_vert.get(source_name)
            if vert_source:
                vert_name = copy_glyph_recursive(bridge, source, vert_source, f'{base_name}.{suffix}.vert', f'.{suffix}.v.', cache)
                vert_map[alt_name] = vert_name
            vrt2_source = source_vrt2.get(source_name)
            if vrt2_source:
                vrt2_name = copy_glyph_recursive(bridge, source, vrt2_source, f'{base_name}.{suffix}.vrt2', f'.{suffix}.v2.', cache)
                vrt2_map[alt_name] = vrt2_name

        locl_index = add_feature(gsub, 'locl', locale_map)
        vert_index = add_feature(gsub, 'vert', vert_map) if vert_map else None
        vrt2_index = add_feature(gsub, 'vrt2', vrt2_map) if vrt2_map else None
        keep = [i for i in base_features if gsub.FeatureList.FeatureRecord[i].FeatureTag not in ('locl', 'vert', 'vrt2')]
        locale_features = keep + [locl_index]
        if vert_index is not None:
            locale_features.append(vert_index)
        if vrt2_index is not None:
            locale_features.append(vrt2_index)
        for script_tag in ('DFLT', 'hani', 'kana', 'hang', 'latn'):
            set_langsys(get_script(gsub, script_tag), lang_tag, locale_features)
        source.close()

    for record in bridge['name'].names:
        if record.nameID == 5:
            try:
                record.string = 'Version 1.100'.encode(record.getEncoding())
            except Exception:
                pass
    path = OUT / f'master-{weight}.ttf'
    bridge.save(path, reorderTables=True)
    bridge.close()
    return path


def main():
    masters = []
    for weight, style in MASTER_WEIGHTS.items():
        path = patch_master(weight)
        masters.append((weight, style, path))
        print('master', weight, path.stat().st_size, flush=True)

    designspace = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.name, axis.tag, axis.minimum, axis.default, axis.maximum = 'Weight', 'wght', 100, 400, 900
    designspace.addAxis(axis)
    for weight, style, path in masters:
        source = SourceDescriptor()
        source.path, source.name = str(path), f'master.{weight}'
        source.familyName, source.styleName, source.location = 'CJK Punct Bridge', style, {'Weight': weight}
        if weight == 400:
            source.copyInfo = source.copyLib = source.copyGroups = source.copyFeatures = True
        designspace.addSource(source)
    for weight, style in ALL_WEIGHTS.items():
        instance = InstanceDescriptor()
        instance.name, instance.familyName, instance.styleName = style, 'CJK Punct Bridge', style
        instance.location = {'Weight': weight}
        designspace.addInstance(instance)
    designspace_path = OUT / 'CJKPunctBridge.designspace'
    designspace.write(designspace_path)

    variable, _, _ = varlib_build(str(designspace_path), exclude=['BASE', 'GDEF', 'GPOS', 'GSUB'])
    regular = TTFont(OUT / 'master-400.ttf')
    for tag in ('BASE', 'GDEF', 'GPOS', 'GSUB'):
        if tag in regular:
            variable[tag] = deepcopy(regular[tag])
    regular.close()
    original = TTFont(BASE)
    variable['name'] = deepcopy(original['name'])
    original.close()
    for record in variable['name'].names:
        if record.nameID == 5:
            try:
                record.string = 'Version 1.100'.encode(record.getEncoding())
            except Exception:
                pass
    variable_path = OUT / 'CJKPunctBridge-Variable.ttf'
    variable.save(variable_path, reorderTables=True)
    variable.close()

    for weight, style in ALL_WEIGHTS.items():
        font = TTFont(variable_path)
        static = instantiateVariableFont(font, {'wght': weight}, inplace=False, optimize=True, static=True)
        static.save(OUT / f'CJKPunctBridge-{style}.ttf', reorderTables=True)
        static.close()
        font.close()
    web = TTFont(variable_path)
    web.flavor = 'woff2'
    web.save(OUT / 'CJKPunctBridge-Variable.woff2')
    web.close()
    print('DONE', variable_path, flush=True)


if __name__ == '__main__':
    main()
