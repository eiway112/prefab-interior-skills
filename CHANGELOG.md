# 变更日志

合集整体版本记录。格式：语义化版本 MAJOR.MINOR.PATCH；标签与条目一一对应。

## v1.0.0 — 2026-08-07

首个公开发布基线。

- 16 个技能 + 治理文件（标准索引 59 条、接口契约 v1.5.5、红线注册表、术语表、变更治理）对外发布，引用入口为 `技能仓备份/`
- 新增 README（引用指南、安装方法、版本迭代策略、免责声明）
- 新增 MIT License
- 仓库改名 `prefab-interior-skills` 并转为公开仓库

## v1.1.0 — 2026-08-13

S1 短期整改基线：补齐关键缺口，消除信息漂移。

- `prefab-bathroom-kitchen-system` 升级至 v2.1.0：引入 v2 认知模型、B2 验证协议、IC-10/SRE 接线、P0/P1/P2 分级红线 14 条，技术内容与 PW/CL/FL/WS 对齐
- `prefab-interior-systems-orchestrator` 红线就地定义：在 SKILL.md 内完整列出 OR-R-P0-1 ~ OR-R-P1-3 共 8 条红线及冲突仲裁规则，消除对外部注册表的悬空依赖
- `shared/redlines-registry.md` 同步注册 BK 14 条红线，全合集红线总数升至 104 条，已注册技能增至 9/14
- 复核并确认 `shared/interface-contracts.md` 中 IC-03（PW→ACE 空气声隔声）已迁移至 ACE-IN/ACE-OUT 嵌套结构，与 IC-08/IC-09 顶层 required 对齐
- README 与 CHANGELOG 数据更新：标准索引数量修正为 67 条，补充 v1.1.0 版本记录

## v1.2.0 — 2026-08-13

S2 第二梯队基线：补齐 ST/MI v2 架构与全局红线注册，修复 L1 开发源漂移。

- `prefab-storage-system` 升级至 v2.1.0：补齐 `examples.md` 与 `product-solutions.md`，SKILL.md 插入多文件协同架构章节，注册 ST-R-P0/P1/P2 共 14 条红线
- `prefab-mep-integration-system` 升级至 v2.1.0：补齐 `examples.md` 与 `product-solutions.md`，SKILL.md 插入多文件协同架构章节，注册 MI-R-P0/P1/P2 共 12 条红线
- `shared/redlines-registry.md` 全局红线注册表更新：红线总数 104→130 条，已注册技能 9→11 个
- 修复 L1 开发源漂移：`_专题_技能合集策划_/redlines-registry.md` 同步至 130 条版本，L1/shared/运行时/WorkBuddy 四层一致
- 新增治理记录 CG-20260813-032

## v1.2.1 — 2026-08-13

S2 运行时契约锚定补丁：在 OR/ST/WS 三个消费端 SKILL.md 路由表中显式标注 IC-02/IC-06/IC-05，消除 interface-contracts v1.5.7 与运行时之间的引用漂移。

- `prefab-interior-systems-orchestrator` v2.1.0 → v2.1.1：兜底 ME 路由标注 IC-02
- `prefab-storage-system` v2.1.0 → v2.1.1：§7 跨技能路由新增 IC-06 入墙式/壁挂柜体对隔墙承载力、厚度要求路由
- `prefab-wall-surface-system` v2.1.3 → v2.1.4：§11 PW 路由标注 IC-05
- 新增治理记录 CG-20260813-033

## v1.2.2 — 2026-08-13

SRE 引擎化第一阶段：将声明式标准推理规则升级为可执行规则包 + 推理器 + 证据对象 + 决策轨迹 + 回归测试集，并完成 IC-10 契约升级与 SRE 红线注册。

- `shared/standards-reasoning-rules.md` 升级至 v1.2：新增§七结构化规则包与引擎化规范，定义规则包组成、推理器接口、证据对象、决策轨迹、成熟度分级与 IC-10 同步要求
- `shared/interface-contracts.md` IC-10 升级至 v1.5.8：响应新增 `证据对象` 与 `决策轨迹`，请求新增 `return_trace`，同步更新 JSON Schema 与字段约束表
- `shared/redlines-registry.md` 注册 SRE 专属红线 3 条（SR-R-P1-5 / P1-6 / P2-3），SR 红线总数 8→11，全合集红线总数 130→133
- `prefab-standards-reviewer` 升级至 v2.1.0：内置 `sre_reasoner.py` 参考推理器与 `sre_regression_test.py` 回归测试集（23 用例全绿），SKILL.md 更新成熟度声明与平台动作建议
- 四层镜像同步：L1 开发源 ↔ 技能仓备份 ↔ QoderWork 运行时 ↔ WorkBuddy 运行时保持一致
- 新增治理记录 CG-20260813-035

## v1.3.0 — 2026-08-13

SSCV 标准条文核验治理补齐（事项 8 P0）：为扫描版/文本版标准核验流水线补齐红线、接口契约、环境依赖与输出物路由四项治理要素，并修复多处遗留漂移。

- `shared/redlines-registry.md` 注册 SSCV 标识与 10 条红线（P0×3 核验诚信 + P1×4 核验方法 + P2×3 记录流程），新增§十五 SSCV 章节；全合集红线总数 133→143，已注册技能 11→12（15 标识）；同步修复 SRE 轮次遗留的头部统计漂移（SR 误记 8 条，实际 11 条）
- `shared/interface-contracts.md` 升级至 v1.6.0：新增 IC-11（标准复核工具/任何技能 → 标准条文核验流水线）契约，含最小参数集、字段约束表（请求 4 项 + 响应 5 项）与 IC-11-Request JSON Schema；§五总览/标识映射、§6.1 降级策略同步登记；附带修复 IC-10-Request Schema description 未转义双引号导致的非法 JSON
- `scanned-standard-clause-verify` 升级至 v1.1.0：新增 IC-11 接收方接口契约、红线约束（10 条摘要表）、环境依赖声明、输出物路由四节
- 新建输出物路由目录 `成果/标准核验/`（含 README 命名规则与报告内容要求）
- `程序文件/validate_governance.py` 修复：章节号正则补"一/二"（修正 CL/BK 章节配对错位）、契约校验范围扩至 IC-11；修复后全量校验 143 通过 / 0 失败
- `文档/项目策划方案索引.md` 漂移修复：红线 90→143、已注册技能 8→12、契约 v1.5.6→v1.6.0、SRE v1.1→v1.2
- 四层镜像同步：L1 开发源 ↔ 技能仓备份 ↔ QoderWork 运行时 ↔ WorkBuddy 运行时保持一致
- 新增治理记录 CG-20260813-036

## v1.4.0 — 2026-08-13

QA/GS/ACG 契约化与红线注册（事项 9 P1）：为质量测试、治理同步、验收清单三个工具类技能补齐红线注册与接口契约，完成第三梯队契约形式化收尾。

- `shared/redlines-registry.md` 注册 AC（验收清单）红线 12 条（P0×4 + P1×4 + P2×4，全量继承技能本地既有分级）与 GS（治理同步）标识及红线 9 条（P0×2 + P1×4 + P2×3），新增§十六/§十七章节；全合集红线总数 143→164，已注册技能 12→14（16 标识）
- `shared/interface-contracts.md` 升级至 v1.7.0：新增 IC-12（任何技能 → QA 测试工具）、IC-13（任何技能 → GS 治理同步工具）、IC-14（总入口 → 验收清单技能）三条契约，各含最小参数集、字段约束表与 Request JSON Schema；§五总览/标识映射、§6.1 降级策略、§八注册状态同步登记；附带修复 IC-07 source_skill 枚举遗漏 SSCV/GS 等三处漂移
- `skill-qa-tester` 升级至 v1.1.0：新增 IC-12 接收方契约、红线约束（6 条摘要表）、测试包模板、与 GS/SSCV 触发关系四节
- `prefab-governance-sync` 升级至 v1.1.0：红线节替换为 9 条全局编号摘要表，新增 IC-13 接收方契约节与脚本化同步流程节
- `prefab-acceptance-checklist-generator` 升级至 v2.1.0：§4 红线加 AC-R 全局编号，文末新增 §9 接口契约（IC-14 接收方）
- `程序文件/validate_governance.py` 升级 v1.4：契约 Schema 校验范围扩至 12 条（新增 IC-12/IC-13/IC-14）
- 四层镜像同步：L1 开发源 ↔ 技能仓备份 ↔ QoderWork 运行时 ↔ WorkBuddy 运行时保持一致
- 新增治理记录 CG-20260813-037

