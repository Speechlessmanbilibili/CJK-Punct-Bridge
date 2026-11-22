# CJK Punct Bridge

**CJK Punct Bridge 是一款面向中英文混排场景的小型语言感知标点字体。** 将它放在 CSS 字体栈的最前方，并为文档设置正确的语言标记，它就会自动为简体中文、繁体中文、日文、韩文或指定的西文文本匹配对应的标点形态。

> 本项目是标点配套字体，而非独立的正文字体。它有意不收录字母、汉字、假名、谚文与 ASCII 数字，将这些字符留给字体栈中后续的字体渲染。

**`v1.3.5` 为当前版本。** 该版本统一采用 Inter 标点形态的问号与感叹号，并在可选的 CJK `?!` 家族与独立的 Interrobang Bridge 附件中保留直接映射 `U+203D`，同时为全部静态与可变字体提供 `WOFF2` 输出。

## 为什么需要标点桥接字体？

许多标点符号在不同语言中共享同一个 Unicode 码位，但各自偏好的字形、字宽与位置却各不相同。普通的字体回退栈无法仅凭语言为同一个码位选择不同的字形。

CJK Punct Bridge 通过 OpenType 语言系统与 `locl` 替换解决这一问题：

- 中日韩语言标签会从对应的 Google Fonts Noto Sans 地区分发版选取标点。
- 显式的西文语言标签会为所有与 Hanken Grotesk 共享的 46 个标点字符选用 Hanken Grotesk 字形。
- 缺失或未指定语言时，默认回退为简体中文标点。
- 在所有语言路径下，`!`、`?`、`¡`、`¿`、`！` 与 `？` 均采用字重匹配的 Inter 4.001 轮廓，全角形态保留 1000 单位字宽。

## 快速开始

从 [GitHub Releases](https://github.com/Speechlessmanbilibili/CJK-Punct-Bridge/releases/latest) 下载最新版本文件。发行包内含：

- 用于网页的 `CJKPunctBridge-Variable.woff2`，提供 `100～900` 的 `wght` 字重轴；
- 用于桌面端的 `CJKPunctBridge-Variable.ttf`；
- 从 Thin 100 到 Black 900 共 9 个字重的静态 `TTF` 与 `WOFF2` 文件。

配套的斜体家族以独立的单轴 `wght` 可变字体和 9 个静态斜体发布，布局与锁定的 Hanken Grotesk 发行版一致：`CJKPunctBridge-Italic-Variable.woff2` / `.ttf`，以及 `CJKPunctBridge-Italic.ttf`、`CJKPunctBridge-ThinItalic.ttf`、……、`CJKPunctBridge-BlackItalic.ttf`，每个静态字重均有对应的 `WOFF2`。

在斜体家族中，西文标点采用真正的 Hanken Grotesk Italic 设计；中日韩标点则采用统一的 10 度人工倾斜（因中日韩并无真正的斜体标点设计）。将正体与斜体两个家族同时安装或声明在同一个 **CJK Punct Bridge** 家族名下，即可获得完整的正斜体支持。

在网页中声明 Web 字体，并将其置于西文字体与中文字体之前：

```css
@font-face {
  font-family: "CJK Punct Bridge";
  src: url("./CJKPunctBridge-Variable.woff2") format("woff2-variations");
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
}
@font-face {
  font-family: "CJK Punct Bridge";
  src: url("./CJKPunctBridge-Italic-Variable.woff2") format("woff2-variations");
  font-style: italic;
  font-weight: 100 900;
  font-display: swap;
}

body {
  font-family:
    "CJK Punct Bridge",
    "Hanken Grotesk",
    "Noto Sans SC",
    sans-serif;
  font-feature-settings: "locl" 1;
}
```

随后为文本提供准确的语言属性：

```html
<p lang="zh-CN">简体中文，使用简体中文标点。</p>
<p lang="zh-TW">繁體中文，使用繁體中文標點。</p>
<p lang="ja">日本語の句読点。</p>
<p lang="ko">한국어 문장 부호.</p>
<p lang="en">English punctuation from Hanken Grotesk.</p>
```

只有在宿主应用或网页正确提供语言元数据时，浏览器和排版引擎才能激活对应的语言系统。

## 字源选择策略

| 文本语言或排版路径 | 标点来源 |
| --- | --- |
| 无语言标记 / 默认语言系统 | Google Fonts Noto Sans SC |
| 简体中文或汉语拼音（`ZHS`、`ZHP`） | Google Fonts Noto Sans SC |
| 繁体中文、中国香港或中国澳门（`ZHT`、`ZHH`、`ZHTM`） | Google Fonts Noto Sans TC |
| 日文（`JAN`） | Google Fonts Noto Sans JP |
| 韩文或古谚文（`KOR`、`KOH`） | Google Fonts Noto Sans KR |
| Common、Latin、Cyrillic、Greek 中配置的显式西文语言 | 覆盖范围内使用 Google Fonts Hanken Grotesk |

已配置的西文路径覆盖了项目常用地区、广泛的现代与历史西文语言集合，以及锁定 Hanken 源中存在的每一个显式语言系统。脚本默认语言系统绝不会被更改为西文标点。

## 排版细节

- 西文 `locl` 路径覆盖桥接字体与 Hanken Grotesk 共享的全部 46 个标点字符。
- `U+2014`（`—`）、`U+2E3A`（`⸺`）与 `U+2E3B`（`⸻`）在简体中文与繁体中文路径下使用源自煮豆黑体的破折号轮廓。
- 连续的 `U+2014` 在默认路径与中日韩路径下保留二连字与三连字不断开效果；西文路径保留分开的 Hanken 破折号。
- 保留 Noto 标点排版特性，包括 `ccmp`、`dlig`、字宽特性、`vert` 与 `vrt2`。
- 在 Noto 字源提供地区竖排字形与竖排度量时予以保留。
- 有意将 `U+002D` 连字符号留给常规西文字体处理。
- 有意排除 ASCII 数字 `U+0030～U+0039`，确保推荐字体栈中的 `0～9` 始终回落到 Hanken Grotesk。

## 可复现构建

发行版二进制文件由哈希校验锁定的上游字源生成，不提交至常规源码历史。

```bash
python scripts/fetch_sources.py
python scripts/build.py
CJK_PUNCT_ITALIC=1 python scripts/build.py
python scripts/audit_release.py fonts/static/CJKPunctBridge-Regular.ttf fonts/variable/CJKPunctBridge-Variable.ttf
python scripts/check_dash_matrix.py fonts/static/CJKPunctBridge-Regular.ttf fonts/variable/CJKPunctBridge-Variable.ttf
```

完成联网拉取字源步骤后，全部构建过程均可离线执行。Noto Sans SC / TC / JP / KR 与 Hanken Grotesk 均严格来自 Google Fonts 仓库中锁定的文件版本。合并策略、不可变字源哈希与发布历史请参阅 [BUILDING.md](BUILDING.md)、[SOURCES.md](SOURCES.md) 与 [FONTLOG.md](FONTLOG.md)。

## 可选的疑问叹号连字变体

发行版同时提供可选的配套家族 **CJK Punct Bridge ?!**，可将问号与感叹号组合连字为疑问叹号：`?!` 与 `!?` 会替换为 `‽`（`U+203D`），全角 `？！` 与 `！？` 会替换为与其他全角中文标点一样左对齐的全角疑问叹号。该连字通过 `liga` 默认启用，并覆盖所有地区 `locl` 变体下的 `?` 与 `!`。直接输入的 `U+203D`（`‽`）也会直接映射到同一个半角字形。每个主控字重均从对应 `wght` 实例化 Inter 4.001 的 `U+203D` 轮廓，因此从 Thin 到 Black 各自拥有真实的字重轮廓差异。标准版桥接字体在 `U+203D` 处保持不变，该直接映射仅属于可选的 `?!` 家族。

双字符排版保留两个源字符槽位并赋予明确字宽：`?!` / `!?` 会变为一个可见的半角 Inter 疑问叹号加一个零宽空字形（`500 + 0`），而 `？！` / `！？` 则使用全角形态加同一个空字形（`1000 + 0`）。因此无需依赖 GDEF 支持，光标停在中间时就会贴合可见字形的右边缘。直接输入 `U+203D` 则保持真正的单字符路径。

该变体属于可选附件而非主产品：前文所述的标准家族仍是默认分发版本与文档主体。该变体以独立家族名称（`CJKPunctBridgeInterrobang-*`）分发，同样包含正斜体可变字体及各 9 个静态字重，可独立安装或卸载。全部静态与可变字型均附带 `WOFF2` 文件。发行附件包名为 `CJKPunctBridgeInterrobang-v1.3.5.zip`。可在标准静态字体生成后执行以下命令构建：

```bash
python scripts/build_interrobang.py                     # 正体静态与可变字体
CJK_PUNCT_ITALIC=1 python scripts/build_interrobang.py  # 斜体静态与可变字体
```

疑问叹号字形源是通过 `INTER_VF` 指定或放入 `upstream/` 目录的哈希锁定版 Inter 可变字体。构建校验会拒绝重复字重轮廓、可变 / 静态端点漂移、字形数量达到 60,000 个或以上，以及 `gvar` 表达到或超过 64 MiB 的产物。

## Interrobang Bridge 附件

发行版还附带 **Interrobang Bridge**，一个仅基于 Inter 构建的极简伴随字体。其 `cmap` 仅覆盖 `!`、`?`、`¡`、`¿`、`！`、`？` 与 `U+203D`（`‽`）。默认 `liga` 将 ASCII 组合排版为 `500 + 0`，将全角组合排版为 `1000 + 0`；其余所有字符均直接透传给字体栈中的下一款字体。当只需要这一套标点与疑问叹号行为时，可将其置于常规字体之前。

该附件提供 9 个正体静态字重、9 个斜体静态字重，以及正斜体两个独立的 `wght` 可变字体。每个主控字重均从对应的 Inter 4.001 字重实例化，并支持直接输入 `U+203D`。全部 20 个 `TTF` 文件均提供对应的 `WOFF2` 版本。发行附件包名为 `InterrobangBridge-v1.3.5.zip`。

```bash
python scripts/build_interrobang_bridge.py
INTERROBANG_BRIDGE_ITALIC=1 python scripts/build_interrobang_bridge.py
```

## 许可证

CJK Punct Bridge 基于 [SIL Open Font License 1.1](OFL.txt) 分发。本项目属于修改并组合的衍生字体，并非 Hanken Grotesk、Noto / Source Han 或煮豆黑体的官方发行版。版权归属详情请参阅 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
