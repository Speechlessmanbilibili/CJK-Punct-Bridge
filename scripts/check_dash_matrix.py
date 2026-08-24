#!/usr/bin/env python3
from pathlib import Path
from fontTools.ttLib import TTFont
import sys
from language_systems import WESTERN_LANGUAGE_SYSTEMS, WESTERN_SCRIPT_TAGS

def _langsys(gsub,script,lang):
 for sr in gsub.ScriptList.ScriptRecord:
  if sr.ScriptTag==script:
   if lang is None:return sr.Script.DefaultLangSys
   for lr in sr.Script.LangSysRecord:
    if lr.LangSysTag==lang:return lr.LangSys
 return None

def _apply(glyphs,lookup):
 out=glyphs[:]
 for st in lookup.SubTable:
  typ=lookup.LookupType
  if typ==7: st=st.ExtSubTable; typ=st.ExtensionLookupType
  if typ==1 and hasattr(st,'mapping'): out=[st.mapping.get(g,g) for g in out]
  elif typ==4:
   ligs=getattr(st,'ligatures',{}); result=[]; i=0
   while i<len(out):
    hit=None
    for lig in ligs.get(out[i],[]):
     seq=[out[i],*lig.Component]
     if out[i:i+len(seq)]==seq and (hit is None or len(seq)>hit[0]): hit=(len(seq),lig.LigGlyph)
    if hit: result.append(hit[1]); i+=hit[0]
    else: result.append(out[i]); i+=1
   out=result
 return out

def _shape(font,text,script,lang,vertical):
 cmap=font.getBestCmap(); gsub=font['GSUB'].table; glyphs=[cmap[ord(ch)] for ch in text]
 ls=_langsys(gsub,script,lang) or _langsys(gsub,script,None)
 for fi in ls.FeatureIndex:
  fr=gsub.FeatureList.FeatureRecord[fi]; tag=fr.FeatureTag
  if tag not in ('ccmp','locl','vert','vrt2'):continue
  if tag in ('vert','vrt2') and not vertical:continue
  for li in fr.Feature.LookupListIndex:glyphs=_apply(glyphs,gsub.LookupList.Lookup[li])
 return glyphs

def _orientation(font,g):
 x=font['glyf'][g]; x.recalcBounds(font['glyf']); w=x.xMax-x.xMin; h=x.yMax-x.yMin
 return 'horizontal' if w>h else 'vertical' if h>w else 'square'

def check_font(path):
 f=TTFont(path); assert 'GSUB' in f and 'vhea' in f and 'vmtx' in f
 for count,text in enumerate(('—','——','———'),1):
  for script,lang in (('DFLT',None),('hani','ZHS '),('hani','ZHT '),('hani','JAN '),('hani','KOR ')):
   h=_shape(f,text,script,lang,False); v=_shape(f,text,script,lang,True)
   assert len(h)==1,(path,text,lang,'not ligated',h)
   assert _orientation(f,h[0])=='horizontal',(path,text,lang,'horizontal',h)
   assert len(v)==1,(path,text,lang,'vertical not ligated',v)
   expected='horizontal' if lang=='KOR ' and count==1 else 'vertical'
   assert _orientation(f,v[0])==expected,(path,text,lang,'vertical orientation',v,_orientation(f,v[0]),expected)
  for script in WESTERN_SCRIPT_TAGS:
   for lang in WESTERN_LANGUAGE_SYSTEMS[script]:
    western=_shape(f,text,script,lang,False)
    assert len(western)==count,(path,text,script,lang,'unexpectedly ligated',western)
    assert all(_orientation(f,g)=='horizontal' for g in western)
 f.close()

def main():
 targets=[Path(x) for x in sys.argv[1:]]
 if not targets:
  root=Path(__file__).resolve().parents[1]; targets=sorted((root/'fonts').rglob('*.ttf'))+sorted((root/'fonts').rglob('*.woff2'))
 if not targets:raise SystemExit('No font files found')
 for p in targets:check_font(p)
 print(f'PASS: {len(targets)} font file(s)')
if __name__=='__main__':main()
