from pathlib import Path
import os
import math
from array import array
from copy import deepcopy
import unicodedata

from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
from fontTools.otlLib.builder import buildLookup, buildSingleSubstSubtable, buildStatTable
from fontTools.ttLib.tables import otTables
from language_systems import (
    CJK_LANGUAGE_ALIASES,
    HANKEN_SHARED_PUNCTUATION,
    WESTERN_LANGUAGE_SYSTEMS,
    WESTERN_SCRIPT_TAGS,
)
from font_metadata import apply_binary_metadata, project_names, VERSION
from inter_punctuation import replace_public_punctuation

REPO = Path(__file__).resolve().parents[1]
UP = Path(os.environ.get("CJK_PUNCT_UPSTREAM_DIR", REPO / "upstream"))
OUT = REPO
WORK = Path(os.environ.get("CJK_PUNCT_BUILD_DIR", REPO / "build"))
for p in [WORK, OUT/"fonts"/"variable", OUT/"fonts"/"static", OUT/"fonts"/"web"]:
    p.mkdir(parents=True, exist_ok=True)

FAMILY="CJK Punct Bridge"
PS="CJKPunctBridge"
MASTER_WEIGHTS={100:"Thin",300:"Light",400:"Regular",700:"Bold",900:"Black"}
ALL_WEIGHTS={100:"Thin",200:"ExtraLight",300:"Light",400:"Regular",500:"Medium",600:"SemiBold",700:"Bold",800:"ExtraBold",900:"Black"}
# Synthetic italic: the CJK punctuation has no true italic design, so the
# Noto/Zhudou sources get a uniform y-shear at the usual synthetic slant
# (10 degrees).  Latin punctuation still comes from the true Hanken Italic.
ITALIC = os.environ.get("CJK_PUNCT_ITALIC") == "1"
SLANT_DEG = 10.0
SLANT = math.tan(math.radians(SLANT_DEG))
HANKEN_IT = UP / "HankenGrotesk-Italic-wght.ttf"
REGIONS={
    "SC": ("ZHS ", UP/"NotoSansSC-wght.ttf"),
    "TC": ("ZHT ", UP/"NotoSansTC-wght.ttf"),
    "JP": ("JAN ", UP/"NotoSansJP-wght.ttf"),
    "KR": ("KOR ", UP/"NotoSansKR-wght.ttf"),
}
HANKEN=UP/"HankenGrotesk-wght.ttf"
INTER_UPRIGHT=UP/"InterVariable.ttf"
INTER_ITALIC=UP/"InterVariable-Italic.ttf"
ZDIR=UP/"zhudou"/"ttf"
ZFILES={100:ZDIR/"ZhudouSans-ExtraLight.ttf",300:ZDIR/"ZhudouSans-Light.ttf",400:ZDIR/"ZhudouSans-Regular.ttf",700:ZDIR/"ZhudouSans-Bold.ttf",900:ZDIR/"ZhudouSans-Heavy.ttf"}

def require_files():
    missing=[str(p) for _,p in REGIONS.values() if not p.exists()]
    if not HANKEN.exists(): missing.append(str(HANKEN))
    for inter in (INTER_UPRIGHT,INTER_ITALIC):
        if not inter.exists(): missing.append(str(inter))
    missing += [str(p) for p in ZFILES.values() if not p.exists()]
    if missing:
        raise SystemExit("Missing upstream files:\n"+"\n".join(missing))

def instance(path,w):
    f=TTFont(path)
    return instantiateVariableFont(f, {"wght":w}, inplace=False, optimize=True, static=True)

def shear_font(font, slant=SLANT, slant_deg=SLANT_DEG):
    """Synthetic italic: y-shear every outline so x' = x + y*slant.

    Simple glyphs keep their exact point structure, flags, and end points --
    only the coordinates are transformed, so varLib still sees interpolatable
    masters.  Composite glyphs are decomposed (identical on both sides thanks
    to the identity-shear pass in ``build_master``).  Advance widths stay
    unchanged while the left side bearing is recomputed from the new bounds;
    vertical metrics are untouched because the shear does not move y.
    """
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.transformPen import TransformPen
    glyph_set = font.getGlyphSet()
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for name in font.getGlyphOrder():
        glyph = glyf[name]
        if glyph is None or glyph.numberOfContours == 0:
            continue
        if glyph.numberOfContours > 0:
            if slant:
                coords = glyph.coordinates
                for i, (x, y) in enumerate(coords):
                    coords[i] = (x + y * slant, y)
        else:
            # Composite: decompose first without any transform, then shear the
            # resulting simple coordinates.  Doing the shear inside the pen
            # replay would round transformed points and let TTGlyphPen drop
            # duplicates, changing the point structure between the upright and
            # italic masters.
            rec = DecomposingRecordingPen(glyph_set)
            glyph_set[name].draw(rec)
            pen = TTGlyphPen(glyph_set)
            rec.replay(pen)
            new = pen.glyph()
            if slant:
                coords = new.coordinates
                for i, (x, y) in enumerate(coords):
                    coords[i] = (x + y * slant, y)
            new.recalcBounds(glyf)
            glyf[name] = new
        glyph = glyf[name]
        glyph.recalcBounds(glyf)
        adv = hmtx.metrics[name][0]
        hmtx.metrics[name] = (adv, getattr(glyph, "xMin", 0))
    font["post"].italicAngle = -slant_deg

def setname(nt,nid,val):
    nt.names=[r for r in nt.names if r.nameID!=nid]
    nt.setName(val,nid,3,1,0x409)
    try:
        val.encode("mac_roman"); nt.setName(val,nid,1,0,0)
    except Exception:
        pass

def set_static_names(f,w,style,italic=False):
    nt=f["name"]
    if italic:
        typographic_sub="Italic" if w==400 else f"{style} Italic"
        legacy_family=FAMILY if w in (400,700) else f"{FAMILY} {style}"
        legacy_sub="Bold Italic" if w==700 else "Italic"
        full=FAMILY if w==400 else f"{FAMILY} {style}"
        full=f"{full} Italic"
        unique=f"{PS}-Italic" if w==400 else f"{PS}-{style}Italic"
    else:
        typographic_sub=style
        legacy_family=FAMILY if w in (400,700) else f"{FAMILY} {style}"
        legacy_sub="Bold" if w==700 else "Regular"
        full=FAMILY if w==400 else f"{FAMILY} {style}"
        unique=f"{PS}-{style}"
    vals={**project_names(unique),1:legacy_family,2:legacy_sub,
          4:full,6:unique,16:FAMILY,17:typographic_sub,25:PS}
    for k,v in vals.items(): setname(nt,k,v)
    apply_binary_metadata(f)
    o=f["OS/2"]; o.usWeightClass=w
    fs=o.fsSelection
    for bit in (0,5,6,9): fs &= ~(1<<bit)
    if italic: fs|=1<<0
    if w==400 and not italic: fs|=1<<6
    if w==700: fs|=1<<5
    o.fsSelection=fs
    f["head"].macStyle &= ~3
    if w==700: f["head"].macStyle |= 1
    if italic: f["head"].macStyle |= 2

def build_vf(masters, italic=False):
    """Build one weight-axis variable font from its static masters.

    Upright and italic families are separate single-axis VF files sharing the
    typographic family name, exactly like the pinned Hanken Grotesk release
    (HankenGrotesk[wght].ttf + HankenGrotesk-Italic[wght].ttf).
    """
    ds=DesignSpaceDocument()
    ax=AxisDescriptor(); ax.name="Weight"; ax.tag="wght"; ax.minimum=100; ax.default=400; ax.maximum=900; ds.addAxis(ax)
    for w,s,p in masters:
        src=SourceDescriptor(); src.path=str(p); src.name=f"master.{w}"
        src.familyName=FAMILY; src.styleName=s+(" Italic" if italic else "")
        src.location={"Weight":w}
        if w==400:
            src.copyInfo=True; src.copyLib=True; src.copyGroups=True; src.copyFeatures=True
        ds.addSource(src)
    for w,s in ALL_WEIGHTS.items():
        name=s+(" Italic" if italic else "")
        ins=InstanceDescriptor(); ins.name=name; ins.familyName=FAMILY; ins.styleName=name
        ins.location={"Weight":w}; ds.addInstance(ins)
    dsp=WORK/f"{PS}{'-Italic' if italic else ''}.designspace"; ds.write(dsp)
    vf,_,_=varlib_build(str(dsp),exclude=["BASE","GDEF","GPOS","GSUB"])
    reg=TTFont(WORK/f"{PS}-Regular{'Italic' if italic else ''}.ttf")
    # BASE is intentionally dropped (Hanlink policy): Noto's static BASE
    # carries Device references into its own ItemVariationStore, which a
    # variable font cannot compile or share with HVAR.
    for tag in ("GDEF","GPOS","GSUB"):
        if tag in reg:
            table=deepcopy(reg[tag])
            # Static Noto-derived layout tables keep a weight-only
            # ItemVariationStore; the variable font cannot compile it
            # (and the layout layer is intentionally non-variable), so the
            # source store is dropped, mirroring Hanlink's own merge policy.
            if hasattr(table,"VarStore") and table.VarStore is not None:
                table.VarStore=None
            vf[tag]=table
    reg.close()
    nt=vf["name"]
    sub="Italic" if italic else "Regular"
    for k,v in {**project_names(f"{PS}-{'Italic-' if italic else ''}VF"),1:FAMILY,2:sub,
                4:FAMILY+(f" {sub}" if italic else ""),
                6:f"{PS}{'-Italic' if italic else ''}",16:FAMILY,17:sub,25:PS}.items():
        setname(nt,k,v)
    apply_binary_metadata(vf)
    o=vf["OS/2"]; o.usWeightClass=400
    fs=o.fsSelection
    for bit in (0,5,6,9): fs &= ~(1<<bit)
    if italic: fs|=1<<0
    else: fs|=1<<6
    o.fsSelection=fs
    vf["head"].macStyle &= ~3
    if italic: vf["head"].macStyle |= 2
    names=[]
    for w,s in ALL_WEIGHTS.items():
        names.append("Italic" if (italic and w==400) else s+(" Italic" if italic else ""))
    for inst,name in zip(vf["fvar"].instances,names):
        inst.subfamilyNameID=nt.addName(name,platforms=((3,1,0x409),(1,0,0)))
    stat_values=[dict(tag="wght",name="Weight",values=[dict(value=w,name=n,flags=0x2 if w==400 else 0) for (w,s),n in zip(ALL_WEIGHTS.items(),names)])]
    if italic:
        stat_values.append(dict(tag="ital",name="Italic",values=[dict(value=1,name="Italic")]))
    try: buildStatTable(vf,stat_values)
    except Exception: pass
    return vf

def copy_glyph(dst,src,sn,dn):
    dst["glyf"][dn]=deepcopy(src["glyf"][sn])
    dst["hmtx"].metrics[dn]=src["hmtx"].metrics[sn]
    if "vmtx" in dst:
        if "vmtx" in src and sn in src["vmtx"].metrics:
            dst["vmtx"].metrics[dn]=src["vmtx"].metrics[sn]
        else:
            dst["vmtx"].metrics[dn]=(1000,0)

def split_encoded_glyph(font,cp,suffix):
    """Give one encoded character its own GSUB-visible source glyph.

    Noto SC intentionally maps U+00B7 MIDDLE DOT and U+2022 BULLET to the same
    glyph, while Hanken gives them different designs.  A locl substitution
    sees glyph IDs rather than code points, so the public inputs must be split
    before Western alternates are attached.  Existing Noto single-substitution
    behavior is mirrored onto the duplicate to keep every CJK path unchanged.
    """
    cmap=font.getBestCmap(); base=cmap[cp]; order=list(font.getGlyphOrder())
    duplicate=f"{base}.{suffix}"; k=2
    while duplicate in order:
        duplicate=f"{base}.{suffix}{k}"; k+=1
    order.append(duplicate); copy_glyph(font,font,base,duplicate); font.setGlyphOrder(order)
    for table in font["cmap"].tables:
        if hasattr(table,"cmap") and cp in table.cmap:
            table.cmap[cp]=duplicate
    if "GSUB" in font:
        for lookup in font["GSUB"].table.LookupList.Lookup:
            for subtable in lookup.SubTable:
                typ=lookup.LookupType
                if typ==7:
                    typ=subtable.ExtensionLookupType; subtable=subtable.ExtSubTable
                if typ==1 and hasattr(subtable,"mapping") and base in subtable.mapping:
                    subtable.mapping[duplicate]=subtable.mapping[base]
    return duplicate

def get_script(table, tag, create=False):
    for sr in table.ScriptList.ScriptRecord:
        if sr.ScriptTag==tag: return sr.Script
    if not create: return None
    sr=otTables.ScriptRecord(); sr.ScriptTag=tag; sr.Script=otTables.Script()
    sr.Script.DefaultLangSys=None; sr.Script.LangSysRecord=[]; sr.Script.LangSysCount=0
    table.ScriptList.ScriptRecord.append(sr)
    table.ScriptList.ScriptRecord.sort(key=lambda r:r.ScriptTag)
    table.ScriptList.ScriptCount=len(table.ScriptList.ScriptRecord)
    return sr.Script

def get_langsys(table, script_tag, lang_tag=None):
    s=get_script(table,script_tag)
    if s is None: return None
    if lang_tag is None: return s.DefaultLangSys
    for lr in s.LangSysRecord:
        if lr.LangSysTag==lang_tag: return lr.LangSys
    return None

def set_langsys(script, tag, indices):
    vals=sorted(dict.fromkeys(indices))
    for lr in script.LangSysRecord:
        if lr.LangSysTag==tag:
            lr.LangSys.FeatureIndex=vals; lr.LangSys.FeatureCount=len(vals); lr.LangSys.ReqFeatureIndex=0xFFFF
            return
    lr=otTables.LangSysRecord(); lr.LangSysTag=tag
    ls=otTables.LangSys(); ls.LookupOrder=None; ls.ReqFeatureIndex=0xFFFF; ls.FeatureIndex=vals; ls.FeatureCount=len(vals)
    lr.LangSys=ls
    script.LangSysRecord.append(lr); script.LangSysRecord.sort(key=lambda r:r.LangSysTag)
    script.LangSysCount=len(script.LangSysRecord)

def append_single_feature(font, tag, mapping):
    g=font["GSUB"].table
    st=buildSingleSubstSubtable(mapping)
    lk=buildLookup([st], table="GSUB")
    g.LookupList.Lookup.append(lk); g.LookupList.LookupCount=len(g.LookupList.Lookup)
    li=len(g.LookupList.Lookup)-1
    fr=otTables.FeatureRecord(); fr.FeatureTag=tag
    feat=otTables.Feature(); feat.FeatureParams=None; feat.LookupListIndex=[li]; feat.LookupCount=1; fr.Feature=feat
    g.FeatureList.FeatureRecord.append(fr); g.FeatureList.FeatureCount=len(g.FeatureList.FeatureRecord)
    return len(g.FeatureList.FeatureRecord)-1

def feature_single_map(font, script, lang, tag):
    g=font["GSUB"].table; ls=get_langsys(g,script,lang); out={}
    if ls is None: return out
    for fi in ls.FeatureIndex:
        fr=g.FeatureList.FeatureRecord[fi]
        if fr.FeatureTag!=tag: continue
        for li in fr.Feature.LookupListIndex:
            lk=g.LookupList.Lookup[li]
            for st in lk.SubTable:
                typ=lk.LookupType
                if typ==7:
                    typ=st.ExtensionLookupType; st=st.ExtSubTable
                if typ==1 and hasattr(st,"mapping"):
                    out.update(st.mapping)
    return out

def apply_maps(glyph, maps):
    for mp in maps:
        glyph=mp.get(glyph,glyph)
    return glyph

def subset_punct(font, unicodes):
    opt=Options(); opt.layout_features=["*"]; opt.name_IDs=["*"]; opt.name_legacy=True
    opt.name_languages=["*"]; opt.glyph_names=True; opt.hinting=False
    sub=Subsetter(options=opt); sub.populate(unicodes=unicodes); sub.subset(font)

def scripts_with_lang(font, lang):
    g=font["GSUB"].table; out=[]
    for sr in g.ScriptList.ScriptRecord:
        if any(lr.LangSysTag==lang for lr in sr.Script.LangSysRecord):
            out.append(sr.ScriptTag)
    return out

def base_feature_indices(font, script_tag):
    g=font["GSUB"].table
    ls=get_langsys(g,script_tag,"ZHS ") or get_langsys(g,script_tag,None) or get_langsys(g,"DFLT",None)
    return list(ls.FeatureIndex) if ls else []

def build_master(weight,style,unicodes,western_cps,italic=False):
    h_src=HANKEN_IT if italic else HANKEN
    src={r:instance(path,weight) for r,(_,path) in REGIONS.items()}
    h=instance(h_src,weight); z=TTFont(ZFILES[weight])
    n=src["SC"]
    subset_punct(n,unicodes)
    for r in ("TC","JP","KR"):
        subset_punct(src[r],unicodes)
    if italic:
        for r in src:
            shear_font(src[r])
        shear_font(z)

    if n.getBestCmap()[0x00B7]==n.getBestCmap()[0x2022]:
        split_encoded_glyph(n,0x2022,"u2022")
    order=list(n.getGlyphOrder()); cmap=n.getBestCmap()
    zc=z.getBestCmap(); hc=h.getBestCmap()

    sc_locl=feature_single_map(n,"hani","ZHS ","locl")
    sc_vert=[feature_single_map(n,"hani","ZHS ","vert"),feature_single_map(n,"hani","ZHS ","vrt2")]
    zvert={0x2014:"uniFE31",0x2E3A:"uni2E3A.vert",0x2E3B:"uni2E3B.vert"}
    for cp in (0x2014,0x2E3A,0x2E3B):
        if cp not in cmap or cp not in zc: continue
        base=cmap[cp]
        copy_glyph(n,z,zc[cp],base)
        sc_h=apply_maps(base,[sc_locl])
        if sc_h in order: copy_glyph(n,z,zc[cp],sc_h)
        sc_v=apply_maps(sc_h,sc_vert)
        if sc_v in order and zvert[cp] in z.getGlyphOrder():
            copy_glyph(n,z,zvert[cp],sc_v)

    g=n["GSUB"].table
    for r in ("TC","JP","KR"):
        sf=src[r]; lang=REGIONS[r][0]; scm=sf.getBestCmap()
        locl=feature_single_map(sf,"hani",lang,"locl")
        vert=feature_single_map(sf,"hani",lang,"vert")
        vrt2=feature_single_map(sf,"hani",lang,"vrt2")
        locmap={}; vertmap={}; vrt2map={}
        for cp in unicodes:
            if cp not in cmap or cp not in scm: continue
            base=cmap[cp]; sb=scm[cp]
            sh=apply_maps(sb,[locl])
            if r=="TC" and cp in (0x2014,0x2E3A,0x2E3B) and cp in zc:
                src_font=z; src_name=zc[cp]
            else:
                src_font=sf; src_name=sh
            alt=f"{base}.{r.lower()}"; k=2
            while alt in order:
                alt=f"{base}.{r.lower()}{k}"; k+=1
            order.append(alt); copy_glyph(n,src_font,src_name,alt); locmap[base]=alt

            sv=apply_maps(sh,[vert,vrt2])
            if r=="TC" and cp in zvert and zvert[cp] in z.getGlyphOrder():
                vfont=z; vname=zvert[cp]
            else:
                vfont=sf; vname=sv
            if vname in vfont.getGlyphOrder() and (vname!=sh or cp in (0x2014,0x2E3A,0x2E3B)):
                valt=f"{base}.{r.lower()}.vert"; kk=2
                while valt in order:
                    valt=f"{base}.{r.lower()}.vert{kk}"; kk+=1
                order.append(valt); copy_glyph(n,vfont,vname,valt)
                vertmap[alt]=valt; vrt2map[alt]=valt

        n.setGlyphOrder(order)
        loc_i=append_single_feature(n,"locl",locmap)
        vert_i=append_single_feature(n,"vert",vertmap) if vertmap else None
        vrt2_i=append_single_feature(n,"vrt2",vrt2map) if vrt2map else None

        aliases=CJK_LANGUAGE_ALIASES[r]
        for stag in sorted(set(scripts_with_lang(sf,lang)) | {"DFLT"}):
            base_idx=base_feature_indices(n,stag)
            generic=[i for i in base_idx if g.FeatureList.FeatureRecord[i].FeatureTag not in ("locl","vert","vrt2")]
            custom=generic+[loc_i]+([vert_i] if vert_i is not None else [])+([vrt2_i] if vrt2_i is not None else [])
            script=get_script(g,stag,create=True)
            for alias in aliases:
                set_langsys(script,alias,custom)

    westmap={}
    for cp in western_cps:
        if cp not in cmap or cp not in hc: continue
        base=cmap[cp]; alt=f"{base}.west"; k=2
        while alt in order:
            alt=f"{base}.west{k}"; k+=1
        order.append(alt); copy_glyph(n,h,hc[cp],alt); westmap[base]=alt
    n.setGlyphOrder(order)
    western_i=append_single_feature(n,"locl",westmap)
    for stag in WESTERN_SCRIPT_TAGS:
        script=get_script(g,stag,create=True)
        for lang in WESTERN_LANGUAGE_SYSTEMS[stag]:
            # Western paths expose only the Hanken punctuation substitution.
            # This prevents Noto ccmp/dlig/width/vertical substitutions from
            # replacing Hanken punctuation after locl has selected it.
            set_langsys(script,lang,[western_i])

    sc_zhs=get_langsys(g,"hani","ZHS ")
    if sc_zhs is not None:
        for stag in scripts_with_lang(n,"ZHS "):
            source=get_langsys(g,stag,"ZHS ")
            if source is None: continue
            for alias in CJK_LANGUAGE_ALIASES["SC"]:
                set_langsys(get_script(g,stag,create=True),alias,list(source.FeatureIndex))
        for alias in CJK_LANGUAGE_ALIASES["SC"]:
            set_langsys(get_script(g,"DFLT",create=True),alias,list(sc_zhs.FeatureIndex))
        # No language/region metadata deliberately behaves like SC.
        for stag in ("DFLT","hani","kana","latn","cyrl","grek"):
            script=get_script(g,stag,create=True)
            ls=otTables.LangSys(); ls.LookupOrder=None; ls.ReqFeatureIndex=0xFFFF
            ls.FeatureIndex=list(sc_zhs.FeatureIndex); ls.FeatureCount=len(ls.FeatureIndex)
            script.DefaultLangSys=ls

    replace_public_punctuation(n,INTER_ITALIC if italic else INTER_UPRIGHT,weight)
    set_static_names(n,weight,style,italic=italic)
    stat_axes=[dict(tag="wght",name="Weight",values=[dict(value=weight,name=style,flags=0x2 if weight==400 else 0)])]
    if italic:
        stat_axes.append(dict(tag="ital",name="Italic",values=[
            dict(value=0,name="Regular",flags=0x2),dict(value=1,name="Italic")]))
    try:
        buildStatTable(n,stat_axes)
    except Exception: pass
    out=WORK/f"{PS}-{style}{'Italic' if italic else ''}.ttf"; n.save(out,reorderTables=True)
    for f in list(src.values())+[h,z]:
        try: f.close()
        except Exception: pass
    return out

def main():
    require_files()
    cmaps={}
    for r,(_,p) in REGIONS.items():
        f=TTFont(p); cmaps[r]=f.getBestCmap(); f.close()
    shared=set.intersection(*(set(cmaps[r]) for r in REGIONS))
    unicodes=sorted(cp for cp in shared if unicodedata.category(chr(cp)).startswith("P") and cp!=0x002D)
    assert not set(range(0x30,0x3A)) & set(unicodes), "ASCII digits must never enter the punctuation bridge"
    hf=TTFont(HANKEN); hc=hf.getBestCmap(); hf.close()
    western_cps=sorted(set(hc) & set(unicodes))
    if tuple(western_cps)!=HANKEN_SHARED_PUNCTUATION:
        raise SystemExit(
            "Pinned Google Fonts Hanken punctuation overlap changed:\n"
            f"expected {len(HANKEN_SHARED_PUNCTUATION)}, got {len(western_cps)}"
        )

    # Cache punctuation-only variable sources. This keeps local builds fast while preserving layout closure.
    subset_dir=WORK/"upstream-subsets"; subset_dir.mkdir(exist_ok=True)
    for r,(_,p) in list(REGIONS.items()):
        q=subset_dir/p.name
        if not q.exists():
            f=TTFont(p); subset_punct(f,unicodes); f.save(q,reorderTables=True); f.close()
        REGIONS[r]=(REGIONS[r][0],q)

    masters=[]
    for w,s in MASTER_WEIGHTS.items():
        p=build_master(w,s,unicodes,western_cps,italic=False); masters.append((w,s,p)); print("master",w,s,p.stat().st_size,flush=True)

    vf=build_vf(masters,italic=False)
    vfp=OUT/"fonts"/"variable"/f"{PS}-Variable.ttf"; vf.save(vfp,reorderTables=True); vf.close()
    for w,s in ALL_WEIGHTS.items():
        f=TTFont(vfp); st=instantiateVariableFont(f,{"wght":w},inplace=False,optimize=True,static=True)
        set_static_names(st,w,s); op=OUT/"fonts"/"static"/f"{PS}-{s}.ttf"
        st.save(op,reorderTables=True)
        st.flavor="woff2"; st.save(OUT/"fonts"/"web"/f"{PS}-{s}.woff2",reorderTables=True)
        st.close(); f.close()
    f=TTFont(vfp); f.flavor="woff2"; f.save(OUT/"fonts"/"web"/f"{PS}-Variable.woff2"); f.close()
    print("DONE upright",vfp,flush=True)

    if ITALIC:
        imasters=[]
        for w,s in MASTER_WEIGHTS.items():
            p=build_master(w,s,unicodes,western_cps,italic=True); imasters.append((w,s,p)); print("italic master",w,s,p.stat().st_size,flush=True)
        vf=build_vf(imasters,italic=True)
        vfp=OUT/"fonts"/"variable"/f"{PS}-Italic-Variable.ttf"; vf.save(vfp,reorderTables=True); vf.close()
        for w,s in ALL_WEIGHTS.items():
            f=TTFont(vfp); st=instantiateVariableFont(f,{"wght":w},inplace=False,optimize=True,static=True)
            set_static_names(st,w,s,italic=True)
            op=OUT/"fonts"/"static"/f"{PS}-{'Italic' if w==400 else s+'Italic'}.ttf"
            st.save(op,reorderTables=True)
            web_name=f"{PS}-{'Italic' if w==400 else s+'Italic'}.woff2"
            st.flavor="woff2"; st.save(OUT/"fonts"/"web"/web_name,reorderTables=True)
            st.close(); f.close()
        f=TTFont(vfp); f.flavor="woff2"; f.save(OUT/"fonts"/"web"/f"{PS}-Italic-Variable.woff2"); f.close()
        print("DONE italic",vfp,flush=True)

if __name__=="__main__":
    main()
