# AGENTS.md — 装配式装修技能开发

> 本文件是跨对话协作的入口锚点（核心 C1）。**它不定义规则，只告诉你规则在哪**：
> 变更定级与审批的唯一事实源是 `_专题_技能合集策划/change-governance.md`，本文件与其冲突时以该文件为准。

## 项目定位

装配式装修技能合集的**开发与治理主仓**（L1 开发源）。技能本体发布到 Qoder 运行时，本仓持有策划稿、治理文件、备份镜像与全过程记录。

- 远端：`https://github.com/eiway112/prefab-interior-skills.git`（`origin/master`）
- 2026-08-30 自 `D:\QoderWork-Files\_项目工作\` 迁入本工作区顶层，`.git` 随迁、历史完整（94 提交）

## 目录结构

```
装配式装修技能开发/
├── AGENTS.md                ← 本文件（C1）
├── .gitignore               ← C5
├── README.md / CHANGELOG.md / LICENSE
├── _专题_技能合集策划/       ← 治理文件 L1 开发源（7 份 shared 治理文件在此）
├── _专题_隔墙技能策划/ _专题_墙面技能策划/
├── _专题_吊顶技能策划/ _专题_楼地面技能策划/ _专题_ACE开发/
│                            ← 各子技能策划稿、QA 基线与红线草案
├── 技能仓备份/              ← 运行时技能的仓内镜像（sync_skill_backup.py 产物，勿手改）
├── 程序文件/                ← C2：三个校验器（见下）
├── 成果/ 文档/ 记录/        ← C3：交付物 / 方案文档 / 执行记录（件数随批浮动，不钉数字）
└── 素材/                    ← 空占位
```

## 三层结构（必须理解后再动手）

| 层 | 位置 | 性质 |
|---|---|---|
| L1 开发源 | 本仓 `_专题_技能合集策划/` | 可编辑 |
| L2 运行时 SOT | `~/.qoder/skills/` | 技能实际被加载处，唯一事实源 |
| L3 只读镜像 | `~/.qoder/skills/shared/` | 治理文件镜像 |

同步流程与验收步骤见运行时技能 `prefab-governance-sync`；**定级（S/A/B/C）与审批看 `change-governance.md`，不看该技能**。

## 改任何共享治理文件前

1. 读 `change-governance.md` §一定义表 + §二流程，**先查先例再定级**（环境路径/BOM/换行类修正属 C 级，可由发起人直接执行并登记）
2. 改完必须：`技能仓备份/` 同步 → 三份 `change-governance.md` 镜像哈希一致 → 登记 CG 编号
3. 历史 CG 行与 `记录/`、`CHANGELOG.md` 中的旧路径**不改写**（属当时事实快照）

## 验收门禁（改完必须实跑，不接受"应该没问题"）

| 命令 | 当前基线 |
|---|---|
| `python -B 程序文件/validate_governance.py` | **【活基线：CG-20260917-009，v1.7.0】**总评 PASS，通过 **194** / 失败 0 / 警告 3，exit 0。**硬判据是「失败 0 + exit 0」**；通过/警告计数随本体内容浮动，不得按固定数字判回归。195→194 系去掉「无到期任务」的质量 PASS，改为维护 INFO，不是检测失败。警告三处：检查 5 的 T-A1 名称差分 13 处与 T-A5Ⅱ 升档标注，以及检查 3 的 41 条无有效核验日期聚合 WARN；均不计 `fail_count`，不因单纯到期增加 WARN。**T-A1 已不属观察期保留组，但档位维持 WARN**；升级须另线处理，见 CG-20260916-002。**检查 3 当前口径以索引 §1.1A 为准**：按表头分类、列名读取核验日期与状态；日期到期按 92／183 天严格大于现算，显式「到期需复核」任务也须披露，二者报 INFO；无记录／无效或未来日期仍报依据链未确认 WARN，**缺日期不等于已超期或标准失效**。并列编号只按全角 `／` 切分，半角 `/` 属编号本体。运行时 `sre_reasoner.py` v1.7 的 `_verification_confirmed()` 将可复用的既有依据与维护提醒分离：已确认者仅因到期不降级，提醒写入 applicability；未确认者仍 inferred＋§1.1A degradation，补真实依据或接受降级为等价出口。已废止另有 inferred＋TA-3 提示，GB 50118 既有部分替代警告保持；自动替代／暂停能力边界见 rules §4.3。**IC-10 item 字段、枚举与适用集成员不变**，deterministic 不代表本轮重新核实最新状态或工程合规放行。v1.6.0 新增**检查 6「治理文件跨层一致性」**，**首轮即 FAIL 档且计入 `fail_count`**（与检查 5 不同：同机字面哈希比对，无外部真值依赖）——两条断言各自指向修复命令：**(A) L1→下游副本全等** 报红 → 由 `prefab-governance-sync` 按 L1→下游带平（抓 -004⑧(b)／-005(a)／-006 那类跨批落后）；**(B) 运行时↔`技能仓备份/` 同层全等** 报红 → 重跑 `程序文件/sync_skill_backup.py`（抓 sync 漏跑/半跑）。口径四条：比对集是**逐文件声明**的 7 件常量表（不 glob，故 `*_pre*` 回退件与 `.bak` 不入），基准**不读** `同步说明.md` 的哈希清单（那是被测工具自产，属自指），哈希取 `sha256(原始字节)` 不做 eol 归一（跨机 `core.autocrlf=true` 克隆会把 `技能仓备份/` 层转 CRLF 而**产假红**，本机 autocrlf=false），运行时层不可达时按检查 5 同口径**降级 WARN 且逐项列出被跳过的 (文件@层)**，而 L1／仓内属固定面缺失仍判 FAIL。`platform-adapter-reference.md` 无 L1 归属，不入 (A) 链、只比同层。覆盖面**只含声明的 7 件治理文件**，技能目录内约 114 件（SKILL.md／reference.md／examples.md／scripts）与机器本地 `sre_regression_report.json` 不经本检查（F-02 遗留）。声明集与 `sync_skill_backup.py` 的 `ROOT_FILES`＋`SHARED_FILES` 做 AST 现读**双向互查**：声明而不属脚本 → FAIL「声明表越界」；属脚本而未声明 → FAIL「漏配」 |
| `python -B 程序文件/verification_policy_test.py` | Ran 6 tests，OK；检查 3 专项：两档严格边界、到期 INFO 且 WARN/PASS 集稳定、显式复查任务、缺记录／异常日期 WARN、实际状态漂移 FAIL。改核验维护规则时与四项既有门禁一并运行。 |
| `python -B 程序文件/ace_regression_test.py` | Ran 90 tests，OK |
| `python -B ~/.qoder/skills/prefab-standards-reviewer/sre_regression_test.py` | **【活基线，更新至 CG-20260917-009】Ran 66 tests，`OK`**（既无 expected failures 亦无 unexpected successes），exit 0，缺口信号 0 条、跨轮指纹 `4f53cda18c2baa0c`（连击计数属机器本地状态，不钉数字）；IC-10 v1.9.0（零新字段、零新枚举）、reasoner v1.7、rules v1.2.6、测试模块 v1.9。59→66 为维护／依据解耦守卫：GB 55037 第 92／93 天保持完整 item 和确定性、响应内提醒、显式复查任务、缺记录／未确认／异常日期保护，以及未知／已废止／GB 50118 部分替代的独立保护；原分档边界、矩阵成员、契约及防空跑断言继续执行。已确认的确定性对称面排除未知和已废止，废止由专用断言验证。独立验收与故障注入见 CHANGELOG v1.12.15。下方为 CG-20260916-009 历史快照，其版本与计数不作当前基线。 ‖历史快照（-009 时代，不改写）‖ Ran 37 tests，`OK`（**既无 expected failures 亦无 unexpected successes**），exit 0，缺口信号 0 条、跨轮指纹 `4f53cda18c2baa0c`。全文 `^\s*@unittest\.expectedFailure` 现 **0 处**——行为组 T-B1—T-B7 七项已全部转为正向常态断言（T-B1／T-B7 随 CG-20260916-003、T-B2 全条与 T-B4 含 `conversion` 半条随 **CG-20260916-004**、T-B3／T-B5／T-B6 随 **CG-20260916-005** 摘档）。用例数 30→32 系 -005 按 §6.2「摘档须升级为有约束力断言」新增两条收紧用例：`test_TB5_empty_family_negative_path`（合成注入无映射域，因矩阵正例在数据面修净后会恒真空跑）与 `test_TB6_national_and_local_coexist`（逐地点正向期望集，期望值从 `DOMAINS` 现读）。**32→37 随 -009（A 级）**：`test_standard_item_schema` 的 `角色` 断言从「只跑 `reason("住宅","分户墙")` 一组」扩为全 34 组激活对 × 7 地点矩阵遍历（带 `visited`／`checked` 漏组与空跑判据），合法值域从 `~/.qoder/skills/shared/interface-contracts.md` 的 IC-10 `角色` 枚举**现读**；另新增 5 例（图集号命中、索引 §二 编号不降级含 `ZZ 9999-1999` 负向半条、GB 18580-2025 落 `mandatory_check`、08J931 落 `construction_guide`、M4 兜底合成注入），并按「修净后的守卫须仍能失败」做反向注入自证（逐项回退复红 1／2／2、三项合并 6）。测试侧共享 helper `_table()` 已修：数据行必须在首个非表格行截断，否则同小节第二张表（索引 §二 的「官方核验记录」）会被并入首表、其表头单元被当成编号（-009 F-02）。**运行时 `sre_reasoner.py` 版本头自本批起为 v1.3**（-005 遗留 (c) 闭合）。T-B2／T-B4 的前置仍是 IC-10 `时间状态` 枚举由四值扩为与 IC-07 同源的六值（契约 **v1.8.0**）并新增可选 `状态注记`，二者判据现从 `~/.qoder/skills/shared/interface-contracts.md` **现读枚举**，故该契约文件不得落后于运行时消费端。实跑产物 `sre_regression_report.json`（已被 `.gitignore` 收录，机器本地）。历史：7 例挂档见 CG-20260916-002、5 例见 -003、3 例见 -004 |
| `python -B ~/.qoder/skills/prefab-standards-reviewer/sr_ic07_compliance_test.py` | Ran 20 tests，OK。**计数硬编码**（`SR_REDLINE_COUNT`、`REGISTRY_TOTAL_COUNT`），红线注册类变更须回扫 |
| `python -B 程序文件/sync_skill_backup.py` | 把 `~/.qoder/skills/` 运行时技能回写 `技能仓备份/` 镜像。**基线已验证**（CG-20260916-006 ④ 实跑）：清掉两层 `__pycache__` 后为「范围 122｜一致 122｜新增 0｜更新 0｜移除 0」，`同步说明.md` 哈希清单随之刷新（CG-20260829-001 ⑤ 的「失准、待重跑」已闭合）。**本行判据是「范围 122 ＋ 新增 0 ＋ 移除 0」**；一致/更新两数随批浮动（改了哪几件就更新几件），不得按固定数字判回归。**CG-20260917-009** 首跑「范围 122｜一致 116｜新增 0｜更新 6｜移除 0」，末次同步与只读检查见 CHANGELOG v1.12.15；使用 `python -B` 避免新生 `.pyc`，同步前检查范围与差异，出现未知新增／移除须停。以下为历史读数（CG-20260917-006）**首跑**为「范围 122｜一致 119｜新增 0｜更新 3｜移除 0」，更新件＝`sre_reasoner.py`／`sre_regression_test.py`／机器本地 `sre_regression_report.json`（＝本批三件运行时改动带平）；**收尾复跑**为「范围 122｜一致 121｜新增 0｜更新 1｜移除 0」，唯一更新件＝机器本地 `sre_regression_report.json`（前三件已一致，report.json 因复跑门禁被重写）——两次读数差即「本批改了哪几件」，正是本行不得钉固定数字的原因。**已知排除面缺口**：脚本不排除 `__pycache__/*.pyc`，本地 import 后首跑会把 `.pyc` 带进镜像（-004 ⑧(b)、-006 ④），跑前须先删两层 `.pyc`。**反向缺口（-009 实测）**：范围是固定的「15 个技能目录 ＋ 根治理文件 ＋ shared 7 文件」，落在 `技能仓备份/` 内但不属于该范围的件会被当差异**移除**——本批放在 `技能仓备份/shared/` 的 `_pre20260916CG009` 备份首跑即被删（读数「移除 1」）。故仓内镜像侧**不是** `_pre*` 备份件的留存位置，回退判据取 `git show HEAD:<path>` 前像，运行时侧备份件仅机器本地保险 |

> **SRE 门禁转红时的正确动作（设计方案 §6.2，不是故障）**：若 `sre_regression_test.py` 报 `FAILED (unexpected successes=N)` 并 exit 1，说明对应缺陷已被真实修复——须摘掉该用例的 `@unittest.expectedFailure` 装饰器、把断言转为正向常态断言，**禁止回退或注释 `sre_reasoner.py` 的修复来让用例重新"预期失败"**。

`validate_governance.py` 从本体算数不硬编码计数；`sr_ic07_compliance_test.py` 等硬编码计数的脚本是盲区，红线注册类变更须回扫。
