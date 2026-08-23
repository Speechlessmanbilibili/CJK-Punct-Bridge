# Building CJK Punct Bridge

CJK Punct Bridge is built from OFL-licensed upstream font families. Exact source hashes are recorded in `SOURCES.md`.

## Stage 1: base SC/English bridge

`scripts/build.py` builds the SC-oriented base from Noto Sans SC, Zhudou Sans, and Hanken Grotesk. It retains Noto CJK layout/vertical machinery, substitutes Zhudou-derived dash forms, and adds the Hanken `ENG` `locl` path.

The resulting variable font is the input to the regional layer. The default language path remains SC.

## Stage 2: TC/JP/KR locale layer

`scripts/add_cjk_locales.py` adds Noto Sans TC/JP/KR punctuation as `ZHT`, `JAN`, and `KOR` `locl` alternatives. The three CJK dash code points are intentionally excluded from the regional replacement so all CJK/default paths keep the same Zhudou-derived continuous-dash behavior. Regional `vert` and `vrt2` targets are copied with their horizontal punctuation.

Set the source paths and run:

```bash
export CJK_PUNCT_BASE_VARIABLE=/path/to/CJKPunctBridge-Variable.ttf
export CJK_PUNCT_TC_VARIABLE=/path/to/NotoSansTC-wght.ttf
export CJK_PUNCT_JP_VARIABLE=/path/to/NotoSansJP-wght.ttf
export CJK_PUNCT_KR_VARIABLE=/path/to/NotoSansKR-wght.ttf
export CJK_PUNCT_LOCALE_BUILD_DIR=/path/to/dist
python scripts/add_cjk_locales.py
```

The locale layer is rebuilt at 100/300/400/700/900 masters, then interpolated back to a `wght` 100–900 variable font. Nine static weights and a variable WOFF2 are emitted as well.

## OpenType behavior

- Missing/unrecognized language tag: SC/default punctuation.
- `ZHS`: SC punctuation.
- `ZHT`: TC punctuation.
- `JAN`: JP punctuation.
- `KOR`: KR punctuation.
- `ENG`: Hanken shared punctuation; CJK repeated-em-dash `ccmp` disabled.
- CJK/default paths retain continuous `——` / `———` and CJK vertical dash forms.

## Distribution

Prebuilt TTF and WOFF2 files are published as GitHub Release assets and intentionally omitted from normal Git history.
