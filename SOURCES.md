# Source inputs

Pinned upstream binaries used by v1.2.0. Build-time source files live in the gitignored `upstream/` directory. Noto Sans and Hanken Grotesk are sourced exclusively from the Google Fonts repository distributions shown below.

| Input | Pinned source | SHA-256 |
| --- | --- | --- |
| Google Fonts Noto Sans SC variable TTF | `google/fonts@2894aab31764f10f29c421bdfd2340d3b382d384 / ofl/notosanssc/NotoSansSC[wght].ttf` | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| Google Fonts Noto Sans TC variable TTF | `google/fonts@b950a7257470b900078f2bf3223823a8602de7e1 / ofl/notosanstc/NotoSansTC[wght].ttf` | `864727d210d54f2537bbe23b3a839436c3992af72de9322af5270897246bd44f` |
| Google Fonts Noto Sans JP variable TTF | `google/fonts@295d98a7a0c17c68f1341eaeea354e7960ea70d3 / ofl/notosansjp/NotoSansJP[wght].ttf` | `c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f` |
| Google Fonts Noto Sans KR variable TTF | `google/fonts@4efc2774c63917927efe769ca845def6bd6debae / ofl/notosanskr/NotoSansKR[wght].ttf` | `194018e6b2b293a7964f037b25c0249ce1418bc9ab3c971060a03aa57861e252` |
| Google Fonts Hanken Grotesk variable TTF | `google/fonts@714891563e901b1a0d8ebcaaa003b01604793888 / ofl/hankengrotesk/HankenGrotesk[wght].ttf` | `813b3f8fa0965405669a89b38e51bbefd95eef6b8e20d1cb2d8c10cce062662f` |
| Zhudou Sans v2.000 release archive | `Buernia/Zhudou-Sans v2.000 / Zhudou.Sans.zip` | `1a2718aa52c98d1ac7e18d60e0f1d61057b18e558e8196a3a770104855a6fc69` |

`scripts/fetch_sources.py` contains the corresponding immutable download URLs and verifies every hash before extraction/building.

The OpenType language-system policy in `scripts/language_systems.py` uses registered tags from Microsoft's OpenType 1.9 registry, last updated 2024-05-31. It is build metadata only, not a font-outline source.
