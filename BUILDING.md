# Building CJK Punct Bridge

CJK Punct Bridge is built from three OFL-licensed upstream font families. Exact source archive hashes are recorded in `SOURCES.md`.

## Inputs

- Noto Sans SC: base punctuation glyphs, CJK metrics, `ccmp`, `vert`, `vrt2`, and vertical metrics.
- Zhudou Sans: CJK em-dash outlines, including horizontal and vertical one-em/two-em/three-em dash forms.
- Hanken Grotesk: English-localized shared punctuation alternates.

## Build strategy

1. Start from Noto Sans SC punctuation coverage.
2. Keep Noto's CJK layout machinery and vertical metrics.
3. Replace `U+2014`, `U+2E3A`, `U+2E3B`, and the corresponding vertical dash targets with Zhudou-derived outlines.
4. Add Hanken-derived alternates for shared punctuation such as `· – — ‘ ’ “ ” …`.
5. Attach those alternates to an `ENG` OpenType `locl` path while keeping the default path CJK-oriented.
6. Produce a variable TTF, nine static TTF weights, and a variable WOFF2.

## OpenType behavior

- Repeated `U+2014` uses the retained Noto `ccmp` machinery to form continuous two-em/three-em dashes.
- `vert` and `vrt2` retain vertical punctuation behavior, with Zhudou-derived vertical dash forms substituted where appropriate.
- `locl` only changes shared punctuation when the shaping engine actually supplies English language metadata.

## Distribution

Prebuilt TTF and WOFF2 files are published as GitHub Release assets and are intentionally omitted from normal Git history.
