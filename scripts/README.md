# Build and audit scripts

- `fetch_sources.py`: optional networked prefetch step. Downloads the pinned Google Fonts Noto SC/TC/JP/KR and Hanken variable TTFs plus Zhudou v2.000, verifies SHA-256, and extracts Zhudou into the gitignored `upstream/` cache.
- `language_systems.py`: pinned OpenType language-system registry and the source-policy constants shared by the build and audits.
- `build.py`: fully offline once `upstream/` is populated. Builds one language-aware punctuation font with SC as the no-language default, corresponding Noto regional CJK paths, explicit Western-language Hanken punctuation, and Zhudou Chinese dashes.
- `audit_release.py`: checks all explicit Western language systems, the complete Hanken punctuation intersection, the absence of ASCII digits, CJK regional aliases, essential CJK GSUB features, vertical tables, and the variable weight axis.
- `check_dash_matrix.py`: structurally shapes one/two/three em dashes for default/CJK and every explicit Western path, checking source-compatible orientation and ligature behavior.

`SOURCES.md` records the immutable source revisions and hashes used by v1.2.0. All Noto Sans and Hanken Grotesk inputs are pinned Google Fonts repository files.
