from pathlib import Path
import hashlib, urllib.request, zipfile

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/'upstream'
UP.mkdir(exist_ok=True)
SOURCES={
 'NotoSansSC-wght.ttf':('https://raw.githubusercontent.com/google/fonts/2894aab31764f10f29c421bdfd2340d3b382d384/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf','a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da'),
 'NotoSansTC-wght.ttf':('https://raw.githubusercontent.com/google/fonts/b950a7257470b900078f2bf3223823a8602de7e1/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf','864727d210d54f2537bbe23b3a839436c3992af72de9322af5270897246bd44f'),
 'NotoSansJP-wght.ttf':('https://raw.githubusercontent.com/google/fonts/295d98a7a0c17c68f1341eaeea354e7960ea70d3/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf','c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f'),
 'NotoSansKR-wght.ttf':('https://raw.githubusercontent.com/google/fonts/4efc2774c63917927efe769ca845def6bd6debae/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf','194018e6b2b293a7964f037b25c0249ce1418bc9ab3c971060a03aa57861e252'),
 'HankenGrotesk-wght.ttf':('https://raw.githubusercontent.com/google/fonts/714891563e901b1a0d8ebcaaa003b01604793888/ofl/hankengrotesk/HankenGrotesk%5Bwght%5D.ttf','813b3f8fa0965405669a89b38e51bbefd95eef6b8e20d1cb2d8c10cce062662f'),
 'Zhudou.Sans-v2.000.zip':('https://github.com/Buernia/Zhudou-Sans/releases/download/v2.000/Zhudou.Sans-v2.000.zip','1a2718aa52c98d1ac7e18d60e0f1d61057b18e558e8196a3a770104855a6fc69'),
}
for name,(url,want) in SOURCES.items():
 p=UP/name
 if not p.exists():
  print('download',name,flush=True); urllib.request.urlretrieve(url,p)
 got=hashlib.sha256(p.read_bytes()).hexdigest()
 if got!=want: raise SystemExit(f'{name}: SHA-256 mismatch: {got}')
 print('ok',name,got)
z=UP/'Zhudou.Sans-v2.000.zip'; dest=UP/'zhudou'
if not dest.exists():
 with zipfile.ZipFile(z) as f: f.extractall(dest)
print('sources ready:',UP)
