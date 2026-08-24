from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from language_systems import (
 CJK_LANGUAGE_ALIASES,
 HANKEN_SHARED_PUNCTUATION,
 WESTERN_LANGUAGE_SYSTEMS,
 WESTERN_SCRIPT_TAGS,
)
from font_metadata import audit_metadata

REGIONS=tuple(tag for aliases in CJK_LANGUAGE_ALIASES.values() for tag in aliases)

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
 unique_id='CJKPunctBridge-VF' if 'fvar' in f else path.stem
 audit_metadata(f,unique_id)
 assert len(cmap)>=180
 assert not set(range(0x30,0x3A)) & set(cmap),(path,'ASCII digits must be supplied by Hanken, not the bridge')
 assert {'ccmp','dlig','locl','vert','vrt2'} <= tags(f,'DFLT',None)
 for lang in REGIONS:
  assert {'ccmp','dlig','locl','vert','vrt2'} <= tags(f,'DFLT',lang), lang
 for script in WESTERN_SCRIPT_TAGS:
  assert {'ccmp','dlig','locl','vert','vrt2'} <= tags(f,script,None),script
  for lang in WESTERN_LANGUAGE_SYSTEMS[script]:
   assert tags(f,script,lang)=={'locl'},(script,lang,tags(f,script,lang))
 quote=cmap[0x201C]
 for lang in ('ZHT ','ZHH ','ZHTM','JAN ','KOR ','KOH '):
  alt=singlemap(f,'DFLT',lang,'locl').get(quote)
  assert alt and alt!=quote,(lang,quote,alt)
 expected_sources={cmap[cp] for cp in HANKEN_SHARED_PUNCTUATION}
 assert len(expected_sources)==len(HANKEN_SHARED_PUNCTUATION)
 for script in WESTERN_SCRIPT_TAGS:
  mapping=singlemap(f,script,WESTERN_LANGUAGE_SYSTEMS[script][0],'locl')
  assert set(mapping)==expected_sources,(script,len(mapping),len(expected_sources))
  for cp in HANKEN_SHARED_PUNCTUATION:
   source=cmap[cp]; alt=mapping.get(source)
   assert alt and alt!=source,(script,hex(cp),source,alt)
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

def glyph_signature(font,glyph):
 g=font['glyf'][glyph]
 coords,end_pts,flags=g.getCoordinates(font['glyf'])
 return (tuple(coords),tuple(end_pts),bytes(flags),font['hmtx'].metrics[glyph])

def audit_hanken_provenance(path,source_path):
 f=TTFont(path); h=TTFont(source_path)
 if 'fvar' in h:
  h=instantiateVariableFont(h,{'wght':400},inplace=False,optimize=True,static=True)
 cmap=f.getBestCmap(); hcmap=h.getBestCmap()
 mapping=singlemap(f,'latn','ENG ','locl')
 for cp in HANKEN_SHARED_PUNCTUATION:
  assert glyph_signature(f,mapping[cmap[cp]])==glyph_signature(h,hcmap[cp]),hex(cp)
 f.close();h.close()

if __name__=='__main__':
 import sys
 root=Path(__file__).resolve().parents[1]
 hanken=root/'upstream'/'HankenGrotesk-wght.ttf'
 for arg in sys.argv[1:]:
  path=Path(arg);audit(path)
  if hanken.exists() and path.name=='CJKPunctBridge-Regular.ttf':
   audit_hanken_provenance(path,hanken)
  print('OK',arg)
