# FONTLOG

## 1.100 — 2026-08-24

- Added `ZHT` localized punctuation from Noto Sans TC.
- Added `JAN` localized punctuation from Noto Sans JP.
- Added `KOR` localized punctuation from Noto Sans KR.
- Kept unspecified/default and `ZHS` punctuation on the SC path.
- Kept Zhudou-derived one-/two-/three-em dash behavior across every CJK/default path.
- Added regional vertical punctuation targets for `vert` / `vrt2`.
- Preserved the Hanken `ENG` `locl` path and its separate repeated em dashes.

## 1.000 — 2026-08-23

- Initial public release.
- Rebuilt the punctuation layer on Noto Sans SC.
- Default `U+2014` changed to a Zhudou-derived CJK em dash.
- Retained Noto `ccmp`, `vert`, `vrt2`, vertical metrics, and other punctuation OpenType behavior.
- Replaced horizontal and vertical one-/two-/three-em dash outlines with Zhudou-derived forms.
- Added `ENG` `locl` alternates from Hanken Grotesk for ambiguous shared punctuation.
- Disabled the CJK continuous-dash `ccmp` path for `ENG`, so repeated English em dashes remain separate Hanken forms.
- Fixed the Simplified-Chinese `locl` / `vert` target mapping so horizontal Chinese dashes cannot receive vertical outlines.
- Added variable, static, and WOFF2 builds.
- Added regression checks for horizontal/vertical dash shaping and language-sensitive behavior.
