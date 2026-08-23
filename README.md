# CJK Punct Bridge

A compact language-aware CJK punctuation bridge font intended to sit before a normal Latin/CJK font stack.

## Behavior

- **No language/region tag defaults to Simplified Chinese (SC)** punctuation behavior.
- Simplified Chinese (`ZHS`) uses Google Fonts **Noto Sans SC** punctuation; Traditional Chinese (`ZHT`), Japanese (`JAN`), and Korean (`KOR`) switch to punctuation outlines taken from the corresponding Google Fonts Noto Sans regional distributions through `locl`.
- `U+2014 —`, `U+2E3A ⸺`, and `U+2E3B ⸻` use **Zhudou-derived** dash outlines on the SC and TC Chinese paths.
- Noto punctuation shaping is retained, including `ccmp`, `dlig`, width features, `vert`, and `vrt2`. Repeated `U+2014` therefore keeps the continuous two-em/three-em behavior on CJK paths.
- English (`ENG`) switches ambiguous shared punctuation (`· – — ‘ ’ “ ” …`) to **Hanken Grotesk** through `locl`; its language system intentionally omits the CJK continuous-dash `ccmp` feature.
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

Set the correct HTML `lang` value so shaping engines can select `ZHS` / `ZHT` / `JAN` / `KOR` / `ENG`. With no language metadata the bridge intentionally falls back to SC.

## Building

Upstream binaries are **not committed**. `scripts/fetch_sources.py` can prefetch the exact pinned inputs into the gitignored `upstream/` directory; after that `scripts/build.py` is fully offline. See `BUILDING.md` and `SOURCES.md`.

## License

CJK Punct Bridge is distributed under the **SIL Open Font License 1.1**. It is a modified/combined font and is not an official release of Hanken Grotesk, Noto/Source Han, or Zhudou Sans. See `OFL.txt` and `THIRD_PARTY_NOTICES.md`.
