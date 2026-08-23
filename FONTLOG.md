# FONTLOG

## 1.100 — 2026-08-24

- Expanded the bridge from SC/English to a single SC/TC/JP/KR/English language-aware punctuation font.
- Made unspecified language/region explicitly follow the SC `ZHS` punctuation path.
- Added `ZHT`, `JAN`, and `KOR` `locl` alternates from the actual Google Fonts Noto Sans TC/JP/KR distributions.
- Added regional vertical punctuation targets while retaining Noto `ccmp`, `dlig`, width features, `vert`, and `vrt2` behavior.
- Kept Zhudou-derived continuous Chinese dash outlines for SC and TC.
- Kept Hanken Grotesk punctuation for `ENG`, with CJK continuous-dash `ccmp` disabled on the English path.
- Switched build inputs to pinned Google Fonts variable TTFs with recorded SHA-256 hashes; builds can run fully offline after source prefetch.

## 1.000 — 2026-08-23

- Initial public release: Noto Sans SC punctuation base, Zhudou-derived Chinese dash outlines, and Hanken `ENG locl` punctuation.
