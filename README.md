# CJK Punct Bridge

A compact CJK punctuation bridge font intended to sit before a normal Latin/CJK font stack.

## Behavior

- **Unspecified/default language and Simplified Chinese (`ZHS`)**: Noto Sans SC punctuation.
- **Traditional Chinese (`ZHT`)**: Noto Sans TC punctuation through `locl`.
- **Japanese (`JAN`)**: Noto Sans JP punctuation through `locl`.
- **Korean (`KOR`)**: Noto Sans KR punctuation through `locl`.
- **English (`ENG`)**: common ambiguous punctuation (`· – — ‘ ’ “ ” …`) switches to Hanken Grotesk through `locl`.
- `U+2014 —`, `U+2E3A ⸺`, `U+2E3B ⸻` use Zhudou-derived CJK dash outlines in every CJK/default path.
- Repeated `U+2014` keeps Noto's `ccmp` machinery for continuous two-em/three-em CJK dashes. English deliberately does not enable that CJK `ccmp` path, so repeated English em dashes remain separate Hanken dashes.
- Regional `vert` / `vrt2` punctuation behavior is retained for SC/TC/JP/KR, and vertical dash forms remain Zhudou-derived.

The fallback for an absent or unrecognized OpenType language tag is deliberately **SC**, so an unspecified region stays Simplified-Chinese-oriented.

## Downloads

Prebuilt fonts are distributed through **GitHub Releases** rather than committed directly to the source repository. Release assets contain a variable TTF (`wght` 100–900), nine static TTF weights, and a variable WOFF2 for web use.

## CSS example

```css
font-family: "CJK Punct Bridge", "Hanken Grotesk", "Noto Sans SC", sans-serif;
```

Language-aware alternates require surrounding text/document language metadata such as HTML `lang`. Browsers do not reliably infer the intended language of punctuation from neighboring characters alone.

## Regression checks

The release is checked for horizontal/vertical dash direction, `ENG` vs CJK language behavior, regional language-system presence, and source-outline identity. See `scripts/audit_release.py`, `scripts/check_dash_matrix.py`, and `scripts/add_cjk_locales.py`.

## License

CJK Punct Bridge is distributed under the **SIL Open Font License 1.1**. It is a modified/combined font and is not an official release of Hanken Grotesk, Noto/Source Han, or Zhudou Sans. See `OFL.txt` and `THIRD_PARTY_NOTICES.md`.
