# CMC 投稿包说明（FedRBC）

日期：2026-10-01 ｜ 目标期刊：Computers, Materials & Continua (CMC, Tech Science Press)

## 包内文件

| 文件 | 说明 |
|---|---|
| `FedRBC_cmc.tex` | 主稿（TSP 模板，`[cmc,article,submit,moreauthors,pdftex]`） |
| `FedRBC_cmc.pdf` | 编译产物（28 页，0 错误、0 未定义引用） |
| `Definitions/` | 官方模板宏包（tsp.cls、package.tex、unicode.tex、vancouver.bst 等） |
| `Figures/` | 9 张图（PDF 矢量版：fig1–fig3 架构/时序/声誉流 + fig5–fig10 实验图；原 fig4 闭环图已删，改为正文文字表达） |
| `Cover_Letter.md` | 投稿信（含原创声明、作者责任、利益冲突、APC 承诺） |
| `preview_p1/p2.png` | 首页/次页版式预览 |

## 对官方模板的三处最小修改（均在 `Definitions/package.tex`，均为"注释掉未使用包"）

1. `%\usepackage{CJKutf8}` —— 本文无中文；
2. `%\usepackage{bbm}` —— 指示函数改用 `\mathbf{1}`（标准 amsfonts），不依赖 bbm；
3. `%\usepackage{verse}` 及相关 `\theHpoemline` hack —— 仅诗歌排版使用，本文不用。

其余（tsp.cls、unicode.tex、vancouver.bst、journalnames.tex）与官方原版一致。

## 合规对照（CMC Instructions for Authors）

| 要求 | 状态 |
|---|---|
| 摘要 200–400 词（Research Article） | ✅ 308 词 |
| 关键词 3–10 个 | ✅ 6 个 |
| Vancouver 参考文献（前6作者+et al.，含 DOI/CrossRef 链接） | ✅ 54 条 |
| Acknowledgement | ✅ Not applicable |
| Funding Statement（含项目全称与编号） | ✅ 25360301D |
| Author Contributions（CRediT，研究论文必需） | ✅ |
| Data Availability（公开仓库） | ✅ github.com/tangsng/FedRBC |
| Ethics Approval | ✅ Not applicable（无人类/动物实验） |
| Conflicts of Interest | ✅ 无利益冲突 + 资助方无角色声明 |
| 作者信息（3人、单位邮编、通讯作者、全部邮箱） | ✅ |
| 公式可编辑（非图片）、连续编号 (1)–(14) | ✅ |
| 图 caption 在下、表 caption 在上 | ✅ |
| 行内引用 ≤5 连续、`[xx]` 方括号数字 | ✅ |

## 投稿步骤

1. 在 CMC 在线系统注册/登录，选择 "Research Article"；
2. 上传 `FedRBC_cmc.tex` + `Definitions/` + `Figures/` 打包为一个 ZIP（编辑部需重编译）；
3. 将 `Cover_Letter.md` 内容粘贴/上传为 Cover Letter；
4. 系统内逐条填写作者信息、单位、邮箱（与 tex 一致）；
5. 按需在系统内添加推荐审稿人。

## 备注

- `\articlenumber{0}`、DOI 后缀 `000000` 为 submit 模式占位，录用后由编辑部切换 `submit`→`accept` 并分配编号；
- 2 处 Overfull \hbox（18pt / 1.1pt）为排版微溢出，录用清样阶段由编辑部处理，不影响审稿。
