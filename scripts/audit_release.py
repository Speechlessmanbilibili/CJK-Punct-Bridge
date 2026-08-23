from pathlib import Path
from fontTools.ttLib import TTFont

DASHES=(0x2014,0x2E3A,0x2E3B)

def _lang_tags(font, script, lang):
    g=font["GSUB"].table
    records=g.FeatureList.FeatureRecord
    for sr in g.ScriptList.ScriptRecord:
        if sr.ScriptTag != script:
            continue
        ls=sr.Script.DefaultLangSys
        for lr in sr.Script.LangSysRecord:
            if lr.LangSysTag == lang:
                ls=lr.LangSys
        if ls is None:
            return set()
        return {records[i].FeatureTag for i in ls.FeatureIndex}
    return set()

def _bbox(font, glyph):
    g=font["glyf"][glyph]
    g.recalcBounds(font["glyf"])
    return g.xMin,g.yMin,g.xMax,g.yMax

def audit(path):
    f=TTFont(path)
    cmap=f.getBestCmap()
    assert "vhea" in f and "vmtx" in f
    assert "ccmp" not in _lang_tags(f,"DFLT","ENG ")
    assert "ccmp" not in _lang_tags(f,"latn","ENG ")
    assert "ccmp" in _lang_tags(f,"DFLT","ZHS ")
    assert "ccmp" in _lang_tags(f,"hani","ZHS ")
    assert {"locl","vert","vrt2"} <= _lang_tags(f,"DFLT","ENG ")
    for cp in DASHES:
        g=cmap[cp]
        x0,y0,x1,y1=_bbox(f,g)
        assert x1-x0 > y1-y0, (path,hex(cp),"horizontal glyph is not horizontal")
    if "fvar" in f:
        axis=next(a for a in f["fvar"].axes if a.axisTag=="wght")
        assert (axis.minValue,axis.defaultValue,axis.maxValue)==(100.0,400.0,900.0)
        assert len(f["fvar"].instances)==9
    f.close()

if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:]:
        audit(Path(arg))
        print("OK",arg)
