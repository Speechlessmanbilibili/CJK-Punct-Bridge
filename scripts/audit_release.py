from pathlib import Path
from fontTools.ttLib import TTFont

REGIONS=('ZHS ','ZHT ','JAN ','KOR ')

def langsys(font,script,lang=None):
 t=font['GSUB'].table
 sr=next((x for x in t.ScriptList.ScriptRecord if x.ScriptTag==script),None)
 if sr is None:return None
 if lang is None:return sr.Script.DefaultLangSys
 return next((x.LangSys for x in sr.Script.LangSysRecord if x.LangSysTag==lang),None)

def tags(font,script,lang=None):
 ls=langsys(font,script,lang)
 if ls is None:return set()
 rec=font['GSUB'].table.FeatureList.FeatureRecord
 return {rec[i].FeatureTag for i in ls.FeatureIndex}

def singlemap(font,script,lang,feature):
 t=font['GSUB'].table; ls=langsys(font,script,lang); out={}
 if ls is None:return out
 for fi in ls.FeatureIndex:
  fr=t.FeatureList.FeatureRecord[fi]
  if fr.FeatureTag!=feature:continue
  for li in fr.Feature.LookupListIndex:
   lk=t.LookupList.Lookup[li]
   for st in lk.SubTable:
    typ=lk.LookupType
    if typ==7: st=st.ExtSubTable; typ=st.ExtensionLookupType
    if typ==1 and hasattr(st,'mapping'): out.update(st.mapping)
 return out

def audit(path):
 f=TTFont(path); cmap=f.getBestCmap()
 assert len(cmap)>=180
 assert {'ccmp','dlig','locl','vert','vrt2'} <= tags(f,'DFLT',None)
 assert 'ccmp' not in tags(f,'DFLT','ENG ')
 for lang in REGIONS:
  assert {'ccmp','dlig','locl','vert','vrt2'} <= tags(f,'DFLT',lang), lang
 quote=cmap[0x201C]
 for lang in ('ZHT ','JAN ','KOR ','ENG '):
  alt=singlemap(f,'DFLT',lang,'locl').get(quote)
  assert alt and alt!=quote,(lang,quote,alt)
 comma=cmap[0x3001]
 for lang in ('JAN ','KOR '):
  h=singlemap(f,'DFLT',lang,'locl').get(comma,comma)
  v=singlemap(f,'DFLT',lang,'vert').get(h,h)
  v=singlemap(f,'DFLT',lang,'vrt2').get(v,v)
  assert v!=h,(lang,h,v)
 assert 'vhea' in f and 'vmtx' in f
 if 'fvar' in f:
  a=next(x for x in f['fvar'].axes if x.axisTag=='wght')
  assert (a.minValue,a.defaultValue,a.maxValue)==(100.0,400.0,900.0)
  assert len(f['fvar'].instances)==9
 f.close()

if __name__=='__main__':
 import sys
 for arg in sys.argv[1:]: audit(Path(arg)); print('OK',arg)
