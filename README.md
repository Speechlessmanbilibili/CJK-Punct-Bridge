# CJK Punct Bridge

**CJK Punct Bridge is a small, language-aware punctuation font for mixed CJK and Western typography.** Put it at the front of a CSS font stack, set the correct language on the document, and let it select punctuation forms for Simplified Chinese, Traditional Chinese, Japanese, Korean, or explicit Western-language runs.

> This is a punctuation companion, not a standalone text typeface. It intentionally leaves letters, CJK ideographs, kana, Hangul, and ASCII digits to the fonts that follow it in the stack.

## Why use a bridge font?

Many punctuation characters share the same Unicode code points across languages even though their preferred shapes, widths, and placement differ. A normal fallback stack cannot choose a different font for the same code point based on language alone.

CJK Punct Bridge solves that problem with OpenType language systems and `locl` substitutions:

- CJK language tags select punctuation from the corresponding Google Fonts Noto Sans regional source.
- Explicit Western language tags select Hanken Grotesk forms for all 46 punctuation characters shared with Hanken.
- A missing or unspecified language intentionally falls back to Simplified Chinese punctuation.

## Quick start

Download the latest files from [GitHub Releases](https://github.com/Speechlessmanbilibili/CJK-Punct-Bridge/releases/latest). The release includes:

- `CJKPunctBridge-Variable.woff2` for the web, with a `wght` axis from 100 to 900;
- `CJKPunctBridge-Variable.ttf` for desktop use;
- nine static TTF weights from Thin 100 through Black 900.

An italic family ships alongside, as a separate `wght`-only variable font plus
nine static italics — the same layout as the pinned Hanken Grotesk release:
`CJKPunctBridge-Italic-Variable.woff2` / `.ttf`, and `CJKPunctBridge-Italic.ttf`,
`CJKPunctBridge-ThinItalic.ttf`, …, `CJKPunctBridge-BlackItalic.ttf`.

In italics, Western punctuation uses the true Hanken Grotesk Italic designs;
CJK punctuation uses a uniform synthetic 10-degree slant (no true CJK italic
design exists). Install or declare both families under the shared
**CJK Punct Bridge** name to get upright and italic styles.

Declare the web font and place it before the Latin and CJK families:

```css
@font-face {
  font-family: "CJK Punct Bridge";
  src: url("./CJKPunctBridge-Variable.woff2") format("woff2-variations");
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
}
@font-face {
  font-family: "CJK Punct Bridge";
  src: url("./CJKPunctBridge-Italic-Variable.woff2") format("woff2-variations");
  font-style: italic;
  font-weight: 100 900;
  font-display: swap;
}

body {
  font-family:
    "CJK Punct Bridge",
    "Hanken Grotesk",
    "Noto Sans SC",
    sans-serif;
  font-feature-settings: "locl" 1;
}
```

Then provide accurate language metadata:

```html
<p lang="zh-CN">简体中文，使用简体中文标点。</p>
<p lang="zh-TW">繁體中文，使用繁體中文標點。</p>
<p lang="ja">日本語の句読点。</p>
<p lang="ko">한국어 문장 부호.</p>
<p lang="en">English punctuation from Hanken Grotesk.</p>
```

Browsers and shaping engines can only activate the intended language system when the surrounding application supplies language information.

## Source-selection policy

| Text language or shaping path | Punctuation source |
| --- | --- |
| No language / default LangSys | Google Fonts Noto Sans SC |
| Simplified or phonetic Chinese (`ZHS`, `ZHP`) | Google Fonts Noto Sans SC |
| Traditional Chinese, Hong Kong, or Macao (`ZHT`, `ZHH`, `ZHTM`) | Google Fonts Noto Sans TC |
| Japanese (`JAN`) | Google Fonts Noto Sans JP |
| Korean or old Hangul (`KOR`, `KOH`) | Google Fonts Noto Sans KR |
| Configured explicit Western languages in Common, Latin, Cyrillic, or Greek runs | Google Fonts Hanken Grotesk where covered |

The configured Western paths cover the project locales, a broad modern and historic language set, and every explicit language system present in the pinned Hanken source. Script defaults are never changed to Western punctuation.

## Typography details

- The Western `locl` path covers all 46 bridge punctuation characters also present in Hanken Grotesk.
- `U+2014 —`, `U+2E3A ⸺`, and `U+2E3B ⸻` use Zhudou-derived dash outlines on the Simplified and Traditional Chinese paths.
- Repeated `U+2014` retains continuous two-em and three-em dash behavior on default and CJK paths; Western paths retain separate Hanken em dashes.
- Noto punctuation shaping is preserved, including `ccmp`, `dlig`, width features, `vert`, and `vrt2`.
- Regional vertical forms and vertical metrics are retained where the Noto source provides them.
- `U+002D` hyphen-minus is deliberately left to the normal Latin font.
- ASCII digits `U+0030`–`U+0039` are deliberately absent, so `0`–`9` always fall through to Hanken Grotesk in the recommended stack.

## Reproducible builds

Release binaries are generated from pinned, hash-verified sources and are not committed to normal source history.

```bash
python scripts/fetch_sources.py
python scripts/build.py
CJK_PUNCT_ITALIC=1 python scripts/build.py
python scripts/audit_release.py fonts/static/CJKPunctBridge-Regular.ttf fonts/variable/CJKPunctBridge-Variable.ttf
python scripts/check_dash_matrix.py fonts/static/CJKPunctBridge-Regular.ttf fonts/variable/CJKPunctBridge-Variable.ttf
```

After the networked fetch step, the build is fully offline. Noto Sans SC/TC/JP/KR and Hanken Grotesk come exclusively from pinned files in the Google Fonts repository. See [BUILDING.md](BUILDING.md), [SOURCES.md](SOURCES.md), and [FONTLOG.md](FONTLOG.md) for the merge policy, immutable source hashes, and release history.

## Optional interrobang variant

Releases also carry an optional companion family, **CJK Punct Bridge ?!**, that
ligates question/exclamation pairs into the interrobang: `?!` and `!?` become
`‽` (U+203D), while full-width `？！` and `！？` become a full-width interrobang,
aligned left like other full-width CJK punctuation. The ligatures are on by
default (`liga`) and cover every regional `locl` variant of `?` and `!`. Each
master uses Inter 4.001's U+203D outline instantiated at the matching `wght`,
so Thin through Black have genuinely different interrobang outlines.

This variant is an attachment, not the main product: the standard family
described above remains the default distribution and the primary subject of
this documentation. The variant ships as its own family
(`CJKPunctBridgeInterrobang-*`) with upright and italic variable fonts plus
nine static weights each, so it can be installed or removed independently.
The release attachment is named `CJKPunctBridgeInterrobang-v1.3.2.zip`.
Build it from the standard statics with:

```bash
python scripts/build_interrobang.py                     # upright statics + VF
CJK_PUNCT_ITALIC=1 python scripts/build_interrobang.py  # italic statics + VF
```

The interrobang glyph source is a hash-pinned Inter variable font passed via
`INTER_VF` or placed in `upstream/`. The build rejects repeated weight outlines,
variable/static endpoint drift, 60,000 or more glyphs, and a `gvar` table at or
above 64 MiB.

## License

CJK Punct Bridge is distributed under the [SIL Open Font License 1.1](OFL.txt). It is a modified and combined font, not an official release of Hanken Grotesk, Noto/Source Han, or Zhudou Sans. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution.
