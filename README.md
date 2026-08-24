# CJK Punct Bridge

A compact language-aware CJK punctuation bridge font intended to sit before a normal Latin/CJK font stack.

The bridge deliberately contains no ASCII digits. `0`–`9` therefore always come from the following Hanken Grotesk face, regardless of the active default, Western, or CJK language system; language selection changes punctuation only.

## Behavior

- **No language/region tag defaults to Simplified Chinese (SC)** punctuation behavior.
- Simplified Chinese (`ZHS`, including phonetic `ZHP`) uses Google Fonts **Noto Sans SC** punctuation; Traditional Chinese (`ZHT`, Hong Kong `ZHH`, Macao `ZHTM`), Japanese (`JAN`), and Korean (`KOR`, including old Hangul `KOH`) switch to punctuation outlines taken from the corresponding Google Fonts Noto Sans regional distributions through `locl`.
- `U+2014 —`, `U+2E3A ⸺`, and `U+2E3B ⸻` use **Zhudou-derived** dash outlines on the SC and TC Chinese paths.
- Noto punctuation shaping is retained, including `ccmp`, `dlig`, width features, `vert`, and `vrt2`. Repeated `U+2014` therefore keeps the continuous two-em/three-em behavior on CJK paths.
- Supported explicit Western languages in Common (`DFLT`), Latin, Cyrillic, and Greek script runs switch every bridge punctuation character also covered by Google Fonts **Hanken Grotesk** to the Hanken glyph through `locl`. Western paths expose no Noto punctuation substitutions, so all 46 shared punctuation characters remain Hanken-derived. Every default LangSys still uses Noto SC.
- Vertical metrics are retained. Regional vertical punctuation forms are selected after regional `locl` where the Noto source provides them.

## Downloads

Prebuilt fonts are distributed through **GitHub Releases** rather than committed directly to source history:

- variable TTF (`wght` 100–900);
- nine static TTF weights;
- variable WOFF2 for web use.

## CSS

```css
font-family: "CJK Punct Bridge", "Hanken Grotesk", "Noto Sans SC", sans-serif;
```

Set the correct HTML `lang` value so shaping engines can select the appropriate OpenType language system. With no language metadata the bridge intentionally falls back to SC; explicit CJK regions use their Noto regional source, while explicit Latin/Cyrillic/Greek languages use Hanken punctuation where Hanken has coverage.

## Building

Upstream binaries are **not committed**. `scripts/fetch_sources.py` can prefetch the exact pinned inputs into the gitignored `upstream/` directory; after that `scripts/build.py` is fully offline. All Noto Sans and Hanken Grotesk inputs come from pinned commits in the **Google Fonts** repository. See `BUILDING.md` and `SOURCES.md`.

## License

CJK Punct Bridge is distributed under the **SIL Open Font License 1.1**. It is a modified/combined font and is not an official release of Hanken Grotesk, Noto/Source Han, or Zhudou Sans. See `OFL.txt` and `THIRD_PARTY_NOTICES.md`.
