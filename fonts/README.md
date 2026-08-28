# Prebuilt fonts

Prebuilt font binaries are published as GitHub Release assets. They are intentionally not committed to the source repository.

Release package contents:

- `static/`: nine static upright weights plus nine static italics (`*Italic.ttf`)
- `variable/CJKPunctBridge-Variable.ttf` (upright, `wght` 100–900)
- `variable/CJKPunctBridge-Italic-Variable.ttf` (italic, `wght` 100–900)
- `web/`: WOFF2 versions of all eighteen static faces plus both variable fonts

Optional release attachments also contain the separate `CJK Punct Bridge ?!`
family and the minimal Inter-only `Interrobang Bridge` family. Their generated
binaries live in gitignored sibling output directories.
