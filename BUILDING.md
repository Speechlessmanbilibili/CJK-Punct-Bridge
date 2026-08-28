# Building CJK Punct Bridge

The build uses only the actual **Google Fonts repository distributions** of Noto Sans SC/TC/JP/KR and Hanken Grotesk, plus Zhudou Sans v2.000. It does not substitute author-repository, system, or mirror builds for Noto or Hanken. Exact immutable source URLs and SHA-256 hashes are in `SOURCES.md`.

## 1. Prefetch sources (networked step)

```bash
python scripts/fetch_sources.py
```

This creates the gitignored `upstream/` cache. The source binaries are deliberately not committed.

## 2. Build offline

Once `upstream/` exists, no network access is required:

```bash
python scripts/build.py
python scripts/audit_release.py fonts/static/CJKPunctBridge-Regular.ttf fonts/variable/CJKPunctBridge-Variable.ttf
python scripts/check_dash_matrix.py fonts/static/CJKPunctBridge-Regular.ttf fonts/variable/CJKPunctBridge-Variable.ttf
```

Outputs are written under `fonts/static/`, `fonts/variable/`, and `fonts/web/`;
`fonts/web/` contains WOFF2 versions of every static and variable face. Release
binaries remain outside normal Git history.

## 3. Italic family

The italic family is a separate single-axis variable font plus nine static
italics, mirroring the pinned Hanken Grotesk release layout (upright and
italic are distinct `wght`-only variable files sharing the typographic family
name). Build it with:

```bash
CJK_PUNCT_ITALIC=1 python scripts/build.py
```

This emits `fonts/variable/CJKPunctBridge-Italic-Variable.ttf`,
`fonts/web/CJKPunctBridge-Italic-Variable.woff2`, and the nine
`fonts/static/CJKPunctBridge-*Italic.ttf` faces.

In italics, the Western punctuation comes from the pinned Google Fonts
**Hanken Grotesk Italic** distribution (true italic designs), while the CJK
regional punctuation and Zhudou dashes use a uniform synthetic 10-degree shear
(`scripts/build.py` `shear_font()`): simple glyphs keep their exact point
structure and flags so varLib masters stay interpolatable, composites are
decomposed identically on every master, advance widths stay unchanged, and
left side bearings are recomputed from the new bounds.

Italic outputs use Office-compatible style linking: `OS/2.fsSelection`
contains `ITALIC` without `REGULAR`; Bold Italic contains `ITALIC + BOLD`.
Legacy name ID 2 carries the linked style while typographic name ID 17 retains
the complete weight and posture.

## 4. Interrobang variant

After both base variable fonts exist, place the pinned Inter 4.001 inputs from
`SOURCES.md` in `upstream/` or set `INTER_VF` explicitly:

```bash
INTER_VF=upstream/InterVariable.ttf python scripts/build_interrobang.py
CJK_PUNCT_ITALIC=1 INTER_VF=upstream/InterVariable-Italic.ttf python scripts/build_interrobang.py
```

Each pass builds nine static faces and one variable font under
`fonts-interrobang/`, with matching WOFF2 files under its `web/` directory.
Inter U+203D is instantiated at the matching weight for
every master. Validation requires nine distinct outlines, matching
variable/static endpoints, fewer than 60,000 glyphs, and a `gvar` table below
64 MiB.

The optional family maps literal `U+203D` directly to the same half-width
weight-matched glyph used by the `?!`/`!?` ligatures. The standard bridge does
not gain this mapping.

## 5. Minimal Western Interrobang Bridge

Build the independent Inter-only companion after the pinned Inter files are in
`upstream/`:

```bash
python scripts/build_interrobang_bridge.py
INTERROBANG_BRIDGE_ITALIC=1 python scripts/build_interrobang_bridge.py
```

It emits nine static weights and one variable font per posture under
`fonts-interrobang-bridge/`, plus matching WOFF2 files. Validation requires the cmap to contain exactly
`!`, `?`, and `U+203D`, both `?!` and `!?` to target the encoded interrobang,
and all nine Inter weight outlines to remain distinct.

## Merge strategy

1. Determine punctuation code points shared by the four Google Fonts Noto CJK distributions; `U+002D` hyphen-minus remains with the normal Latin font.
   ASCII `U+0030`–`U+0039` are a hard exclusion: the bridge must never intercept digits, which are supplied by Hanken Grotesk in downstream stacks for every language.
2. Use Noto Sans SC as the default OpenType/layout skeleton and make the no-language default follow its `ZHS` behavior.
3. Preserve Noto SC punctuation GSUB behavior including `ccmp`, `dlig`, width alternates, `vert`, and `vrt2`.
4. Copy the final localized punctuation outlines from Noto Sans TC/JP/KR and attach them to the corresponding Chinese, Japanese, and Korean `locl` language systems, including registered Hong Kong, Macao, phonetic-Chinese, and old-Hangul aliases. Regional vertical targets are copied and attached through `vert` / `vrt2`.
5. Replace Chinese SC/TC one-em/two-em/three-em dash outlines with Zhudou-derived horizontal and vertical forms while retaining the Noto continuous-dash machinery.
6. Compute the full punctuation intersection between the bridge and pinned Google Fonts Hanken Grotesk (currently 46 code points). For every configured explicit Western language under `DFLT`, `latn`, `cyrl`, or `grek`, attach those Hanken alternates through `locl` and expose no Noto punctuation substitutions. Every default language system remains Noto SC, and explicit CJK tags remain on their corresponding Noto regional paths.
7. Build five static masters, interpolate a `wght` 100–900 variable TTF, instantiate nine static weights, and emit WOFF2. The italic family follows the same pipeline with Hanken Grotesk Italic as the Western source and a synthetic shear applied to the CJK sources.

The regional Google Fonts Noto punctuation subsets retain the same relevant punctuation GSUB feature set after subsetting; Korean-only extra shaping lookups outside punctuation are removed by the punctuation closure and are not needed by this bridge.

`scripts/language_systems.py` contains the OpenType 1.9 registered tags used by the project's Common/Latin/Cyrillic/Greek policy. It covers all project locales, a broad modern/historic Western set, and every explicit language system in the pinned Hanken source. It deliberately does not change any script's default LangSys.
