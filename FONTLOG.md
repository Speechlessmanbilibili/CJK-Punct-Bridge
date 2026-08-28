# FONTLOG

## 1.340 / v1.3.4 — 2026-08-28

- Replaced `!`, `?`, `¡`, and `¿` with matching Inter 4.001 outlines in the standard and optional families.
- Replaced full-width `！` and `？` with the same Inter outlines on a 1000-unit advance.
- Changed optional pair shaping to explicit 500+0 glyph slots for `?!`/`!?` and 1000+0 slots for `？！`/`！？`.

## 1.330 / v1.3.3 — 2026-08-28

- Added a literal `U+203D` cmap entry to every optional **CJK Punct Bridge ?!** static and variable font, pointing to the same half-width, weight-matched Inter outline used by the `?!` and `!?` ligatures.
- Kept the standard bridge family unchanged at `U+203D`; the direct-character mapping remains exclusive to the optional `?!` attachment.
- Advanced all standard and optional release fonts to internal version 1.330 and extended static/variable validation to enforce the cmap boundary.
- Added **Interrobang Bridge**, an independent Inter-only companion attachment, initially with cmap entries for `!`, `?`, and `U+203D`; v1.3.4 expands it to inverted and full-width forms and replaces standard ligatures with two-slot shaping.
- Added WOFF2 output for every static and variable face in the standard bridge, CJK Punct Bridge ?!, and Interrobang Bridge families.

## 1.320 — 2026-08-27

- Corrected upright/italic family metadata in both the standard and optional `?!` builds: italic faces now set `ITALIC` and clear `REGULAR`, while Bold Italic sets only `ITALIC + BOLD`.
- Corrected legacy subfamily names separately from typographic subfamily names so Office/GDI links Regular, Bold, Italic, and Bold Italic without losing the full weight name.
- Rebuilt the optional `?!` family from weight-matched Inter 4.001 instances instead of reusing the default 400 `U+203D` outline for every master.
- Added nine-weight outline, variable/static endpoint, glyph-count, and 64 MiB `gvar` validation for the optional variable fonts.

## 1.310 — 2026-08-26

- Added an optional companion family, **CJK Punct Bridge ?!**, shipped as a release attachment: `?!`/`!?` ligate to U+203D and full-width `？！`/`！？` ligate to a full-width left-aligned interrobang, enabled by default via `liga` across all regional `locl` variants.
- Sourced the interrobang outline from Inter's U+203D design (half-width extracted, full-width reusing the same contour with a 1000-unit advance); the variant is a separate family (`CJKPunctBridgeInterrobang-*`) with upright and italic variable fonts plus nine static weights each.
- The standard family remains the default distribution; the interrobang build is documented as an optional attachment.

## 1.300 — 2026-08-24

- Added a full italic family alongside the upright family, published as a separate single-axis variable font (`CJKPunctBridge-Italic-Variable.ttf`) plus nine static italics, exactly mirroring the pinned Hanken Grotesk release layout.
- Latin/Western punctuation in italics uses the true Hanken Grotesk Italic designs from the pinned Google Fonts distribution; CJK regional punctuation and Zhudou dashes use a uniform synthetic 10-degree shear because no true CJK italic design exists.
- The synthetic shear preserves simple-glyph point structure, flags, and end points so varLib masters stay interpolatable; composites are decomposed identically on every master; left side bearings are recomputed from the new bounds.
- Dropped the Noto-derived `BASE` ItemVariationStore from the variable build (Hanlink merge policy) so the layout tables compile cleanly against HVAR.
- Extended release audits to verify italic style bits, `italicAngle`, subfamily naming, and exact Hanken Italic provenance for the Western punctuation.

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
