# Build and audit scripts

- `fetch_sources.py`: optional networked prefetch step. Downloads the pinned Google Fonts Noto SC/TC/JP/KR and Hanken upright/italic variable TTFs plus Zhudou v2.000, verifies SHA-256, and extracts Zhudou into the gitignored `upstream/` cache.
- `language_systems.py`: pinned OpenType language-system registry and the source-policy constants shared by the build and audits.
- `font_metadata.py`: canonical project authorship, copyright, source attribution, URLs, license fields, and internal font revision shared by every build and release audit.
- `build.py`: fully offline once `upstream/` is populated. Builds the upright family by default and the italic family with `CJK_PUNCT_ITALIC=1`, with SC as the no-language default, corresponding Noto regional CJK paths, explicit Western-language Hanken punctuation, and Zhudou Chinese dashes.
- `build_interrobang.py`: builds the optional upright/italic `CJK Punct Bridge ?!` families with weight-matched Inter `U+203D` outlines and variable endpoint/size validation.
- `audit_release.py`: checks canonical metadata, all explicit Western language systems, the complete Hanken punctuation intersection, the absence of ASCII digits, CJK regional aliases, essential CJK GSUB features, vertical tables, and the variable weight axis.
- `check_dash_matrix.py`: structurally shapes one/two/three em dashes for default/CJK and every explicit Western path, checking source-compatible orientation and ligature behavior.

`build_variable_interrobang.py` remains available for rebuilding only the optional variable font from already generated static masters; it uses the same corrected metadata rules.

`SOURCES.md` records the immutable source revisions and hashes used by v1.3.2. All Noto Sans and Hanken Grotesk inputs are pinned Google Fonts repository files.
