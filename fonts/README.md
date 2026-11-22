# 预构建字体

预构建的字体二进制文件作为 GitHub Release 资产发布，有意不提交至源码仓库。

发行包内容：

- `static/`：9 个正体静态字重与 9 个静态斜体（`*Italic.ttf`）
- `variable/CJKPunctBridge-Variable.ttf`（正体，`wght` `100～900`）
- `variable/CJKPunctBridge-Italic-Variable.ttf`（斜体，`wght` `100～900`）
- `web/`：全部 18 个静态字重与 2 个可变字体的 `WOFF2` 版本

可选发行附件还包含独立的 `CJK Punct Bridge ?!` 家族以及极简的纯 Inter `Interrobang Bridge` 家族。它们生成的二进制文件位于已加入 `.gitignore` 的同级输出目录中。
