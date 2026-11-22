# 构建与审计脚本

- `fetch_sources.py`：可选的联网预取步骤。下载锁定的 Google Fonts Noto SC/TC/JP/KR、Hanken 正斜体可变 TTF 以及煮豆黑体 `v2.000`，校验 SHA-256 后将煮豆黑体解压至已加入 `.gitignore` 的 `upstream/` 缓存目录。
- `language_systems.py`：构建与审计共用的锁定 OpenType 语言系统注册表及字源策略常量。
- `font_metadata.py`：所有构建与发行审计共用的规范项目作者、版权、来源署名、链接、许可证字段与内部字体版本号。
- `build.py`：当 `upstream/` 就绪后可完全离线运行。默认构建全部正体 `TTF` 与 `WOFF2`，设置 `CJK_PUNCT_ITALIC=1` 时构建全部斜体，以简中作为无语言默认路径、对应 Noto 地区路径、显式西文 Hanken 标点与煮豆中文破折号。
- `build_interrobang.py`：构建可选的正斜体 `CJK Punct Bridge ?!` 家族，包含按字重匹配的 Inter `U+203D` 轮廓及可变端点 / 体积校验。
- `build_interrobang_bridge.py`：构建独立的纯 Inter 伴随字体，其 `cmap` 覆盖 `!`、`?`、`¡`、`¿`、`！`、`？` 与 `U+203D`，采用 `500 + 0` / `1000 + 0` 上下文双槽位排版，包含正斜体各 9 个静态字重与 2 个可变字体。
- `audit_release.py`：检查规范元数据、所有显式西文语言系统、完整 Hanken 标点交集、是否已排除 ASCII 数字、中日韩地区别名、核心中日韩 `GSUB` 特性、竖排表以及可变字重轴。
- `check_dash_matrix.py`：结构化校验默认 / 中日韩及所有显式西文路径下 1 / 2 / 3 个破折号的整形结果，验证方向兼容性与连字行为。

`build_variable_interrobang.py` 保留用于从已生成的静态主控字重单独重建可选可变字体，同样遵循修正后的元数据规则。

`SOURCES.md` 记录了 `v1.3.5` 使用的不可变字源修订与哈希。所有 Noto Sans 与 Hanken Grotesk 输入均来自锁定的 Google Fonts 仓库文件。
