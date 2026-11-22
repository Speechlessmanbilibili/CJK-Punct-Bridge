# 构建 CJK Punct Bridge

构建过程仅使用来自 **Google Fonts 官方仓库** 分发的 Noto Sans SC / TC / JP / KR、Hanken Grotesk，以及煮豆黑体 `v2.000`，不会以作者个人仓库、系统字体或镜像构建替代 Noto 或 Hanken。精确的不可变下载链接与 SHA-256 哈希见 [SOURCES.md](SOURCES.md)。

## 1. 预取上游字源（联网步骤）

```bash
python scripts/fetch_sources.py
```

该步骤会生成已加入 `.gitignore` 的 `upstream/` 缓存目录。上游字源二进制文件有意不提交至源码仓库。

## 2. 离线构建

当 `upstream/` 准备就绪后，后续构建全程无需联网：

```bash
python scripts/build.py
python scripts/audit_release.py fonts/static/CJKPunctBridge-Regular.ttf fonts/variable/CJKPunctBridge-Variable.ttf
python scripts/check_dash_matrix.py fonts/static/CJKPunctBridge-Regular.ttf fonts/variable/CJKPunctBridge-Variable.ttf
```

构建产物输出至 `fonts/static/`、`fonts/variable/` 与 `fonts/web/`；`fonts/web/` 包含全部静态与可变字型的 `WOFF2` 版本。发行二进制文件不纳入常规 Git 提交历史。

## 3. 斜体家族

斜体家族由一个独立的单轴可变字体与 9 个静态斜体组成，沿用锁定的 Hanken Grotesk 发行结构（正体与斜体各自为独立的仅含 `wght` 轴的可变文件，共享同一个排版家族名）。使用以下命令构建：

```bash
CJK_PUNCT_ITALIC=1 python scripts/build.py
```

该命令会生成 `fonts/variable/CJKPunctBridge-Italic-Variable.ttf`、`fonts/web/CJKPunctBridge-Italic-Variable.woff2`，以及 9 个 `fonts/static/CJKPunctBridge-*Italic.ttf` 静态斜体文件。

在斜体家族中，西文标点来自锁定的 Google Fonts **Hanken Grotesk Italic** 分发版（真斜体设计）；中日韩地区标点与煮豆破折号则使用统一的 10 度人工倾斜（`scripts/build.py` 中的 `shear_font()`）：简单字形保持完全一致的轮廓点结构与标志位以确保 `varLib` 主控字重可插值，复合字形在所有主控字重中以相同方式打散，步进宽度保持不变，并依据新边界重新计算左侧轴距。

斜体输出采用兼容 Office 的样式关联：`OS/2.fsSelection` 设置 `ITALIC` 且清除 `REGULAR`；Bold Italic 仅设置 `ITALIC + BOLD`。传统 `nameID 2` 保留样式关联名，而排版子族 `nameID 17` 保留完整的字重与姿态名称。

## 4. 疑问叹号连字变体

在正斜体两款基础可变字体生成后，将 `SOURCES.md` 中锁定的 Inter 4.001 文件放入 `upstream/` 或显式设置 `INTER_VF`：

```bash
INTER_VF=upstream/InterVariable.ttf python scripts/build_interrobang.py
CJK_PUNCT_ITALIC=1 INTER_VF=upstream/InterVariable-Italic.ttf python scripts/build_interrobang.py
```

每次执行都会在 `fonts-interrobang/` 下生成 9 个静态字体与 1 个可变字体，并在其 `web/` 子目录下生成对应的 `WOFF2` 文件。Inter 的 `U+203D` 会按每个主控字重的权重分别实例化。校验会强制要求 9 个轮廓互异、可变与静态端点匹配、字形总数少于 60,000 个，且 `gvar` 表小于 64 MiB。

该可选家族还会将直接输入的 `U+203D` 映射到 `?!` / `!?` 连字所使用的同一款按字重匹配的半角字形。标准版桥接字体不会获得此映射。

双字符组合排版采用两次上下文替换而非标准连字：第一个源字符变为可见的疑问叹号，第二个源字符变为零宽空字形。因此 ASCII 组合排版为 `500 + 0`，全角组合排版为 `1000 + 0`，使中间光标恰好落在可见字形的右边界上。

## 5. 极简西文 Interrobang Bridge

在将锁定的 Inter 文件放入 `upstream/` 后，可构建独立的纯 Inter 伴随字体：

```bash
python scripts/build_interrobang_bridge.py
INTERROBANG_BRIDGE_ITALIC=1 python scripts/build_interrobang_bridge.py
```

它会在 `fonts-interrobang-bridge/` 下输出每种姿态各 9 个静态字重与 1 个可变字体，以及对应的 `WOFF2` 文件。其 `cmap` 包含 `!`、`?`、`¡`、`¿`、`！`、`？` 与 `U+203D`；双字符排版使用 `500 + 0` 或 `1000 + 0`，且全部 9 个 Inter 字重轮廓必须互不相同。

## 合并策略

1. 计算 4 个 Google Fonts Noto CJK 分发版共有的标点码位；`U+002D` 连字符号继续交由常规西文字体提供。
   硬性排除 ASCII 数字 `U+0030～U+0039`：桥接字体绝不能拦截数字，下游字体栈中的数字在任何语言下均由 Hanken Grotesk 提供。
2. 以 Noto Sans SC 作为默认的 OpenType / 布局骨架，使未指定语言时的默认行为遵循其 `ZHS` 规则。
3. 保留 Noto SC 标点 `GSUB` 行为，包括 `ccmp`、`dlig`、字宽替换、`vert` 与 `vrt2`。
4. 从 Noto Sans TC / JP / KR 复制最终的本地化标点轮廓，并挂载到对应的中文、日文、韩文 `locl` 语言系统，包括已注册的香港、澳门、注音 / 拼音中文以及古谚文别名。地区竖排目标字形也一并复制并通过 `vert` / `vrt2` 挂载。
5. 将简繁中文的一字、二字、三字破折号轮廓替换为源自煮豆黑体的横排与竖排形态，同时保留 Noto 的连续破折号机制。
6. 计算桥接字体与锁定 Google Fonts Hanken Grotesk 的完整标点交集（当前共 46 个码位）。为 `DFLT`、`latn`、`cyrl`、`grek` 下配置的所有显式西文语言通过 `locl` 挂载 Hanken 替换字形，且不暴露任何 Noto 标点替换。各脚本默认语言系统仍保持 Noto SC，显式 CJK 标签仍走各自对应的 Noto 地区路径。
7. 构建 5 个静态主控字重，插值生成 `wght` `100～900` 可变 TTF，再实例化 9 个静态字重并输出 `WOFF2`。斜体家族遵循相同管线，西文源换用 Hanken Grotesk Italic，中日韩字源则施加人工倾斜。

各个地区的 Google Fonts Noto 标点子集在子集化后保留了相同的核心标点 `GSUB` 特性集合；韩文版中标点之外的额外排版查找表会在标点闭包过程中移除，本桥接字体无需这些查找表。

`scripts/language_systems.py` 收录了项目在 Common / Latin / Cyrillic / Greek 策略中使用的 OpenType 1.9 已注册标签，涵盖所有项目地区、广泛的现代与历史西文语言集合，以及锁定 Hanken 字源中的所有显式语言系统，并且有意不修改任何脚本的默认 `LangSys`。
