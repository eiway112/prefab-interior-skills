---
name: prefab-governance-sync
description: 装配式装修技能合集治理文件三层同步与发布流程（项目仓策划 ↔ 运行时 skills 根 SOT ↔ shared 只读镜像）。当用户要求同步治理文件、发布技能更新、同步 standards-index/glossary/interface-contracts/红线注册表、或发现三层文件不一致需要修复漂移时使用。变更定级与审批规则不在此技能，以 change-governance.md 为唯一事实源。
version: 1.0.0
---

# 治理文件三层同步（prefab-governance-sync）

## 定位

装配式装修技能合集治理文件的**执行层同步流水线**（薄技能）：只管"怎么同步、怎么验收"。变更定级（S/A/B/C）、审批流程、专项规则的唯一事实源是 `change-governance.md`（项目仓 `_专题_技能合集策划/` 与 `shared/` 各一份，须保持同步）。

## 三层结构与文件映射

| 层 | 路径 | 角色 |
|---|---|---|
| L1 开发源 | `D:\QoderWork-Files\_项目工作\装配式装修技能开发\_专题_技能合集策划\` | 治理文件开发源；各 `_专题_*` 目录存子技能策划稿 |
| L2 运行时 SOT | `~/.qoderwork/skills/` | standards-index.md（根 SOT，头部含 SOT 声明+镜像说明）+ 各 prefab-*/skill-qa-tester 技能目录 |
| L3 只读镜像 | `~/.qoderwork/skills/shared/` | change-governance、glossary、interface-contracts、platform-adapter-reference、redlines-registry、standards-index（头部为 shared 路径定位措辞） |

特例：**redlines-registry.md 运行时只有 shared/ 镜像一处**（无根副本），LF 换行，同步 = 备份后字节覆盖。

## 同步前检查（必做）

1. 三方逐文件比对（项目仓 ↔ 运行时根 ↔ 镜像），用 `cmp` 或哈希，输出差异清单。
2. 读各冲突文件头部"最后更新"字段定方向：**新的覆盖旧的**，逐文件独立判定（允许不同文件方向不同，glossary 曾出现运行时反向更优的先例）。
3. 方向不明或两侧都有独有改动时，暂停，报告用户裁决，不得猜测合并。

## 标准变更五步同步（standards-index 类）

1. 修源文件（项目仓策划目录）
2. 更新 standards-index（含重编号）——**重编号陷阱：§锚定表行内含 "| 序号 | 编号 |" 子串，须先替换锚定表行、再替换主表行，否则脚本断言冲突**
3. 同步策划表（技能合集策划方案索引等 A0 表）
4. 同步映射文件（reasoning-rules 激活表、技能内序号引用）
5. grep 交叉验证：标准编号/序号全链零残留旧值

## 发布到运行时

- **覆盖前先备份**：`_pre` 后缀（如 v2_1_2_pre）或 `shared/backup_skills_shared_YYYYMMDD/` 目录。
- standards-index 根 ↔ 镜像同步：**头部声明不同**（根含 SOT+镜像说明两行，镜像为 shared 措辞）。字节覆盖后必须恢复各自头部声明，只同步正文。
- redlines-registry：备份 → 字节覆盖 → 确认 LF 换行（CRLF=0）。
- 子技能 SKILL.md 升版：改 frontmatter version + 对应变更说明；技能内容变更须按 change-governance.md 定级走复核。

## 验收清单

1. 三方比对：本次同步范围内所有文件哈希一致（头部声明差异除外，须显式声明）
2. CRLF 检查：同步后的 LF 约定文件 CRLF=0
3. grep 回归：变更涉及的编号/序号/标注（如"待官方核验"）全链零残留旧值
4. change-governance.md 变更日志已登记 CG 编号，项目仓与 shared 镜像两份一致
5. git 提交：项目仓提交，信息含 CG 编号与同步验证结论

## git 提交与推送

- 提交在项目仓 `D:\QoderWork-Files\_项目工作\装配式装修技能开发` 执行，信息格式参照既有提交（CG 编号 + 内容摘要 + 同步验证结论）。
- 推送：`GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c credential.helper=manager push`（读 Windows 凭据管理器）。
- **GitHub 连接 reset 连败 2 次即停**，本地提交安全，改日再推，不得无限重试。

## 红线

- 不得改写历史草稿与过程报告（draft A/B 层、阶段报告、策划方案旧稿）——标注清除只发生在活跃文件。
- 不得跳过备份直接覆盖运行时文件。
- 不得在同步中顺手修改正文内容（发现内容问题 → 走 change-governance.md 变更流程，另立任务）。
- 不得把本技能内容当作治理规则的权威来源；规则冲突时以 change-governance.md 为准。
