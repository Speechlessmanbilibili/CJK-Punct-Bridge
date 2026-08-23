# Building CJK Punct Bridge

CJK Punct Bridge is built from three OFL-licensed upstream font families. Exact source archive hashes are recorded in `SOURCES.md`.

## Inputs

- Noto Sans SC: base punctuation glyphs, CJK metrics, `ccmp`, `vert`, `vrt2`, and vertical metrics.
- Zhudou Sans: CJK em-dash outlines, including horizontal and vertical one-em/two-em/three-em dash forms.
- Hanken Grotesk: English-localized shared punctuation alternates.

Place the required source fonts under the repository-local `upstream/` directory before running `scripts/build.py`:

```text
upstream/
├─ noto/
│  ├─ NotoSansSC-Thin.ttf
│  ├─ NotoSansSC-Light.ttf
│  ├─ NotoSansSC-Regular.ttf
│  ├─ NotoSansSC-Bold.ttf
│  └─ NotoSansSC-Black.ttf
├─ hanken/
│  ├─ HankenGrotesk-Thin.ttf
│  ├─ HankenGrotesk-Light.ttf
│  ├─ HankenGrotesk-Regular.ttf
│  ├─ HankenGrotesk-Bold.ttf
│  └─ HankenGrotesk-Black.ttf
└─ zhudou/
   ├─ ZhudouSans-ExtraLight.ttf
   ├─ ZhudouSans-Light.ttf
   ├─ ZhudouSans-Regular.ttf
   ├─ ZhudouSans-Bold.ttf
   └─ ZhudouSans-Heavy.ttf
```

Then run:

```bash
python scripts/build.py
python scripts/audit_release.py dist/static/CJKPunctBridge-Regular.ttf dist/variable/CJKPunctBridge-Variable.ttf
python scripts/check_dash_matrix.py
```

Compiled outputs are written to `dist/`.

## Build strategy

1. Start from Noto Sans SC punctuation coverage.
2. Keep Noto's CJK layout machinery and vertical metrics.
3. Resolve the Simplified-Chinese horizontal `locl` targets and their true `vert` targets from GSUB instead of relying on glyph names.
4. Replace `U+2014`, `U+2E3A`, `U+2E3B`, their Simplified-Chinese localized horizontal forms, and their corresponding vertical targets with Zhudou-derived outlines.
5. Add Hanken-derived alternates for shared punctuation such as `· – — ‘ ’ “ ” …`.
6. Attach those alternates to an `ENG` OpenType `locl` path while removing the CJK continuous-dash `ccmp` feature from the English path.
7. Produce a variable TTF, nine static TTF weights, and a variable WOFF2.

## OpenType behavior

- Repeated `U+2014` uses the retained Noto `ccmp` machinery to form continuous two-em/three-em dashes in default/CJK language systems.
- English `ENG` runs use Hanken shared punctuation alternates and do not apply the CJK repeated-em-dash ligature.
- `vert` and `vrt2` retain vertical punctuation behavior, with Zhudou-derived vertical dash forms substituted where appropriate.
- The build also extends the default vertical path so vertical dash substitution works even when an engine supplies vertical direction without an explicit `ZHS` language tag.

## Distribution

Prebuilt TTF and WOFF2 files are published as GitHub Release assets and are intentionally omitted from normal Git history.
