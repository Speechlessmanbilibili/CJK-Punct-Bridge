# 上游字源输入

构建时字源位于已加入 `.gitignore` 的 `upstream/` 目录。Noto Sans 与 Hanken Grotesk 均严格来自下方列出的 Google Fonts 官方仓库分发版本。

| 输入源 | 锁定来源 | SHA-256 |
| --- | --- | --- |
| Google Fonts Noto Sans SC 可变 TTF | `google/fonts@2894aab31764f10f29c421bdfd2340d3b382d384 / ofl/notosanssc/NotoSansSC[wght].ttf` | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| Google Fonts Noto Sans TC 可变 TTF | `google/fonts@b950a7257470b900078f2bf3223823a8602de7e1 / ofl/notosanstc/NotoSansTC[wght].ttf` | `864727d210d54f2537bbe23b3a839436c3992af72de9322af5270897246bd44f` |
| Google Fonts Noto Sans JP 可变 TTF | `google/fonts@295d98a7a0c17c68f1341eaeea354e7960ea70d3 / ofl/notosansjp/NotoSansJP[wght].ttf` | `c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f` |
| Google Fonts Noto Sans KR 可变 TTF | `google/fonts@4efc2774c63917927efe69ca845def6bd6debae / ofl/notosanskr/NotoSansKR[wght].ttf` | `194018e6b2b293a7964f037b25c0249ce1418bc9ab3c971060a03aa57861e252` |
| Google Fonts Hanken Grotesk 可变 TTF | `google/fonts@714891563e901b1a0d8ebcaaa003b01604793888 / ofl/hankengrotesk/HankenGrotesk[wght].ttf` | `813b3f8fa0965405669a89b38e51bbefd95eef6b8e20d1cb2d8c10cce062662f` |
| Google Fonts Hanken Grotesk Italic 可变 TTF | `google/fonts@714891563e901b1a0d8ebcaaa003b01604793888 / ofl/hankengrotesk/HankenGrotesk-Italic[wght].ttf` | `ae5731726ff75301a3cb63f2e98d1babc77d55ab09fb8e229ca75f5bd46fbe32` |
| 煮豆黑体 `v2.000` 发行归档 | `Buernia/Zhudou-Sans v2.000 / Zhudou.Sans.zip` | `1a2718aa52c98d1ac7e18d60e0f1d61057b18e558e8196a3a770104855a6fc69` |
| Inter 4.001 正体可变 TTF（仅限 `CJK Punct Bridge ?!` 与 `Interrobang Bridge`） | 本地 OFL 输入 `InterVariable.ttf`，内部源码修订 `git-9221beed3`；可通过 `INTER_VF` 指定或放入 `upstream/` | `4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf` |
| Inter 4.001 斜体可变 TTF（仅限 `CJK Punct Bridge ?!` 与 `Interrobang Bridge`） | 本地 OFL 输入 `InterVariable-Italic.ttf`，内部源码修订 `git-9221beed3`；可通过 `INTER_VF` 指定或放入 `upstream/` | `d6f1f6a172d9e588438db9f986fd5cfad7b30f644374080a8a9d4d91e344586f` |

`scripts/fetch_sources.py` 中包含对应的不可变下载链接，并会在解压与构建前校验每一个文件的哈希值。

Inter 仅用于构建包含疑问叹号的相关版本。构建前会由 `scripts/build_interrobang.py` 与 `scripts/build_interrobang_bridge.py` 校验其精确哈希、`opsz` / `wght` 轴与 `U+203D` 覆盖情况。

`scripts/language_systems.py` 中的 OpenType 语言系统策略使用来自微软 OpenType 1.9 注册表（最后更新于 2024-05-31）的已注册标签。它仅作为构建元数据使用，并非字体轮廓来源。
