# 装配式装修智能体整改 S1 — Pre-flight 预审摘要

**日期**：2026-08-13  
**任务**：按综合评审报告短期建议，补齐 S1 关键缺口，不扩散至 S2/M/L。

---

## 计划预审：PASS（WARN：BK/OR 版本号待确认）

## 任务目标

落实评审报告 3.1 节 5 项短期建议中的 4 项可落地项：

1. BK（prefab-bathroom-kitchen-system）升级到 v2 架构：接入 SRE（IC-10）、引入 P0/P1/P2 分级红线、分离 SKILL.md 与 reference.md。
2. OR（prefab-interior-systems-orchestrator）红线就地定义：在 SKILL.md 内完整定义 P0/P1/P2 红线，消除悬空引用。
3. IC-03 Schema 迁移：从旧版扁平结构改为 ACE-IN/ACE-OUT 嵌套结构，与 IC-08/IC-09 对齐。
4. README / CHANGELOG 数据更新：标准数 59→67，CHANGELOG 补入版本与变更记录。

暂不实施：OR 功能测试（需构造多技能场景，超出 S1 文件治理范围，归入 S2/验收阶段）。

## 交付物

| 序号 | 文件 | 变更内容 |
|------|------|----------|
| 1 | `技能仓备份/prefab-bathroom-kitchen-system/SKILL.md` | 接入 SRE 调用入口、P0/P1/P2 红线、Step 0~5 B2 验证协议 |
| 2 | `技能仓备份/prefab-bathroom-kitchen-system/reference.md` | 新建/重构：知识体系、选型指引、性能指标数据源分级、施工控制点 |
| 3 | `技能仓备份/prefab-interior-systems-orchestrator/SKILL.md` | 新增 OR-R-P0/P1/P2 红线章节，替换现有 4 条行为要点 |
| 4 | `技能仓备份/shared/interface-contracts.md` | IC-03 Schema 改为 ACE-IN/ACE-OUT 嵌套结构 |
| 5 | `README.md` | 标准数量、技能数量等统计更新 |
| 6 | `CHANGELOG.md` | 补入 v1.0.0 之后版本与变更记录 |
| 7 | `shared/change-governance.md` | 追加 S1 变更日志条目（CG-20260813-028 等） |
| 8 | `记录/2026-08-13_装配式装修智能体整改S1_验收报告.md` | 跨文件一致性校验结果 |

## 计划输出路径

- 技能文件：`D:\QoderWork-Files\_项目工作\装配式装修技能开发\技能仓备份\`
- 共享治理文件：`D:\QoderWork-Files\_项目工作\装配式装修技能开发\技能仓备份\shared\`
- 项目根文件：`D:\QoderWork-Files\_项目工作\装配式装修技能开发\`
- 记录文件：`D:\QoderWork-Files\_项目工作\装配式装修技能开发\记录\`

## 验收等级：L2

**定级依据**：

- 修改已有项目真实资产（技能 SKILL.md、共享治理文件、README/CHANGELOG）。
- 影响对象 ≥ 3 个文件/技能。
- 无不可逆操作、无外部系统副作用、无费用/权限/隐私风险。
- 交付物主要为 Markdown 文件，不直接产生可执行脚本，但须通过结构化扫描验证。

## 关键风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| BK 升级中 reference.md 与现有内容不一致 | 数据分级、标准引用失真 | 以原 SKILL.md 内容为准，仅做结构拆分，不改数据口径 |
| IC-03 迁移后 PW SKILL.md 内示例仍用旧字段 | 接口引用脱节 | 同步检索并更新 PW 中 IC-03 示例/引用 |
| OR 红线编号与 redlines-registry 现有编号冲突 | 全局编号漂移 | 先扫描注册表，预留 OR-R-P0-x / OR-R-P1-x / OR-R-P2-x 区间 |
| 版本号/变更日志遗漏 | 治理记录不完整 | 每改一个文件同步追加 CG 条目 |

## 需要用户确认

1. BK 升级是否以 PW（prefab-partition-wall-solution）为模板结构？
2. OR 红线定义后是否同步写入 `shared/redlines-registry.md`？
3. 是否只处理 S1 四项，暂不进入 ST/MI 升级和运行时红线验证？

## 最小成功标准

- BK SKILL.md 出现 `IC-10`、`SRE`、`P0/P1/P2`、`Step 0~5` 关键字，红线编号全局唯一。
- OR SKILL.md 红线章节编号连续、触发后标准应对完整。
- IC-03 Schema 与 IC-08/IC-09 结构一致，字段命名无歧义。
- README 标准数为 67，CHANGELOG 包含 2026-08 版本记录。
- `shared/change-governance.md` 追加对应 CG 条目。

## 最小闭环

读取目标文件 → 结构化修改 → 本地回读/关键词扫描 → 更新变更日志 → 输出验收报告。

## 中止或纠偏触发条件

- 发现红线编号与 `redlines-registry.md` 冲突且无法预留新号。
- IC-03 Schema 验证与 IC-08/IC-09 字段不一致且两次修正未收敛。
- 用户明确要求扩大范围至 ST/MI 升级（需重新 Pre-flight）。
- 连续两次同类扫描异常（如版本号、编号、数据源分级）。
