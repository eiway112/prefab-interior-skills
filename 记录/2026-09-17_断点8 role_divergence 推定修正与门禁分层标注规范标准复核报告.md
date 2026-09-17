# CG-20260917-004 规范标准复核报告

> **批次**：CG-20260917-004（B 级）P1 整改 item 11（断点8 role_divergence 推定修正）＋ item 14（门禁分层标注）
> **复核角色**：prefab-standards-reviewer（线内复核）
> **复核日期**：2026-09-17
> **复核结论**：**PASS**（附 OBS-1／OBS-2 两项登记不处置）
> **触发文件**：`成果/第三方机制与行为审阅评估及整改方案_20260916.md` §三 断点8 ＋ §6.3 ＋ P1 列表 item 11/14

---

## 一、复核背景与定级

第三方审阅整改方案 §三 列「八处生效路径断点」，断点8 称 T-A1（`validate_governance.py` 门禁）的 role_divergence 信号「名称差分会改 M4 角色」；§6.3 提出门禁应分「机检层／判断层」，并称场景级期望值断言「当前完全缺失」。P1 列表 item 11＝修正断点8 推定，item 14＝门禁分层重构。

- **定级 B 级**：依 CG-20260916-010 先例「校验器检查面变更＝B 级」。§4.5 未列校验器为 A 级模块（A 级面是运行时推理算法与接口契约）；本批对 `sre_reasoner.py` 推理算法、`interface-contracts.md` 契约、`standards-index.md` 本体、`standards-reasoning-rules.md` **零改动**，T-A1 属 WARN 档不计 `fail_count`，硬判据「失败 0＋exit 0」零影响，故不升档。
- **授权链**：用户「按你的建议直接推进，过程中若没有专业难点请直接推进，只有在必须用户确认或需要开新线时再停下来」延续 P1 推进授权；本批**首次开启「门禁自改」线**（动 `程序文件/validate_governance.py`——-001/-002/-003 三批均明文「本批不动」、历次复核把「其哈希未变」当红线通过判据的门禁本体），属 blast-radius 升级／开新线，另经 AskUserQuestion 明示裁定「授权，一个 B 级批同落两项」构成 §二 第 3 步确认。
- **未授予 git commit**：成果处工作树未入库态。

## 二、核验面（复核者自定的核验项）

1. 断点8 反事实是否**亲跑可复现**（非采信第三方报告）。
2. 门禁 item 11 文案订正是否**只去假声称而不改计数**（14 处名称差分／2 处关键词差分／WARN 档／exit code 均不变）。
3. 门禁 item 14 header 分层行是否**真不计入** `total_pass/fail/warn`（即 195/0/2 与 exit code 不受影响）。
4. 判断层守卫 `test_BP8` 是否**非恒真空跑**（有正向对照 ＋ 经反向注入证伪）。
5. 是否**越界触碰** reasoner／契约／索引本体。

## 三、逐项核验

### 核验项 1：断点8 反事实实测（PASS）

复核者亲跑反事实（D 盘临时脚本、运行时零写入、用毕删除），**不采信**第三方报告的因果声称：

| 标准编号 | 层级 | 权限 | 名称含「测量/评价」 | baseline 角色 | 去关键词后角色 | 判定 |
|---|---|---|---|---|---|---|
| `DB33/T 1168-2019` | L2 | binding_support | 是（评价） | design_basis | design_basis | **UNCHANGED** |
| `DBJ/T 15-208-2020` | L2 | binding_support | 是（评价） | design_basis | design_basis | **UNCHANGED** |
| `SJG 159-2024`（对照） | L4 | reference | 是（评价） | verification_reference | — | 名称支活代码 |

**根因**：`DB33/T 1168-2019`、`DBJ/T 15-208-2020` 经断点7（CG-20260917-002，DB/DBJ 层级 L3→L2）后属 **L2/binding_support**，角色在 `sre_reasoner.py:695-696`（`L2/L3 ＋ binding_support → design_basis`）即定、**永不到达名称敏感的 :697 支**（`elif "测量"/"评价" in 名称 → verification_reference`）。:697 名称支为**活代码、只被 binding_support 支遮蔽**——对照 `SJG 159-2024`（L4/reference、名含评价）落 :697→verification_reference 即证。

**结论**：第三方断点8「名称差分会改 M4 角色」的因果声称**被实测推翻**。门禁 `validate_governance.py:981` 文案两缺陷成立：(a) **陈旧行号「:506」**——v1.5 名称→角色逻辑实际在 :697，:506 系旧版 reasoner 行号未随 v1.3→v1.5 刷新；(b) **过度声称**「role_divergence 2 处经 :506 改变 M4 角色与排序」与实测矛盾。

### 核验项 2：item 11 处置只去假声称不改计数（PASS）

处置依 item 14 §6.3「机检层只裁存在性、真伪归判断层」：

- 检测**保留**为「关键词存在性差分」（变量 `role_div`→`kw_div`、`n_role`→`n_kw` 消 misnomer），检测逻辑 `(("测量" in sre_name, "评价" in sre_name) != ("测量" in idx_name, "评价" in idx_name))` **逐字未改**。
- 去假因果声称、订正 `:506`→`:697`、msg 改实测口径（名称仅在 :697 非 L1 且非 L2/L3-binding_support 支参与 verification_reference；当前 flagged 属 L2/binding_support→角色恒 design_basis、名称差分不实际改角色）、detail 标签「［role_divergence］」→「［关键词差分·实测不改角色］」、加 4 行注释说明机检层／判断层分工。

**计数核验**：14 处名称差分、2 处关键词差分（`n_kw＝2`）、WARN 档、`fail_count`、exit code **均不变**。硬判据零影响。

### 核验项 3：item 14 header 分层行不计入计数（PASS）

方案 §6.3 称场景级期望值断言「当前完全缺失」系 2026-09-16 报告时点真相——`sre_regression_test.py:724 TestP0SceneExpectations` 已含 BP1—BP6「给定输入→断言输出标准集」11 例（随 CG-20260917-001/-002 P0 带入），故本批只落**剩余「分层标注」面**。

`Report.print_report()` 标题块 ＋3 行 `print`（本报告全部为【机检层】＝存在性／一致性、【判断层】＝真伪抽样见 `sre_regression_test.py`、机检零 ERROR≠内容正确）。

**计数核验**：3 行系 `print()` 输出、**非** `Report.ok/fail/warn/info` item，不进 `self.sections`，故 `total_pass/total_fail/total_warn` 不受影响。实跑 **195/0/2 exit 0** 与改前逐字一致。

### 核验项 4：判断层守卫 test_BP8 非恒真（PASS）

按 item 14 分层原则，断点8 真伪结论须落判断层有守卫，否则即 P1 要治的「规则写了没人执行」。载体 B **50→51**，新增 `test_BP8_name_keyword_does_not_override_binding_support_role`：

- **遮蔽组**：断言 `DB33/T 1168-2019`、`DBJ/T 15-208-2020` L2/binding_support ＋ 名含评价 → 角色恒 design_basis。
- **正向对照**：动态遍历 `STANDARD_NAMES` 取名含测量/评价且**非 L1／非 binding_support** 者（取 ≥3），断言 → verification_reference；对照组为空即 `assertTrue` 报错防空跑。

**非恒真取证（反向注入，依「修净后的守卫须仍能失败」）**：把 :697 名称支移到 :695-696 binding_support 支之前（注入锚唯一性 `assert count==1` 守卫），`DB33/T` 角色 design_basis→verification_reference、BP8 遮蔽组断言**转红**（RED_OK＝True）；运行时 `sre_reasoner.py` sha16 `db9518a071df0cb9` 注入前后一致（**运行时零写入**，注入打在 D 盘临时副本）、临时件已删。证 BP8 守卫有绑定力、非恒真空跑。

`TestP0SceneExpectations` 类 docstring「P0 断点 1-4」订正为「P0 断点 1-6＋P1 断点8」、模块版本头 v1.6→**v1.7**。

### 核验项 5：未越界触碰（PASS）

| 文件 | 本批状态 |
|---|---|
| `sre_reasoner.py`（运行时推理算法） | **零改动**（`db9518a071df0cb9`） |
| `standards-index.md` 本体 | 零改动 |
| `interface-contracts.md`（契约 v1.9.0） | 零改动 |
| `standards-reasoning-rules.md` | 零改动 |
| `sync_skill_backup.py` | 零改动 |
| 设计方案文档、13 条锚定集、各子技能 SKILL.md 正文 | 零改动 |
| `程序文件/validate_governance.py` | **改**（item 11 文案 ＋ item 14 header）——本批授权面 |
| `sre_regression_test.py` ＋ 仓内镜像 | **改**（v1.6→v1.7、50→51）——本批授权面 |

## 四、门禁读数（2026-09-17 实跑）

| 门禁 | 读数 |
|---|---|
| `validate_governance.py` | **PASS｜通过 195｜失败 0｜警告 2｜exit 0**（计数零变；T-A1 文案订正、header 分层行新增；检查 6 跨层一致性全绿——change-governance 三层 `b5674a240c95098f`） |
| `ace_regression_test.py` | Ran 90 OK |
| `sr_ic07_compliance_test.py` | Ran 20 OK |
| `sre_regression_test.py` | Ran 50→**51** `OK`（既无 expected failures 亦无 unexpected successes）、exit 0、缺口信号 0、跨轮指纹 `4f53cda18c2baa0c` 未漂移 |

## 五、OBS 登记（不处置）

- **OBS-1（程序性，独立性局限）**：复核者与发起人为**同一会话**，B 级线内复核独立性受限（沿 CG-20260917-001/-002/-003 同会话先例如实登记）。
- **OBS-2（低，耦合）**：BP8 遮蔽组前置 `assertIn("评价", DBJ/T 15-208-2020 的 SRE 名)` 依赖 **F-01 争议名称**（CG-20260917-001 F-01：索引 §5.3 名「建筑室内装配式轻质隔墙技术规程」vs SRE `STANDARD_NAMES` 名「广东省装配式建筑评价标准」须官方核验）。若 F-01 裁定改 SRE 名致其不再含「评价」，BP8 前置须同批复核（属**预期耦合**非缺陷，F-01 本身仍「登记不处置、待官方核验」）。

## 六、规模与哈希（绑登记时刻）

| 件 | 哈希（sha256 前 16 位） | 规模 | 备注 |
|---|---|---|---|
| `程序文件/validate_governance.py` | `85912ea6019fa650` | 69,746 B／1,480 行／CR 0 | **仅本仓 1 处副本、无三层镜像、不属 shared 7 件** |
| `sre_regression_test.py`（运行时＝仓内镜像） | `53346fdf95f86286` | 65,358 B／1,220 行 | v1.6→v1.7、cmp 字节全等 |
| `sre_reasoner.py`（运行时） | `db9518a071df0cb9` | — | **本批零改动** |
| `change-governance.md`（三层） | `b5674a240c95098f` | 318,256 B | 三份互等；本行不写本文件终值哈希（依 CG-20260916-004 ⑧(b) 自指先例），复算判据取「三份 sha256 前 16 位互等」 |

`sync_skill_backup.py` 跑前删两层 `.pyc`、首跑「范围 122｜一致 121｜更新 1（change-governance.md）｜移除 0」；`sre_regression_report.json` 系 `.gitignore` 收录机器本地件、不入提交。

## 七、遗留/移交另案

- (a) P1 余项 item 9/10（时效分档＋核验状态现读＋STATUS_UNKNOWN 降级复用，动 `_load_standards_index()`、改动面大于本批宜单独成批）、item 12（ACE 估算值免责）、item 13（红线行为守恒抽样、归判断层）、item 14 剩余「判断层真伪抽样」周期跑机制（本批只落标注面、未建判断层独立跑批／台账）。
- (b) P2（item 15—23 接长闭环＋止通胀）／P3（item 24 真实项目试点）须另行授权。
- (c) CG-20260917-001 遗留 (a) `DOMAINS` 余三处死键、(b) F-01 `DBJ/T 15-208-2020` 名称冲突（须官方核验、OBS-2 与之耦合）本批未触及。
- (d) `AGENTS.md` 门禁表完整对账（本批只刷 SRE 行 Ran 50→51＋用例演进、未逐批回填）。
- (e) 本批未 git commit——注：-001/-002/-003/-010 已随 `637ff90` 单提交入库，本批系其后新增未入库态，提交时序由用户仲裁。

## 八、复核结论

五项核验面全 **PASS**：断点8 因果声称经亲跑反事实推翻、门禁文案订正只去假声称不改计数、header 分层行不计入 pass/fail/warn、BP8 守卫经正向对照＋反向注入证非恒真、未越界触碰 reasoner／契约／索引本体。四门禁读数与改前同值（PASS｜195｜0｜2 exit 0）。OBS-1／OBS-2 登记不处置。**批次 CG-20260917-004 线内复核通过。**
