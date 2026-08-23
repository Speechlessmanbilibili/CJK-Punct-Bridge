from pathlib import Path
import os
from copy import deepcopy
import unicodedata

from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
from fontTools.otlLib.builder import buildLookup, buildSingleSubstSubtable, buildStatTable
from fontTools.ttLib.tables import otTables

REPO = Path(__file__).resolve().parents[1]
UP = Path(os.environ.get("CJK_PUNCT_UPSTREAM_DIR", REPO / "upstream"))
OUT = REPO
WORK = Path(os.environ.get("CJK_PUNCT_BUILD_DIR", REPO / "build"))
for p in [WORK, OUT/"fonts"/"variable", OUT/"fonts"/"static", OUT/"fonts"/"web"]:
    p.mkdir(parents=True, exist_ok=True)

FAMILY="CJK Punct Bridge"
PS="CJKPunctBridge"
VERSION="1.100"
MASTER_WEIGHTS={100:"Thin",300:"Light",400:"Regular",700:"Bold",900:"Black"}
ALL_WEIGHTS={100:"Thin",200:"ExtraLight",300:"Light",400:"Regular",500:"Medium",600:"SemiBold",700:"Bold",800:"ExtraBold",900:"Black"}
REGIONS={
    "SC": ("ZHS ", UP/"NotoSansSC-wght.ttf"),
    "TC": ("ZHT ", UP/"NotoSansTC-wght.ttf"),
    "JP": ("JAN ", UP/"NotoSansJP-wght.ttf"),
    "KR": ("KOR ", UP/"NotoSansKR-wght.ttf"),
}
HANKEN=UP/"HankenGrotesk-wght.ttf"
ZDIR=UP/"zhudou"/"ttf"
ZFILES={100:ZDIR/"ZhudouSans-ExtraLight.ttf",300:ZDIR/"ZhudouSans-Light.ttf",400:ZDIR/"ZhudouSans-Regular.ttf",700:ZDIR/"ZhudouSans-Bold.ttf",900:ZDIR/"ZhudouSans-Heavy.ttf"}

COPYRIGHT=("Portions Copyright 2021 The Hanken Grotesk Project Authors. "
           "Portions Copyright 2014-2021 Adobe, with Reserved Font Name 'Source'. "
           "Portions Copyright 2022 Buernia, with Reserved Font Names 'Zhudou' and '煮豆'; portions Copyright 2015 Google Inc. "
           "CJK Punct Bridge is a modified/combined font distributed under SIL Open Font License 1.1.")

def require_files():
    missing=[str(p) for _,p in REGIONS.values() if not p.exists()]
    if not HANKEN.exists(): missing.append(str(HANKEN))
    missing += [str(p) for p in ZFILES.values() if not p.exists()]
    if missing:
        raise SystemExit("Missing upstream files:\n"+"\n".join(missing))

def instance(path,w):
    f=TTFont(path)
    return instantiateVariableFont(f, {"wght":w}, inplace=False, optimize=True, static=True)

def setname(nt,nid,val):
    nt.names=[r for r in nt.names if r.nameID!=nid]
    nt.setName(val,nid,3,1,0x409)
    try:
        val.encode("mac_roman"); nt.setName(val,nid,1,0,0)
    except Exception:
        pass

def set_static_names(f,w,style):
    nt=f["name"]
    legacy_family=FAMILY if w in (400,700) else f"{FAMILY} {style}"
    legacy_sub="Bold" if w==700 else "Regular"
    full=FAMILY if w==400 else f"{FAMILY} {style}"
    vals={0:COPYRIGHT,1:legacy_family,2:legacy_sub,3:f"{VERSION};BridgeBuild;{PS}-{style}",
          4:full,5:f"Version {VERSION}",6:f"{PS}-{style}",13:"SIL Open Font License, Version 1.1",
          14:"https://openfontlicense.org",16:FAMILY,17:style,25:PS}
    for k,v in vals.items(): setname(nt,k,v)
    o=f["OS/2"]; o.usWeightClass=w; o.achVendID="NONE"
    fs=o.fsSelection
    for bit in (0,5,6,9): fs &= ~(1<<bit)
    if w==400: fs|=1<<6
    if w==700: fs|=1<<5
    o.fsSelection=fs
    f["head"].macStyle &= ~3
    if w==700: f["head"].macStyle |= 1

def copy_glyph(dst,src,sn,dn):
    dst["glyf"][dn]=deepcopy(src["glyf"][sn])
    dst["hmtx"].metrics[dn]=src["hmtx"].metrics[sn]
    if "vmtx" in dst:
        if "vmtx" in src and sn in src["vmtx"].metrics:
            dst["vmtx"].metrics[dn]=src["vmtx"].metrics[sn]
        else:
            dst["vmtx"].metrics[dn]=(1000,0)

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
                    st=st.ExtSubTable; typ=st.ExtensionLookupType
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

def build_master(weight,style,unicodes,en_cps):
    src={r:instance(path,weight) for r,(_,path) in REGIONS.items()}
    h=instance(HANKEN,weight); z=TTFont(ZFILES[weight])
    n=src["SC"]
    subset_punct(n,unicodes)
    for r in ("TC","JP","KR"):
        subset_punct(src[r],unicodes)

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

        for stag in sorted(set(scripts_with_lang(sf,lang)) | {"DFLT"}):
            base_idx=base_feature_indices(n,stag)
            generic=[i for i in base_idx if g.FeatureList.FeatureRecord[i].FeatureTag not in ("locl","vert","vrt2")]
            custom=generic+[loc_i]+([vert_i] if vert_i is not None else [])+([vrt2_i] if vrt2_i is not None else [])
            set_langsys(get_script(g,stag,create=True),lang,custom)

    enmap={}
    for cp in en_cps:
        if cp not in cmap or cp not in hc: continue
        base=cmap[cp]; alt=f"{base}.en"; k=2
        while alt in order:
            alt=f"{base}.en{k}"; k+=1
        order.append(alt); copy_glyph(n,h,hc[cp],alt); enmap[base]=alt
    n.setGlyphOrder(order)
    eng_i=append_single_feature(n,"locl",enmap)
    for stag in ("DFLT","latn"):
        base_idx=base_feature_indices(n,stag)
        generic=[i for i in base_idx if g.FeatureList.FeatureRecord[i].FeatureTag not in ("locl","ccmp")]
        set_langsys(get_script(g,stag,create=True),"ENG ",generic+[eng_i])

    sc_zhs=get_langsys(g,"hani","ZHS ")
    if sc_zhs is not None:
        set_langsys(get_script(g,"DFLT",create=True),"ZHS ",list(sc_zhs.FeatureIndex))
        # No language/region metadata deliberately behaves like SC.
        for stag in ("DFLT","hani","kana","latn","cyrl","grek"):
            script=get_script(g,stag,create=True)
            ls=otTables.LangSys(); ls.LookupOrder=None; ls.ReqFeatureIndex=0xFFFF
            ls.FeatureIndex=list(sc_zhs.FeatureIndex); ls.FeatureCount=len(ls.FeatureIndex)
            script.DefaultLangSys=ls

    set_static_names(n,weight,style)
    try:
        buildStatTable(n,[dict(tag="wght",name="Weight",values=[dict(value=weight,name=style,flags=0x2 if weight==400 else 0)])])
    except Exception: pass
    out=WORK/f"{PS}-{style}.ttf"; n.save(out,reorderTables=True)
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
    hf=TTFont(HANKEN); hc=hf.getBestCmap(); hf.close()
    en_cps=[cp for cp in (0x00B7,0x2013,0x2014,0x2018,0x2019,0x201C,0x201D,0x2026) if cp in hc and cp in unicodes]

    # Cache punctuation-only variable sources. This keeps local builds fast while preserving layout closure.
    subset_dir=WORK/"upstream-subsets"; subset_dir.mkdir(exist_ok=True)
    for r,(_,p) in list(REGIONS.items()):
        q=subset_dir/p.name
        if not q.exists():
            f=TTFont(p); subset_punct(f,unicodes); f.save(q,reorderTables=True); f.close()
        REGIONS[r]=(REGIONS[r][0],q)

    masters=[]
    for w,s in MASTER_WEIGHTS.items():
        p=build_master(w,s,unicodes,en_cps); masters.append((w,s,p)); print("master",w,p.stat().st_size,flush=True)

    ds=DesignSpaceDocument()
    ax=AxisDescriptor(); ax.name="Weight"; ax.tag="wght"; ax.minimum=100; ax.default=400; ax.maximum=900; ds.addAxis(ax)
    for w,s,p in masters:
        src=SourceDescriptor(); src.path=str(p); src.name=f"master.{w}"; src.familyName=FAMILY; src.styleName=s; src.location={"Weight":w}
        if w==400:
            src.copyInfo=True; src.copyLib=True; src.copyGroups=True; src.copyFeatures=True
        ds.addSource(src)
    for w,s in ALL_WEIGHTS.items():
        ins=InstanceDescriptor(); ins.name=s; ins.familyName=FAMILY; ins.styleName=s; ins.location={"Weight":w}; ds.addInstance(ins)
    dsp=WORK/f"{PS}.designspace"; ds.write(dsp)
    vf,_,_=varlib_build(str(dsp),exclude=["BASE","GDEF","GPOS","GSUB"])
    reg=TTFont(WORK/f"{PS}-Regular.ttf")
    for tag in ("BASE","GDEF","GPOS","GSUB"):
        if tag in reg: vf[tag]=deepcopy(reg[tag])
    reg.close()
    nt=vf["name"]
    for k,v in {0:COPYRIGHT,1:FAMILY,2:"Regular",3:f"{VERSION};BridgeBuild;{PS}-VF",4:FAMILY,5:f"Version {VERSION}",
                6:PS,13:"SIL Open Font License, Version 1.1",14:"https://openfontlicense.org",16:FAMILY,17:"Regular",25:PS}.items():
        setname(nt,k,v)
    for inst,(w,s) in zip(vf["fvar"].instances,ALL_WEIGHTS.items()):
        inst.subfamilyNameID=nt.addName(s,platforms=((3,1,0x409),(1,0,0)))
    try:
        buildStatTable(vf,[dict(tag="wght",name="Weight",values=[dict(value=w,name=s,flags=0x2 if w==400 else 0) for w,s in ALL_WEIGHTS.items()])])
    except Exception: pass
    vfp=OUT/"fonts"/"variable"/f"{PS}-Variable.ttf"; vf.save(vfp,reorderTables=True); vf.close()
    for w,s in ALL_WEIGHTS.items():
        f=TTFont(vfp); st=instantiateVariableFont(f,{"wght":w},inplace=False,optimize=True,static=True)
        set_static_names(st,w,s); op=OUT/"fonts"/"static"/f"{PS}-{s}.ttf"; st.save(op,reorderTables=True); st.close(); f.close()
    f=TTFont(vfp); f.flavor="woff2"; f.save(OUT/"fonts"/"web"/f"{PS}-Variable.woff2"); f.close()
    print("DONE",vfp,flush=True)

if __name__=="__main__":
    main()
