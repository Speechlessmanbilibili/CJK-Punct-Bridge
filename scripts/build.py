from pathlib import Path
from copy import deepcopy
import unicodedata, shutil, zipfile
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
from fontTools.otlLib.builder import buildLookup, buildSingleSubstSubtable, buildStatTable
from fontTools.ttLib.tables import otTables

ROOT=Path('/mnt/data')
SRC=ROOT/'fontwork'
OUT=ROOT/'CJKPunctBridge-v2'
WORK=ROOT/'CJKPunctBridge-v2-build'
for p in [OUT,WORK,OUT/'fonts'/'variable',OUT/'fonts'/'static',OUT/'fonts'/'web']:
    p.mkdir(parents=True,exist_ok=True)
FAMILY='CJK Punct Bridge'; PS='CJKPunctBridge'; VERSION='2.000'
MASTER_WEIGHTS={100:'Thin',300:'Light',400:'Regular',700:'Bold',900:'Black'}
ALL_WEIGHTS={100:'Thin',200:'ExtraLight',300:'Light',400:'Regular',500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black'}
NFILES={w:SRC/'noto/static'/f'NotoSansSC-{s}.ttf' for w,s in MASTER_WEIGHTS.items()}
HFILES={w:SRC/'hanken/static'/f'HankenGrotesk-{s}.ttf' for w,s in MASTER_WEIGHTS.items()}
ZFILES={100:ROOT/'zhudou_work/ttf/ZhudouSans-ExtraLight.ttf',300:ROOT/'zhudou_work/ttf/ZhudouSans-Light.ttf',400:ROOT/'zhudou_work/ttf/ZhudouSans-Regular.ttf',700:ROOT/'zhudou_work/ttf/ZhudouSans-Bold.ttf',900:ROOT/'zhudou_work/ttf/ZhudouSans-Heavy.ttf'}

z0=TTFont(ZFILES[400]); n0=TTFont(NFILES[400]); h0=TTFont(HFILES[400])
zc=z0.getBestCmap(); nc=n0.getBestCmap(); hc=h0.getBestCmap()
UNICODES=sorted(cp for cp in set(zc)&set(nc) if unicodedata.category(chr(cp)).startswith('P') and cp != 0x002D)
EN_CPS=[cp for cp in [0x00B7,0x2013,0x2014,0x2018,0x2019,0x201C,0x201D,0x2026] if cp in hc and cp in UNICODES]
z0.close(); n0.close(); h0.close()

COPYRIGHT=("Portions Copyright 2021 The Hanken Grotesk Project Authors. "
           "Portions Copyright 2014-2021 Adobe, with Reserved Font Name 'Source'. "
           "Portions Copyright 2022 Buernia, with Reserved Font Names 'Zhudou' and '煮豆'; portions Copyright 2015 Google Inc. "
           "CJK Punct Bridge is a modified/combined font distributed under SIL Open Font License 1.1.")

def setname(nt,nid,val):
    nt.names=[r for r in nt.names if r.nameID!=nid]
    nt.setName(val,nid,3,1,0x409)
    try:
        val.encode('mac_roman'); nt.setName(val,nid,1,0,0)
    except Exception: pass

def set_static_names(f,w,style):
    nt=f['name']
    legacy_family=FAMILY if w in (400,700) else f'{FAMILY} {style}'
    legacy_sub='Regular' if w not in (700,) else 'Bold'
    full=FAMILY if w==400 else f'{FAMILY} {style}'
    vals={0:COPYRIGHT,1:legacy_family,2:legacy_sub,3:f'{VERSION};BridgeBuild;{PS}-{style}',4:full,5:f'Version {VERSION}',6:f'{PS}-{style}',13:'SIL Open Font License, Version 1.1',14:'https://openfontlicense.org',16:FAMILY,17:style,25:PS}
    for k,v in vals.items(): setname(nt,k,v)
    o=f['OS/2']; o.usWeightClass=w; o.achVendID='NONE'; fs=o.fsSelection
    for bit in (0,5,6,9): fs &= ~(1<<bit)
    if w==400: fs|=1<<6
    if w==700: fs|=1<<5
    o.fsSelection=fs; f['head'].macStyle &= ~3
    if w==700: f['head'].macStyle |= 1

def copy_glyph(dst,src,sn,dn,vertical=True):
    dst['glyf'][dn]=deepcopy(src['glyf'][sn]); dst['hmtx'].metrics[dn]=src['hmtx'].metrics[sn]
    if vertical and 'vmtx' in dst:
        if 'vmtx' in src and sn in src['vmtx'].metrics: dst['vmtx'].metrics[dn]=src['vmtx'].metrics[sn]
        else: dst['vmtx'].metrics[dn]=(1000,0)

def increment_feature_indices(gsub,insert_idx):
    for sr in gsub.ScriptList.ScriptRecord:
        systems=[]
        if sr.Script.DefaultLangSys: systems.append(sr.Script.DefaultLangSys)
        systems += [lr.LangSys for lr in sr.Script.LangSysRecord]
        for ls in systems:
            ls.FeatureIndex=[i+1 if i>=insert_idx else i for i in ls.FeatureIndex]
            if ls.ReqFeatureIndex!=0xFFFF and ls.ReqFeatureIndex>=insert_idx: ls.ReqFeatureIndex += 1

def get_script(gsub,tag):
    for sr in gsub.ScriptList.ScriptRecord:
        if sr.ScriptTag==tag: return sr.Script
    sr=otTables.ScriptRecord(); sr.ScriptTag=tag; sr.Script=otTables.Script(); sr.Script.DefaultLangSys=None; sr.Script.LangSysRecord=[]; sr.Script.LangSysCount=0
    gsub.ScriptList.ScriptRecord.append(sr); gsub.ScriptList.ScriptRecord.sort(key=lambda r:r.ScriptTag); gsub.ScriptList.ScriptCount=len(gsub.ScriptList.ScriptRecord); return sr.Script

def set_langsys(script,tag,feature_indices):
    for lr in script.LangSysRecord:
        if lr.LangSysTag==tag:
            lr.LangSys.FeatureIndex=sorted(set(feature_indices)); lr.LangSys.FeatureCount=len(lr.LangSys.FeatureIndex); lr.LangSys.ReqFeatureIndex=0xFFFF; return
    lr=otTables.LangSysRecord(); lr.LangSysTag=tag; ls=otTables.LangSys(); ls.LookupOrder=None; ls.ReqFeatureIndex=0xFFFF; ls.FeatureIndex=sorted(set(feature_indices)); ls.FeatureCount=len(ls.FeatureIndex); lr.LangSys=ls
    script.LangSysRecord.append(lr); script.LangSysRecord.sort(key=lambda r:r.LangSysTag); script.LangSysCount=len(script.LangSysRecord)

def add_english_locl(font,mapping):
    g=font['GSUB'].table
    st=buildSingleSubstSubtable(mapping); lookup=buildLookup([st],table='GSUB')
    g.LookupList.Lookup.append(lookup); g.LookupList.LookupCount=len(g.LookupList.Lookup); lookup_idx=len(g.LookupList.Lookup)-1
    fr=otTables.FeatureRecord(); fr.FeatureTag='locl'; feat=otTables.Feature(); feat.FeatureParams=None; feat.LookupListIndex=[lookup_idx]; feat.LookupCount=1; fr.Feature=feat
    tags=[r.FeatureTag for r in g.FeatureList.FeatureRecord]; insert_idx=0
    while insert_idx<len(tags) and tags[insert_idx] <= 'locl': insert_idx += 1
    increment_feature_indices(g,insert_idx)
    g.FeatureList.FeatureRecord.insert(insert_idx,fr); g.FeatureList.FeatureCount=len(g.FeatureList.FeatureRecord)
    for stag in ('DFLT','latn'):
        s=get_script(g,stag)
        base=list(s.DefaultLangSys.FeatureIndex) if s.DefaultLangSys else []
        locl_indices={i for i,r in enumerate(g.FeatureList.FeatureRecord) if r.FeatureTag=='locl'}
        base=[i for i in base if i not in locl_indices]
        set_langsys(s,'ENG ',base+[insert_idx])
    hani=get_script(g,'hani'); zhs=None
    for lr in hani.LangSysRecord:
        if lr.LangSysTag=='ZHS ': zhs=list(lr.LangSys.FeatureIndex)
    if zhs is not None: set_langsys(get_script(g,'DFLT'),'ZHS ',zhs)

def build_master(w,style):
    n=TTFont(NFILES[w]); h=TTFont(HFILES[w]); z=TTFont(ZFILES[w])
    opt=Options(); opt.layout_features=['*']; opt.name_IDs=['*']; opt.name_legacy=True; opt.name_languages=['*']; opt.glyph_names=True; opt.hinting=False
    sub=Subsetter(options=opt); sub.populate(unicodes=UNICODES); sub.subset(n)
    order=list(n.getGlyphOrder()); cmap=n.getBestCmap(); zc=z.getBestCmap(); hc=h.getBestCmap()
    for cp in (0x2014,0x2E3A,0x2E3B):
        if cp in cmap and cp in zc: copy_glyph(n,z,zc[cp],cmap[cp])
    for dn,sn in [('uni2015','uniFE31'),('glyph30430','uni2E3A.vert'),('glyph30431','uni2E3B.vert')]:
        if dn in order and sn in z.getGlyphOrder(): copy_glyph(n,z,sn,dn)
    mapping={}
    for cp in EN_CPS:
        base=cmap[cp]; alt=base+'.en'; k=2
        while alt in order: alt=base+f'.en{k}'; k+=1
        order.append(alt); copy_glyph(n,h,hc[cp],alt); mapping[base]=alt
    n.setGlyphOrder(order)
    add_english_locl(n,mapping)
    set_static_names(n,w,style)
    try: buildStatTable(n,[dict(tag='wght',name='Weight',values=[dict(value=w,name=style,flags=0x2 if w==400 else 0)])])
    except Exception: pass
    p=WORK/f'{PS}-{style}.ttf'; n.save(p,reorderTables=True); n.close(); h.close(); z.close(); return p

masters=[]
for w,s in MASTER_WEIGHTS.items():
    p=build_master(w,s); masters.append((w,s,p)); print('master',w,p.stat().st_size,flush=True)

ds=DesignSpaceDocument(); ax=AxisDescriptor(); ax.name='Weight'; ax.tag='wght'; ax.minimum=100; ax.default=400; ax.maximum=900; ds.addAxis(ax)
for w,s,p in masters:
    src=SourceDescriptor(); src.path=str(p); src.name=f'master.{w}'; src.familyName=FAMILY; src.styleName=s; src.location={'Weight':w}
    if w==400: src.copyInfo=True; src.copyLib=True; src.copyGroups=True; src.copyFeatures=True
    ds.addSource(src)
for w,s in ALL_WEIGHTS.items():
    ins=InstanceDescriptor(); ins.name=s; ins.familyName=FAMILY; ins.styleName=s; ins.location={'Weight':w}; ds.addInstance(ins)
dsp=WORK/f'{PS}.designspace'; ds.write(dsp)
vf,_,_=varlib_build(str(dsp),exclude=['BASE','GDEF','GPOS','GSUB'])
def400=TTFont(WORK/f'{PS}-Regular.ttf')
for tag in ('BASE','GDEF','GPOS','GSUB'):
    if tag in def400: vf[tag]=deepcopy(def400[tag])
def400.close()
nt=vf['name']
for k,v in {0:COPYRIGHT,1:FAMILY,2:'Regular',3:f'{VERSION};BridgeBuild;{PS}-VF',4:FAMILY,5:f'Version {VERSION}',6:PS,13:'SIL Open Font License, Version 1.1',14:'https://openfontlicense.org',16:FAMILY,17:'Regular',25:PS}.items(): setname(nt,k,v)
for inst,(w,s) in zip(vf['fvar'].instances,ALL_WEIGHTS.items()): inst.subfamilyNameID=nt.addName(s,platforms=((3,1,0x409),(1,0,0)))
try: buildStatTable(vf,[dict(tag='wght',name='Weight',values=[dict(value=w,name=s,flags=0x2 if w==400 else 0) for w,s in ALL_WEIGHTS.items()])])
except Exception: pass
vfp=OUT/'fonts'/'variable'/f'{PS}-Variable.ttf'; vf.save(vfp,reorderTables=True); vf.close()
for w,s in ALL_WEIGHTS.items():
    f=TTFont(vfp); st=instantiateVariableFont(f,{'wght':w},inplace=False,optimize=True,static=True); set_static_names(st,w,s); op=OUT/'fonts'/'static'/f'{PS}-{s}.ttf'; st.save(op,reorderTables=True); st.close(); f.close()
f=TTFont(vfp); f.flavor='woff2'; wp=OUT/'fonts'/'web'/f'{PS}-Variable.woff2'; f.save(wp); f.close()
licdir=OUT/'licenses'; licdir.mkdir(exist_ok=True)
shutil.copy(SRC/'hanken/OFL.txt',licdir/'OFL-Hanken-Grotesk.txt'); shutil.copy(SRC/'noto/OFL.txt',licdir/'OFL-Noto-Sans-SC.txt'); shutil.copy(ROOT/'CJKPunctBridge/OFL-Zhudou-Sans.txt',licdir/'OFL-Zhudou-Sans.txt')
htext=(SRC/'hanken/OFL.txt').read_text(encoding='utf-8'); body=htext[htext.index('This Font Software'):]
(OUT/'OFL.txt').write_text(COPYRIGHT+'\n\n'+body,encoding='utf-8')
for p in [OUT/'fonts'/'static'/f'{PS}-Regular.ttf',vfp]:
    f=TTFont(p); tags=sorted(set(r.FeatureTag for r in f['GSUB'].table.FeatureList.FeatureRecord)); cm=f.getBestCmap(); print('validate',p.name,len(cm),'vhea' in f,'vmtx' in f,tags,cm.get(0x2014),cm.get(0x2E3A),flush=True)
    if 'fvar' in f: print('axis',[(a.axisTag,a.minValue,a.defaultValue,a.maxValue) for a in f['fvar'].axes],flush=True)
    f.close()
