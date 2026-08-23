# Building CJK Punct Bridge

The build uses the actual Google Fonts distributions of Noto Sans SC/TC/JP/KR and Hanken Grotesk, plus Zhudou Sans v2.000. Exact immutable source URLs and SHA-256 hashes are in `SOURCES.md`.

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

Outputs are written under `fonts/static/`, `fonts/variable/`, and `fonts/web/`; release binaries remain outside normal Git history.

## Merge strategy

1. Determine punctuation code points shared by the four Google Fonts Noto CJK distributions; `U+002D` hyphen-minus remains with the normal Latin font.
2. Use Noto Sans SC as the default OpenType/layout skeleton and make the no-language default follow its `ZHS` behavior.
3. Preserve Noto SC punctuation GSUB behavior including `ccmp`, `dlig`, width alternates, `vert`, and `vrt2`.
4. Copy the final localized punctuation outlines from Noto Sans TC/JP/KR and attach them to `ZHT`, `JAN`, and `KOR` `locl` language systems. Regional vertical targets are copied and attached through `vert` / `vrt2`.
5. Replace Chinese SC/TC one-em/two-em/three-em dash outlines with Zhudou-derived horizontal and vertical forms while retaining the Noto continuous-dash machinery.
6. Add Hanken shared-punctuation alternates to `ENG locl`; omit `ccmp` from that English language system so English repeated em dashes remain separate.
7. Build five static masters, interpolate a `wght` 100–900 variable TTF, instantiate nine static weights, and emit WOFF2.

The regional Google Fonts Noto punctuation subsets retain the same relevant punctuation GSUB feature set after subsetting; Korean-only extra shaping lookups outside punctuation are removed by the punctuation closure and are not needed by this bridge.
