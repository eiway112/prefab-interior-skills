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
├── 成果/ 文档/ 记录/        ← C3：交付物 / 方案文档 / 67 份执行记录
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
| `python 程序文件/validate_governance.py` | 总评 PASS，通过 171 / 失败 0 / 警告 2，exit 0。**硬判据是「失败 0 + exit 0」**；通过/警告计数随索引本体内容浮动（检查 4 与检查 5 都从本体算数），不得按固定数字判回归。警告来自检查 5「SRE 静态体检 T-A1—T-A5」的首轮 WARN 档位（T-A1 名称差分 14 处、T-A5Ⅱ 升档标注），不计 `fail_count`。**T-A1 已不属观察期保留组**（其最后 1 处外部真值依赖已按设计方案 §7.4 通道 ② 裁定并落地），但**档位维持 WARN**——升 FAIL 须待其余 14 处差分修完并另线改 `程序文件/validate_governance.py`，见 CG-20260915-001、CG-20260916-001 与 CG-20260916-002 |
| `python 程序文件/ace_regression_test.py` | Ran 90 tests，OK |
| `python ~/.qoder/skills/prefab-standards-reviewer/sre_regression_test.py` | Ran 30 tests，`OK (expected failures=7)`，exit 0。7 例 expectedFailure = SRE 确定性体检行为组 T-B1—T-B7（缺陷未修期间挂档以护 exit code），实跑产物 `sre_regression_report.json`（已被 `.gitignore` 收录，机器本地）。见 CG-20260916-002 |
| `python ~/.qoder/skills/prefab-standards-reviewer/sr_ic07_compliance_test.py` | Ran 20 tests，OK。**计数硬编码**（`SR_REDLINE_COUNT`、`REGISTRY_TOTAL_COUNT`），红线注册类变更须回扫 |
| `python 程序文件/sync_skill_backup.py` | 把 `~/.qoder/skills/` 运行时技能回写 `技能仓备份/` 镜像。**未验证基线**：CG-20260829-001 ⑤ 记其 `同步说明.md` 哈希清单失准、待重跑 |

> **SRE 门禁转红时的正确动作（设计方案 §6.2，不是故障）**：若 `sre_regression_test.py` 报 `FAILED (unexpected successes=N)` 并 exit 1，说明对应缺陷已被真实修复——须摘掉该用例的 `@unittest.expectedFailure` 装饰器、把断言转为正向常态断言，**禁止回退或注释 `sre_reasoner.py` 的修复来让用例重新"预期失败"**。

`validate_governance.py` 从本体算数不硬编码计数；`sr_ic07_compliance_test.py` 等硬编码计数的脚本是盲区，红线注册类变更须回扫。
