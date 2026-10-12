# Xtu Law Thesis Format

根据湘潭大学法学学部本科毕业论文模板及注释规范整理的 Codex skill。用于论文排版、格式检查、脚注、参考文献及过程材料整理。

这是个人整理版本。依据保留在 `assets/` 中的两份文件，并非学校官方发布或最新格式的认证。

## 本版本的调整

- 全文页眉留空，页脚页码保留。这与原模板的校名页眉要求不同。
- 中文标题和正文主题字体均为宋体，分别对应 WPS 的“宋体（标题）”“宋体（正文）”角色。
- 两个主题角色的英文和数字均为 Times New Roman。
- 原模板中的其他排版及引用要求保存在 `references/`，未明确的要求不补造成学校规定。

## 安装

下载本仓库 ZIP 并解压，将含有 `SKILL.md` 的目录命名为 `xtu-law-thesis-format`，放入你的 Codex 个人技能目录：

```text
~/.codex/skills/xtu-law-thesis-format/
```

如果你自定义了 `CODEX_HOME`，使用该目录下的 `skills/xtu-law-thesis-format/`。安装后在新聊天中调用。

## 使用

```text
使用 $xtu-law-thesis-format，帮我检查这份论文的格式。
```

```text
使用 $xtu-law-thesis-format，按本技能的规范排版这份 Word，输出副本。
```

仅检查时不修改原件。排版不等于核验引文真实性，也不自动改写论文观点。个人信息、引用页码、教师评语等只依据实际材料填写。

## 文件结构

```text
SKILL.md                     技能入口
agents/openai.yaml           显示名称及默认调用提示
references/                  排版、引用、过程材料、WPS兼容性及来源
assets/thesis-template.doc   学校论文及过程材料模板原件
assets/citation-standard.doc 学校注释和参考文献规范原件
scripts/                     字体角色处理与只读检查工具
```

## 辅助脚本

检查器需要 Python 3；字体角色处理器还需要 `lxml`。完整 Word 排版及页面验证由使用环境中的文档工具完成。

```bash
python scripts/check_docx_compatibility.py input.docx
python scripts/apply_font_roles.py input.docx --out output.docx
```

字体处理器生成副本，更新主题字体、文字字体设置并清空页眉，保留正文和页脚。处理后仍需检查分页及目标软件的实际显示。

系统字体查询不证明 WPS 或 Word 实际使用了哪种字体；泛化的“缺失字体”提示也不证明缺的是宋体。主题标签不是另一种字体的名称。

## 来源与适用范围

- 附件1：湘潭大学法学学部本科毕业论文模板（含过程材料）
- 附件2：湘潭大学法学学部本科毕业论文注释与参考文献标准

依据文件在2026年10月11日整理；部分原批注提及2024届。使用时核对自己所在年级、专业的实际要求，不套用模板旧进度日期或示例信息。本技能不默认用于其他学校或研究生论文。

源文件供核对格式与样例。该仓库没有另行授予学校原附件或其他第三方材料的授权。
