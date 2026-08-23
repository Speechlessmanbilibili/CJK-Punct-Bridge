# CJK Punct Bridge

A compact CJK punctuation bridge font intended to sit before a normal Latin/CJK font stack.

## Behavior

- Default punctuation outlines: **Noto Sans SC**.
- `U+2014 —`, `U+2E3A ⸺`, `U+2E3B ⸻`: **Zhudou-derived** dash outlines.
- Repeated `U+2014` uses Noto's `ccmp` machinery with Zhudou-derived continuous two-em/three-em dash outlines in the default/CJK path.
- Vertical `vert` / `vrt2` behavior and vertical metrics are retained from Noto Sans SC; dash vertical forms are replaced by the corresponding Zhudou-derived forms.
- When an OpenType shaping engine supplies English language (`ENG`, e.g. HTML `lang="en"`), common ambiguous punctuation (`· – — ‘ ’ “ ” …`) switches to **Hanken Grotesk** through `locl`.
- The English path deliberately does **not** enable the CJK continuous-dash `ccmp`, so repeated English em dashes remain separate Hanken em dashes.
- Without a language tag, the default is CJK-oriented.

## Downloads

Prebuilt fonts are distributed through **GitHub Releases** rather than committed directly to the source repository. Release assets include:

- a variable TTF (`wght` 100–900);
- nine static TTF weights;
- a variable WOFF2 for web use.

## CSS example

```css
font-family: "CJK Punct Bridge", "Hanken Grotesk", "Noto Sans SC", sans-serif;
```

Language-aware alternates require the surrounding text/document to expose language metadata to the shaping engine. Browsers do not reliably infer language per phrase.

## Regression checks

The release is checked for horizontal/vertical dash direction, `ENG` vs `ZHS` language behavior, and source-outline identity for Noto/Hanken-derived punctuation. See `scripts/audit_release.py` and `scripts/check_dash_matrix.py`.

## License

CJK Punct Bridge is distributed under the **SIL Open Font License 1.1**. It is a modified/combined font and is not an official release of Hanken Grotesk, Noto/Source Han, or Zhudou Sans. See `OFL.txt` and `THIRD_PARTY_NOTICES.md`.

## Building

Source archive hashes are recorded in `SOURCES.md`; the merge strategy and reproducibility notes are documented in `BUILDING.md`.
