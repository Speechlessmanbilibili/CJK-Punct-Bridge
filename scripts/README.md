# Build and regression scripts

`build.py` is the audited build script for release 1.000. It expects the upstream font files under `upstream/` as described in `BUILDING.md` and writes compiled fonts to `dist/`.

`audit_release.py` performs structural checks for language-sensitive `ccmp` behavior, vertical metrics, dash orientation, and the variable `wght` axis.

`check_dash_matrix.py` exercises the `—`, `——`, and `———` substitution paths for default/CJK, English, horizontal, and vertical shaping without requiring HarfBuzz.
