# FONTLOG

## 1.200 — 2026-08-24

- Expanded Hanken `locl` coverage from eight ambiguous English marks to all 46 punctuation code points shared by the bridge and the pinned Google Fonts Hanken Grotesk distribution.
- Made ASCII digits a hard bridge exclusion so `0`–`9` always fall through to Hanken Grotesk in every language.
- Applied the Hanken punctuation path to the configured registered Western languages in Common, Latin, Cyrillic, and Greek runs, while keeping every default LangSys on Noto Sans SC.
- Added explicit Noto regional aliases for Chinese Hong Kong/Macao/phonetic tags and Korean old Hangul.
- Hardened release audits to check the complete Hanken punctuation mapping, every Western language system, all CJK regional aliases, and the no-ligation dash policy.
- Split Noto SC's shared `U+00B7`/`U+2022` source glyph inside the bridge so both code points can select their distinct Hanken designs without changing CJK behavior.
- Repaired the pinned Zhudou v2.000 release-asset URL after the upstream archive name changed.
- Documented that every Noto Sans and Hanken Grotesk build input must come from a pinned Google Fonts repository commit.
- Replaced inherited upstream identity fields with explicit project authorship, modification copyright, source attribution, repository links, OFL details, and a project-aligned internal revision in every static, variable, and web font.

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
