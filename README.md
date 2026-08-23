# CJK Punct Bridge

A compact CJK punctuation bridge font. It is intended to sit before a normal Latin/CJK font stack.

## Behavior

- Default punctuation outlines: **Noto Sans SC**.
- `U+2014 —`, `U+2E3A ⸺`, `U+2E3B ⸻`: **Zhudou-derived** dash outlines.
- Repeated `U+2014` uses Noto's original `ccmp` machinery with the Zhudou-derived continuous two-em/three-em dash outlines.
- Vertical `vert` / `vrt2` behavior and vertical metrics are retained from Noto Sans SC; dash vertical forms are replaced by the corresponding Zhudou-derived forms.
- When an OpenType shaping engine supplies English language (`ENG`, e.g. HTML `lang="en"`), common ambiguous punctuation (`· – — ‘ ’ “ ” …`) switches to **Hanken Grotesk** through `locl`.
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

## License

CJK Punct Bridge is distributed under the **SIL Open Font License 1.1**. It is a modified/combined font and is not an official release of Hanken Grotesk, Noto/Source Han, or Zhudou Sans. See `OFL.txt` and `THIRD_PARTY_NOTICES.md`.
