# Build and audit scripts

`build.py` is the audited build script used for release 1.000. It writes compiled fonts under the repository `fonts/` directory and accepts optional environment variables for source/workspace locations:

- `CJK_PUNCT_BUILD_WORKSPACE`
- `CJK_PUNCT_UPSTREAM_DIR`
- `CJK_PUNCT_ZHUDOU_DIR`
- `CJK_PUNCT_ZHUDOU_LICENSE`
- `CJK_PUNCT_BUILD_DIR`

`SOURCES.md` records the exact upstream archive hashes used for the published binaries.

`audit_release.py` and `check_dash_matrix.py` perform structural regression checks for language-sensitive `ccmp` behavior, vertical metrics, dash orientation, and the variable weight axis.
