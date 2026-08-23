from pathlib import Path
from copy import deepcopy
import unicodedata
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
from fontTools.otlLib.builder import buildLookup, buildSingleSubstSubtable, buildStatTable
from fontTools.ttLib.tables import otTables

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'upstream'
OUT=ROOT/'dist'; WORK=ROOT/'build'
for p in (OUT/'static',OUT/'variable',OUT/'web',WORK): p.mkdir(parents=True,exist_ok=True)
FAMILY='CJK Punct Bridge'; PS='CJKPunctBridge'; VERSION='1.000'
MASTER={100:'Thin',300:'Light',400:'Regular',700:'Bold',900:'Black'}
ALL={100:'Thin',200:'ExtraLight',300:'Light',400:'Regular',500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black'}
N={w:SRC/'noto'/f'NotoSansSC-{s}.ttf' for w,s in MASTER.items()}
H={w:SRC/'hanken'/f'HankenGrotesk-{s}.ttf' for w,s in MASTER.items()}
Z={100:SRC/'zhudou/ZhudouSans-ExtraLight.ttf',300:SRC/'zhudou/ZhudouSans-Light.ttf',400:SRC/'zhudou/ZhudouSans-Regular.ttf',700:SRC/'zhudou/ZhudouSans-Bold.ttf',900:SRC/'zhudou/ZhudouSans-Heavy.ttf'}

z0,n0,h0=TTFont(Z[400]),TTFont(N[400]),TTFont(H[400]); zc,nc,hc=z0.getBestCmap(),n0.getBestCmap(),h0.getBestCmap()
UNICODES=sorted(cp for cp in set(zc)&set(nc) if unicodedata.category(chr(cp)).startswith('P') and cp!=0x002D)
EN_CPS=[cp for cp in (0x00B7,0x2013,0x2014,0x2018,0x2019,0x201C,0x201D,0x2026) if cp in hc and cp in UNICODES]
for f in (z0,n0,h0): f.close()
COPYRIGHT="Portions Copyright 2021 The Hanken Grotesk Project Authors. Portions Copyright 2014-2021 Adobe, with Reserved Font Name 'Source'. Portions Copyright 2022 Buernia, with Reserved Font Names 'Zhudou' and '煮豆'; portions Copyright 2015 Google Inc. CJK Punct Bridge is a modified/combined font distributed under SIL Open Font License 1.1."

def setname(nt,nid,val):
    nt.names=[r for r in nt.names if r.nameID!=nid]; nt.setName(val,nid,3,1,0x409)
    try: val.encode('mac_roman'); nt.setName(val,nid,1,0,0)
    except UnicodeEncodeError: pass

def names(f,w,style):
    legacy=FAMILY if w in (400,700) else f'{FAMILY} {style}'; sub='Bold' if w==700 else 'Regular'; full=FAMILY if w==400 else f'{FAMILY} {style}'
    vals={0:COPYRIGHT,1:legacy,2:sub,3:f'{VERSION};BridgeBuild;{PS}-{style}',4:full,5:f'Version {VERSION}',6:f'{PS}-{style}',13:'SIL Open Font License, Version 1.1',14:'https://openfontlicense.org',16:FAMILY,17:style,25:PS}
    for k,v in vals.items(): setname(f['name'],k,v)
    o=f['OS/2']; o.usWeightClass=w; o.achVendID='NONE'; o.fsSelection &= ~((1<<0)|(1<<5)|(1<<6)|(1<<9)); f['head'].macStyle &= ~3
    if w==400:o.fsSelection|=1<<6
    if w==700:o.fsSelection|=1<<5; f['head'].macStyle|=1

def copyglyph(dst,src,sn,dn):
    dst['glyf'][dn]=deepcopy(src['glyf'][sn]); dst['hmtx'].metrics[dn]=src['hmtx'].metrics[sn]
    if 'vmtx' in dst:
        dst['vmtx'].metrics[dn]=src['vmtx'].metrics.get(sn,(1000,0)) if 'vmtx' in src else (1000,0)

def langsys(g,script,lang=None):
    for sr in g.ScriptList.ScriptRecord:
        if sr.ScriptTag!=script: continue
        if lang is None:return sr.Script.DefaultLangSys
        for lr in sr.Script.LangSysRecord:
            if lr.LangSysTag==lang:return lr.LangSys

def singlemap(g,script,lang,tag):
    ls=langsys(g,script,lang); out={}
    if not ls:return out
    for fi in ls.FeatureIndex:
        fr=g.FeatureList.FeatureRecord[fi]
        if fr.FeatureTag!=tag:continue
        for li in fr.Feature.LookupListIndex:
            lk=g.LookupList.Lookup[li]
            for st in lk.SubTable:
                typ=lk.LookupType
                if typ==7:st,typ=st.ExtSubTable,st.ExtensionLookupType
                if typ==1 and hasattr(st,'mapping'):out.update(st.mapping)
    return out

def get_script(g,tag):
    for sr in g.ScriptList.ScriptRecord:
        if sr.ScriptTag==tag:return sr.Script
    sr=otTables.ScriptRecord();sr.ScriptTag=tag;sr.Script=otTables.Script();sr.Script.DefaultLangSys=None;sr.Script.LangSysRecord=[];sr.Script.LangSysCount=0;g.ScriptList.ScriptRecord.append(sr);g.ScriptList.ScriptRecord.sort(key=lambda r:r.ScriptTag);g.ScriptList.ScriptCount=len(g.ScriptList.ScriptRecord);return sr.Script

def set_lang(s,tag,idxs):
    for lr in s.LangSysRecord:
        if lr.LangSysTag==tag:ls=lr.LangSys;break
    else:
        lr=otTables.LangSysRecord();lr.LangSysTag=tag;ls=otTables.LangSys();ls.LookupOrder=None;lr.LangSys=ls;s.LangSysRecord.append(lr);s.LangSysRecord.sort(key=lambda r:r.LangSysTag);s.LangSysCount=len(s.LangSysRecord)
    ls.ReqFeatureIndex=0xFFFF;ls.FeatureIndex=sorted(set(idxs));ls.FeatureCount=len(ls.FeatureIndex)

def add_eng_locl(f,mapping):
    g=f['GSUB'].table; st=buildSingleSubstSubtable(mapping);lk=buildLookup([st],table='GSUB');g.LookupList.Lookup.append(lk);g.LookupList.LookupCount=len(g.LookupList.Lookup);li=len(g.LookupList.Lookup)-1
    fr=otTables.FeatureRecord();fr.FeatureTag='locl';feat=otTables.Feature();feat.FeatureParams=None;feat.LookupListIndex=[li];feat.LookupCount=1;fr.Feature=feat
    pos=next((i for i,r in enumerate(g.FeatureList.FeatureRecord) if r.FeatureTag>'locl'),len(g.FeatureList.FeatureRecord))
    for sr in g.ScriptList.ScriptRecord:
        systems=([sr.Script.DefaultLangSys] if sr.Script.DefaultLangSys else [])+[x.LangSys for x in sr.Script.LangSysRecord]
        for ls in systems:ls.FeatureIndex=[i+1 if i>=pos else i for i in ls.FeatureIndex]
    g.FeatureList.FeatureRecord.insert(pos,fr);g.FeatureList.FeatureCount=len(g.FeatureList.FeatureRecord)
    blocked={i for i,r in enumerate(g.FeatureList.FeatureRecord) if r.FeatureTag in ('locl','ccmp')}
    for stag in ('DFLT','latn'):
        s=get_script(g,stag);base=list(s.DefaultLangSys.FeatureIndex) if s.DefaultLangSys else [];set_lang(s,'ENG ',[i for i in base if i not in blocked]+[pos])
    hz=langsys(g,'hani','ZHS ')
    if hz:set_lang(get_script(g,'DFLT'),'ZHS ',list(hz.FeatureIndex))

def build_master(w,style):
    n,h,z=TTFont(N[w]),TTFont(H[w]),TTFont(Z[w])
    opt=Options();opt.layout_features=['*'];opt.name_IDs=['*'];opt.name_legacy=True;opt.name_languages=['*'];opt.glyph_names=True;opt.hinting=False
    ss=Subsetter(options=opt);ss.populate(unicodes=UNICODES);ss.subset(n)
    order=list(n.getGlyphOrder());cm=n.getBestCmap();zc=z.getBestCmap();hc=h.getBestCmap();g=n['GSUB'].table
    zhs_locl=singlemap(g,'hani','ZHS ','locl');zhs_vert=singlemap(g,'hani','ZHS ','vert')
    src={0x2014:'uniFE31',0x2E3A:'uni2E3A.vert',0x2E3B:'uni2E3B.vert'};verts={}
    for cp,zvert in src.items():
        base=cm[cp];copyglyph(n,z,zc[cp],base);zh=zhs_locl.get(base,base);copyglyph(n,z,zc[cp],zh);vt=zhs_vert.get(zh);verts[cp]=vt
        if vt and zvert in z.getGlyphOrder():copyglyph(n,z,zvert,vt)
    # Make vertical dash substitution work without an explicit zh-CN language tag.
    dflt=langsys(g,'DFLT')
    if dflt:
        for fi in dflt.FeatureIndex:
            fr=g.FeatureList.FeatureRecord[fi]
            if fr.FeatureTag!='vert':continue
            for li in fr.Feature.LookupListIndex:
                lk=g.LookupList.Lookup[li]
                for st in lk.SubTable:
                    typ=lk.LookupType
                    if typ==7:st,typ=st.ExtSubTable,st.ExtensionLookupType
                    if typ==1 and hasattr(st,'mapping'):
                        for cp,vt in verts.items():
                            if vt:st.mapping[cm[cp]]=vt
                        break
    mapping={}
    for cp in EN_CPS:
        base=cm[cp];alt=base+'.en';i=2
        while alt in order:alt=f'{base}.en{i}';i+=1
        order.append(alt);copyglyph(n,h,hc[cp],alt);mapping[base]=alt
    n.setGlyphOrder(order);add_eng_locl(n,mapping);names(n,w,style);buildStatTable(n,[dict(tag='wght',name='Weight',values=[dict(value=w,name=style,flags=0x2 if w==400 else 0)])])
    p=WORK/f'{PS}-{style}.ttf';n.save(p,reorderTables=True);[x.close() for x in (n,h,z)];return p

masters=[(w,s,build_master(w,s)) for w,s in MASTER.items()]
ds=DesignSpaceDocument();ax=AxisDescriptor();ax.name='Weight';ax.tag='wght';ax.minimum=100;ax.default=400;ax.maximum=900;ds.addAxis(ax)
for w,s,p in masters:
    x=SourceDescriptor();x.path=str(p);x.name=f'master.{w}';x.familyName=FAMILY;x.styleName=s;x.location={'Weight':w};x.copyInfo=x.copyLib=x.copyGroups=x.copyFeatures=(w==400);ds.addSource(x)
for w,s in ALL.items():
    x=InstanceDescriptor();x.name=s;x.familyName=FAMILY;x.styleName=s;x.location={'Weight':w};ds.addInstance(x)
dsp=WORK/f'{PS}.designspace';ds.write(dsp);vf,_,_=varlib_build(str(dsp),exclude=['BASE','GDEF','GPOS','GSUB']);r=TTFont(WORK/f'{PS}-Regular.ttf')
for tag in ('BASE','GDEF','GPOS','GSUB'):
    if tag in r:vf[tag]=deepcopy(r[tag])
r.close()
for k,v in {0:COPYRIGHT,1:FAMILY,2:'Regular',3:f'{VERSION};BridgeBuild;{PS}-VF',4:FAMILY,5:f'Version {VERSION}',6:PS,13:'SIL Open Font License, Version 1.1',14:'https://openfontlicense.org',16:FAMILY,17:'Regular',25:PS}.items():setname(vf['name'],k,v)
for inst,(w,s) in zip(vf['fvar'].instances,ALL.items()):inst.subfamilyNameID=vf['name'].addName(s,platforms=((3,1,0x409),(1,0,0)))
buildStatTable(vf,[dict(tag='wght',name='Weight',values=[dict(value=w,name=s,flags=0x2 if w==400 else 0) for w,s in ALL.items()])]);vfp=OUT/'variable'/f'{PS}-Variable.ttf';vf.save(vfp,reorderTables=True);vf.close()
for w,s in ALL.items():
    f=TTFont(vfp);st=instantiateVariableFont(f,{'wght':w},inplace=False,optimize=True,static=True);names(st,w,s);st.save(OUT/'static'/f'{PS}-{s}.ttf',reorderTables=True);st.close();f.close()
f=TTFont(vfp);f.flavor='woff2';f.save(OUT/'web'/f'{PS}-Variable.woff2');f.close()
print('Built',OUT)
