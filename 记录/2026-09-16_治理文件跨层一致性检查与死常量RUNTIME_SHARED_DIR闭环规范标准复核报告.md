# 治理文件跨层一致性检查（检查 6）与死常量 `RUNTIME_SHARED_DIR` 闭环（CG-20260916-010）规范标准复核报告

## 复核日期

2026-09-16（建单、改码、取证、登记同日完成；四门禁末次实跑见「收口读数」一节）

## 复核对象与触发依据

| 项 | 内容 |
|---|---|
| 被测件 | `程序文件/validate_governance.py`（改前 `903d2d3c5bda2b97`／58,164 B／HEAD 前像 → 改后 `6e818969eb950846`／68,385 B／1,469 行／CR 字节 0；版本头 v1.5.1→v1.6.0；7 处 hunk，+180／−3 行，`git diff --numstat HEAD` 同值） |
| 唯一改动码件 | 同上。`git status` 本批工作树内除本报告与 -009 遗留的未入库报告外无其他改动件 |
| 触发依据 | CG-20260916-009 遗留 (c)「`validate_governance.py:77` `RUNTIME_SHARED_DIR` 零引用致校验面无跨层比对（与 F-02 同源，属结构性加固）」＋ CG-20260916-006 既存偏差第一项同源；发起人 2026-09-16 建单授权开本线，并要求「先报建单不动码，我说『开』再落」 |
| 定级 | **B 级**。校验器检查面新增属 `change-governance.md` §一 的 B 级范畴，先例：CG-20260915-001「新增检查 5：SRE 静态体检 T-A1—T-A5」＝ B 级；CG-20260813-036／-037「检查 2 校验范围由 4 条／9 条扩展」＝ B 级。§4.5 未把 `validate_governance.py` 列 A 级模块（A 级面是运行时推理算法与契约），本批对 `sre_reasoner.py` 零改动，故不升档 |
| 授权面 | `程序文件/validate_governance.py` ＋ `AGENTS.md` 验收门禁表 validate 行 ＋ `CHANGELOG.md` ＋ `change-governance.md`（L1 ＋ 两份镜像）＋ 本报告 |
| 未授予 | `git commit`（本批成果现处工作树未入库态）；`sre_reasoner.py`、`sre_regression_test.py`、`interface-contracts.md`、`standards-index.md` 本体、`standards-reasoning-rules.md`、设计方案文档、`sync_skill_backup.py` 均在禁改面 |
| 档位裁定 | **首轮即 FAIL 档**（计入 `fail_count`）。发起人的落地前置是「须先实测确认当前 0 差异，否则打破门禁基线『失败 0』」——改前实测得 0 差异（见下），前置成立。与检查 5 的 WARN 档位区别在于：检查 5 有 14 处外部真值依赖未清，本检查是同机字面哈希比对，不依赖任何外部真值 |

## 独立性声明与本次复核的局限（如实披露）

1. 本批复核由同一执行线在线完成（沿 CG-20260915-001、-002、-003、-004、-005、-009 先例），复核子代理与改码子代理同会话，**非独立第三方审阅**。为压低自证风险：断言的比对集是逐文件声明的常量表（`CROSS_LAYER_SET:1245`），其成员与 `sync_skill_backup.py` 的管辖范围做了**双向互查**（该脚本以 AST 现读，不 import、不作判据源复制）；并设 I-A—I-E 五组注入作为门禁绑定力的外部检验。
2. 本批未调用 prefab-standards-reviewer 的「技术指标表格核验」主功能：`standards-index.md` 本体与技能 reference 未触及，无数值型指标改动。实际核验面为「跨层字节是否全等、检查是否漏配、降级是否显式、新增检查是否仍能失败」四项。
3. 报告中所有哈希为 `sha256` 原始字节前 16 位（`sha256(p.read_bytes()).hexdigest()[:16]`），不做 eol／编码归一；所有行数以文件末行含换行的 `wc -l` 口径。任一读数可按此配方复算。
4. **取证过程中一处探针缺陷（不属被测件缺陷）**：首轮分类注入结果时以 `"(A)" in line` 匹配，而捕获行带报告前缀 `"x "`，导致打印「属检查 6：(A) 0 条／(B) 0 条」的假象；第二轮去前缀后分类正确。上表的 (A)／(B) 计数来自第二口径（先剥 `x ` 前缀再判前缀），FAIL 行文本本身在两轮回读中一致。

## 改前逐项实测（绑改前件哈希 `903d2d3c5bda2b97`）

### 1. 死常量确认（AST，不 import）

| 常量 | 改前：赋值行／`ast.Load` 引用数 | 改后：赋值行／`ast.Load` 引用数 |
|---|---|---|
| `RUNTIME_SHARED_DIR` | `:77` ／ **0** | `:100` ／ **1**（`:1286` 检查 6 `layer_dir`） |
| `RUNTIME_SKILLS` | `:75` ／ 2 | `:98` ／ 4 |
| `SRE_DIR` | `:76` ／ 1 | `:99` ／ 1 |
| `REPO_BACKUP_DIR` | 无此常量 | `:103` ／ 3（新增） |
| `REPO_BACKUP_SHARED_DIR` | 无此常量 | `:104` ／ 1（新增） |

即：改前件里 `RUNTIME_SHARED_DIR` 是一枚**声明后零消费**的常量——三层结构在治理文件里被反复声明为必须，但校验面从未比对过 L1↔L3↔仓内，这正是 -006 靠人工同步才发现「三份镜像落后三行」、-009 靠人工同步才带平 `standards-reasoning-rules.md` 的机制成因。条文存在而生效路径上没有承担者，属个人记忆《条文存在≠机制生效：查生效路径四类断点》所载第二类。

### 2. 跨层现状（本批落地 FAIL 档的前置判据）

配方：五层各自 `sha256(原始字节)[:16]`；层路径 L1=`_专题_技能合集策划/`、RT_ROOT=`~/.qoder/skills/`、RT_SHARED=`~/.qoder/skills/shared/`、REPO_ROOT=`技能仓备份/`、REPO_SHARED=`技能仓备份/shared/`。

| 件 | L1 | RT_ROOT | RT_SHARED | REPO_ROOT | REPO_SHARED |
|---|---|---|---|---|---|
| standards-index.md | `40334c38412017d3` | 同 | 同 | 同 | 同（五层全等） |
| change-governance.md | `fe230db9e33202e4` | 不存在 | `fe230db9e33202e4` | 不存在 | 同 |
| glossary.md | `cb710982b458e3e2` | 不存在 | 同 | 不存在 | 同 |
| interface-contracts.md | `581e83dd15a63cba` | 不存在 | 同 | 不存在 | 同 |
| redlines-registry.md | `31d168e7acb4765c` | 不存在 | 同 | 不存在 | 同 |
| standards-reasoning-rules.md | `0bfb4f529c88133e` | 不存在 | 同 | 不存在 | 同 |
| platform-adapter-reference.md | **不存在** | `cea4bb23296ea5ee` | `364fe021c4d78027` | `cea4bb23296ea5ee` | `364fe021c4d78027` |

**结论：按本检查的断言口径，改前差异 0 处**，故 FAIL 档可落地且不打破「失败 0」基线。两点必须写清，否则上表会被读成矛盾：

- `platform-adapter-reference.md` 的 RT_ROOT ≠ RT_SHARED（差 147 B）**不计为差异**：该件 SOT 直接建于运行时根、项目仓无 L1 开发副本（`技能合集总入口策划方案` 文件清单），根与镜像的头部差异系 `prefab-governance-sync` 约定（根含 SOT 声明＋镜像说明），故它只参与同层比对（RT_ROOT↔REPO_ROOT、RT_SHARED↔REPO_SHARED），两条均全等。
- `standards-index.md` 的头部约定（`prefab-governance-sync:40`）当前**未被维持**——五层字节全等，这与 CG-20260916-006 ⑧(b) 登记的既存偏差同源。本批不裁定该偏差（超出授权面），采取的做法是把该耦合**写进声明表的备注并在通过态以 INFO 显式打印**：若日后恢复头部约定，本件必须同批改为「本体比对＋头部豁免」，否则假红。见 F-01。

### 3. 改前门禁基线

`python 程序文件/validate_governance.py` → 总评 PASS｜通过 171｜失败 0｜警告 2｜exit 0（两条警告：检查 5 T-A1 名称差分 14 处、T-A5Ⅱ 升档标注）。

## 改后逐项实测（绑改后件哈希 `6e818969eb950846`）

### 1. 检查 6 结构与读数

新增：`import hashlib`、常量 `REPO_BACKUP_DIR`／`REPO_BACKUP_SHARED_DIR`、`CROSS_LAYER_SET`（`:1245`，7 件逐文件声明分层归属）、`sha256_file()`、`check_cross_layer()`（`:1278`）、`main()` 内 `:1461` 挂载点（检查 5 之后）。

| 项 | 读数 |
|---|---|
| (A) L1→下游副本全等 | **14 项 PASS**（standards-index 4 层 ＋ 其余 5 件各 RT_SHARED／REPO_SHARED 2 层） |
| (B) 运行时↔技能仓备份同层全等 | **9 项 PASS**（含 platform-adapter 两条同层对） |
| 声明集 ↔ sync 脚本管辖范围双源互查 | **1 项 PASS**（7 件，对称差 0） |
| 检查 6 PASS 合计 | **24**（INFO 8 条：3 条归属备注 ＋ 1 条「无 L1 归属→不入 (A) 链」＋ 覆盖面边界 ＋ 哈希口径 ＋ 层路径 ＋ 比对计数） |
| 门禁总读数 | PASS｜通过 **195**｜失败 0｜警告 2｜exit 0 |
| 增量核对 | 195 − 171 = **24** = 检查 6 的 PASS 条数；警告仍为 2（T-A1 14 处、T-A5Ⅱ），未新增警告面 |

比对项计数取 `a_checked + b_checked = 14 + 9`，`platform-adapter-reference.md` 因无 L1 不入 (A) 链，故 (A) 不是「7 件 × 层数」的对称矩阵——这是刻意设计：不拿不存在归属的层去凑断言。

### 2. 断言为何拆两条（不合成一条「全等」）

两条断言抓的是两类不同的失效，合成一条会互相掩盖：

- **(A) L1 → 下游副本**：抓「L1 已改、下游未带平」。先例即 CG-20260916-004 ⑧(b) 记录的「`change-governance.md` 两份镜像缺 -001／-002/-003 三行（L1 318 行 vs 镜像 315 行）」与 -005 遗留 (a)「因本批 L1 编辑重新落后」。这类跨批落后**只在 L1 与下游之间可见**，运行时↔仓内比对看不出来。
- **(B) 运行时 ↔ `技能仓备份/`**：抓「sync 漏跑或半跑」。-009 F-06 实测的「范围外件首跑即被移除」、-006 ④ 的「`.pyc` 被带进镜像」都发生在这一层对之间。

失效模式不同 → 判据文案也不同（(A) 指向 `prefab-governance-sync` 带平，(B) 指向 `sync_skill_backup.py` 重跑），避免报红后不知道该跑哪条命令。

### 3. 三条自律（按建单硬约束逐条落实）

| 建单约束 | 落实 | 实测证明 |
|---|---|---|
| 比对集逐文件声明、不用目录 glob | `CROSS_LAYER_SET` 7 件枚举 | I-C 注入一枚假件即复红；glob 会把 `*_pre*` 回退件、`.bak` 一起卷进来 |
| 不读 `同步说明.md` 哈希清单作基准 | 全检查只 `read_bytes()` 算哈希 | 该清单是 `sync_skill_backup.py` 自己的产物，以其为基准属自指——工具说一致就算一致 |
| 运行时不可达按 `:893` 既有口径降级 WARN | 只降级 `RUNTIME_LAYERS = ("RT_ROOT","RT_SHARED")` | I-D：2 条 WARN、9 处逐项列出、**0 FAIL、非静默通过**；L1／仓内属固定面，缺失仍 FAIL |

## 反向注入取证（新增检查是否仍能失败）

依个人记忆《摘档/修净后的守卫须仍能失败》：断言恒真＝空跑。五组注入均在**本会话内**完成，文件级注入逐字节还原并复验。

| 案 | 注入 | 预期 | 实测读数 | 还原 |
|---|---|---|---|---|
| I-A | L1 `glossary.md` 尾部追加一行（模拟「L1 改了、下游没跟」） | (A) 复红、(B) 不受染 | **exit 1｜FAIL 2 条**，全为 `(A) glossary.md：RT_SHARED ／ REPO_SHARED ≠ L1`；(B) 0 条；总评 FAIL｜193｜2｜2 | `cb710982b458e3e2` 逐字节还原、`git diff` 空、复跑 exit 0｜195｜0｜2 |
| I-B | `技能仓备份/platform-adapter-reference.md` 尾部追加一行（模拟 sync 半跑） | (B) 复红、(A) 不受染 | **exit 1｜FAIL 1 条** `(B) platform-adapter-reference.md：RT_ROOT cea4bb23296ea5ee ≠ REPO_ROOT 624f5dd8bb8da95a → sync_skill_backup.py 漏跑或半跑`；(A) 0 条；总评 FAIL｜194｜1｜2 | `cea4bb23296ea5ee` 还原、`git diff` 空、复跑 exit 0｜195｜0｜2 |
| I-C | 声明表加入一枚实际不存在的治理件（导出面越界） | 复红且不漏报归属 | **FAIL 4 条**：越界 1 条（`在 CROSS_LAYER_SET 内而不属 sync_skill_backup.py 范围 → 声明表越界，须核归属或让该脚本纳管`）＋ 三层各 1 条「声明归属…实际无此件」 | 内存态注入，未触盘 |
| I-D | 运行时层指向不存在目录（模拟无技能仓的机器） | 降级 WARN、不判红、不静默 | **0 FAIL**；2 条 WARN（不可达声明 ＋ `降级不判项 9 处：standards-index.md@RT_ROOT、…platform-adapter-reference.md@RT_SHARED`，末句显式标注「运行时不可达所致，**非该层与 L1 一致**」）；(A) 的仓内侧 7 条仍 PASS | 内存态注入，未触盘 |
| I-E | 声明表清空（模拟整检查失效） | 不得判绿 | **FAIL 8 条**：7 条漏配（`在 sync_skill_backup.py 管辖范围内而 CROSS_LAYER_SET 未声明 → 该件的跨层漂移不经门禁（漏配）`）＋ 1 条空跑判据 `(A)(B) 零比对项且非降级态 —— 声明表或层路径已失效，本检查不得判绿` | 内存态注入，未触盘 |

I-A 与 I-B 分别只复红一条断言，证明两条断言**互不掩盖**；I-C／I-E 是 I-A／I-B 的镜像方向（越界 vs 漏配），双向都有判据；I-D 证明降级是「显式不判」而非「默默通过」——这是本批唯一一处无法用真实数据证伪的方向（机器本地无第二套运行时），故以合成注入承担。附带一条非显然分工：`(B)` 在 platform-adapter 上的绑定力**只来自该件的两条同层对**，其余 6 件的 (B) 与 (A) 共享同一份哈希来源，(B) 对它们不构成独立失效面（见 F-02）。

## 复核发现与处置（F-01—F-07，均在落码轮内处置）

| 号 | 级别 | 发现 | 处置 |
|---|---|---|---|
| F-01 | 中（登记不处置） | `standards-index.md` 五层字节全等与 `prefab-governance-sync:40` 的「根含 SOT 声明＋镜像说明」头部约定相互矛盾——若日后恢复头部约定，本件 (A) 链将假红 | 不改比对语义（那需要裁定 CG-20260916-006 ⑧(b)，超出本线授权）。改为把该耦合写进声明表备注 ＋ 通过态 INFO 打印，恢复头部约定时必须同批改本件 |
| F-02 | 中（覆盖面边界，登记不处置） | (B) 实际只覆盖 7 件治理件；技能目录内约 114 件（SKILL.md／reference.md／examples.md／scripts）与机器本地产物（`sre_regression_report.json`）不在面上，「sync 漏跑」在这一大片仍无人守 | 在检查尾部以 INFO 显式声明覆盖面边界，不冒充全量；扩至技能目录须另案（涉及 `.pyc` 排除面与机器本地件判据，见遗留 (b)） |
| F-03 | 高（程序性，当场整改） | 首版声明表是自指的：只有 `CROSS_LAYER_SET` 自己知道覆盖哪些件，`sync_skill_backup.py` 的 `ROOT_FILES`＋`SHARED_FILES` 若增删成员，本检查不会察觉漏配 | 新增 AST 现读该脚本范围常量、与声明集做对称差，双向 FAIL（越界／漏配）；由 I-C、I-E 分别证两方向能失败。脚本本体属禁改面，未写入其产物作基准 |
| F-04 | 中（当场整改） | 首版降级 WARN 文案沿用检查 5 的「无技能仓的机器上门禁不炸」，与本检查「L1／仓内缺失仍 FAIL」实际行为矛盾；且不列出被跳过的是哪些 (文件,层) 对 | 文案改写为「只降级不判红；L1 与 `技能仓备份/` 属本仓固定面，缺失仍判 FAIL」，并新增逐项 `降级不判项 N 处：…@…` 清单（I-D 实测 9 处） |
| F-05 | 低（当场整改） | 哈希口径未声明：`sha256(原始字节)` 不做 eol 归一，跨机 `core.autocrlf=true` 的克隆会把 `技能仓备份/` 层转成 CRLF 而产假红 | 尾部新增 INFO 记录口径与本机实测（`git config core.autocrlf=false`；治理件 CR 字节 0；唯 `platform-adapter-reference.md` 四层均 CRLF 26 处，故它本就带 CR，不受归一影响）；`.gitattributes` 缺失登记为遗留 (c) |
| F-06 | 低（当场整改） | 层路径来源不显：`main()` 有 `--runtime-dir` 选项，读者会以为检查 6 随之改变，实际取模块常量 | 尾部 INFO 打印三层实际解析路径并标注「不受 `--runtime-dir` 影响」；该不一致同写入版本变更块 |
| F-07 | 程序性 | 建单只写「新增跨层比对＋消除死常量」，未写档位；FAIL 档会直接改门禁基线数字（171→195）与 AGENTS.md 判据 | 落地前先实测 0 差异（改前实测一节）再上 FAIL 档；同批改 AGENTS.md 门禁行；按记忆《是否型请求默认只读，扩范围须当场申请》，未越面去改 `sync_skill_backup.py` 或技能目录 |

## 收口读数（四门禁，2026-09-16 同日实跑）

| 命令 | 读数 |
|---|---|
| `python 程序文件/validate_governance.py` | 总评 PASS｜通过 **195**｜失败 0｜警告 2｜exit 0（警告仍为 T-A1 14 处、T-A5Ⅱ 升档标注；检查 6 无 WARN） |
| `python 程序文件/ace_regression_test.py` | Ran 90 tests，OK |
| `python ~/.qoder/skills/prefab-standards-reviewer/sre_regression_test.py` | Ran 37 tests，`OK`（无 expected failures 亦无 unexpected successes），缺口信号 0 条，跨轮指纹 `4f53cda18c2baa0c`（与 -009 同值，连续一致 30 轮） |
| `python ~/.qoder/skills/prefab-standards-reviewer/sr_ic07_compliance_test.py` | Ran 20 tests，OK |

### 三层镜像带平与 sync 收敛

| 步 | 动作 | 读数 |
|---|---|---|
| ① | 登记前 L1 编辑 | `change-governance.md` L1 由 `fe230db9e33202e4`／245,587 B → `90f00cb89e9a8b09`／256,777 B（CR 字节 0，326 行）；此时两份镜像落后——**这正是本批新检查要自动抓的情形** |
| ② | L1 → L3 运行时 `~/.qoder/skills/shared/`（本批授权写面） | 复制后逐文件比对：L3 `90f00cb89e9a8b09` ＝ L1 |
| ③ | 删两层 `__pycache__/*.pyc` 后跑 `sync_skill_backup.py` | 首跑「范围 122｜一致 120｜新增 0｜更新 2｜移除 0」（两条更新＝`shared/change-governance.md` 与机器本地件 `prefab-standards-reviewer/sre_regression_report.json`，后者系上一步载体 B 复跑重生成、已由 `.gitignore` 收录）；二跑收敛至 **「范围 122｜一致 122｜新增 0｜更新 0｜移除 0」** |
| ④ | 三份互等复验（判据取状态关系，不写本文件终值哈希，依 CG-20260916-004 ⑧(b)） | L1 ＝ L3 ＝ 仓内 `技能仓备份/shared/`，sha256 前 16 位三者相等 |
| ⑤ | 检查 6 在同一状态下复跑 | 24 条 PASS、0 FAIL、0 WARN——即「镜像带平」这一事实现由门禁自身而非人工确认 |

**顺序纪律（本批实测确认，写下来防下批复踩）**：`sync_skill_backup.py` 的方向是**运行时 → 仓内**，所以必须先把 L1 复制进 `~/.qoder/skills/shared/` 再跑该脚本；否则脚本会拿落后的运行时去刷新仓内镜像，把带平做成带偏。

## 影响面

- **运行时行为零影响**：`validate_governance.py` 是仓内门禁件，不被任何技能 import；`sre_reasoner.py`／`sre_regression_test.py`／契约／索引／rules.md 本批逐字未改（改后复核：`interface-contracts.md` 仍 `581e83dd15a63cba`、`standards-index.md` 仍 `40334c38412017d3`、`standards-reasoning-rules.md` 仍 `0bfb4f529c88133e`）。
- **门禁基线变化一处**：通过项 171 → 195（＋24，全部来自检查 6）。判据仍按 AGENTS.md「硬判据是失败 0 ＋ exit 0，通过/警告计数随本体内容浮动」——但本批的 ＋24 是**结构性的**（新增检查），故同批改写 AGENTS.md 该行，避免下批把它当漂移来查。
- **新门禁会在真实漂移发生时判红**：I-A／I-B 已证。日常效果是 -004⑧(b)、-005(a)、-006、-009 这四次「人工发现镜像落后」此后由门禁自动发现。

## 遗留项（须另行授权，本批不处置）

| 号 | 事项 | 为什么本批不做 |
|---|---|---|
| (a) | F-01 头部约定与五层全等的矛盾，须裁定 `standards-index.md` 到底该不该有根／镜像头部差异（随 CG-20260916-006 ⑧(b)） | 裁定会改 `prefab-governance-sync` 的同步语义，超出「改校验器」授权面 |
| (b) | F-02 (B) 面不覆盖技能目录约 114 件；扩面须先解决 `sync_skill_backup.py` 不排除 `__pycache__/*.pyc` 与机器本地件的判据 | 该脚本属本批禁改面 |
| (c) | 仓内无 `.gitattributes`，跨机 `core.autocrlf=true` 克隆可使 `技能仓备份/` 层转 CRLF → 检查 6 假红（F-05 只记录了口径，未消除诱因） | 新增仓库级配置文件属另一类变更 |
| (d) | CG-20260916-009 复核报告 `记录/2026-09-16_M1前缀不可识别支…复核报告.md` 至今仍 untracked；与本 -010 报告同属「已入库文档引用未入库文件」的悬空引用（-007 曾为此专门补登记 -008） | 提交须 `git commit` 授权，本批未授予 |
| (e) | -009 遗留 (a)(b)(d)(e) 四项（`DOMAINS` 死映射键、M4 规则 5 `SJG` 死测试、T-A1 余 14 处差分、rules.md:3 陈旧部署路径）本批未触及 | 均与本线判据无关，另案 |

## 结论

**B 级线内复核：通过。** 检查 6 已实装并计入 `fail_count`，当前 0 差异故不打破「失败 0」基线；`RUNTIME_SHARED_DIR` 由死常量转为唯一消费点（`:1286`），-009 遗留 (c) 闭合；新增检查的绑定力由 I-A—E 五组注入自证（2／1／4／8 条复红，降级案 0 FAIL 且逐项列名），文件级注入均已逐字节还原并复验。本批**未 git commit**（未授予），成果处工作树未入库态。
