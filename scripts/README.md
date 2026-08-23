# Build and audit scripts

- `fetch_sources.py`: optional networked prefetch step. Downloads the pinned Google Fonts Noto SC/TC/JP/KR and Hanken variable TTFs plus Zhudou v2.000, verifies SHA-256, and extracts Zhudou into the gitignored `upstream/` cache.
- `build.py`: fully offline once `upstream/` is populated. Builds one language-aware punctuation font with SC as the no-language default, `ZHT`/`JAN`/`KOR` regional punctuation, Hanken `ENG locl`, and Zhudou Chinese dashes.
- `audit_release.py`: checks language systems, essential punctuation GSUB features, vertical tables, and the variable weight axis.
- `check_dash_matrix.py`: structurally shapes one/two/three em dashes for default, ZHS, ZHT, JAN, KOR, and ENG and checks source-compatible orientation/ligature behavior.

`SOURCES.md` records the immutable source revisions and hashes used by v1.1.0.
