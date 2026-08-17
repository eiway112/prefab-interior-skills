# 变更日志

合集整体版本记录。格式：语义化版本 MAJOR.MINOR.PATCH；标签与条目一一对应。

## v1.8.0 — 2026-08-17

技能定义骨架增强首批（CG-20260817-001/002）：补齐"工作流"与"量化成功指标"两个结构块，门禁从"防乱来"扩展到"防空转、防无限打磨"。

- 新增 `_专题_技能合集策划/技能定义骨架规范.md` v1.0：八块骨架定义、块分离原则、工作流块与成功指标块编写要求（含期望校准必备条款与高风险领域指标锚定护栏）；来源为 The Agency 对标分析结论的去环境依赖改编
- `prefab-partition-wall-solution` v2.0.3→v2.1.0（试点）：新增「工作流」块（需求确认→标准推理→验证执行→输出复核，阶段放行条件=证据产物存在）与「成功指标（量化）」块（清单覆盖率/引用合规/数据来源标注/红线处理四条可证伪验收线 + 期望校准）
- `prefab-interior-systems-orchestrator` v2.1.1→v2.2.0：多部品协同新增「阶段证据放行条件」小节与整改循环期望校准条款
- 方法论、红线体系、接口接线零变更（只增不改断言验证通过），reviewer 复核 PASS

## v1.7.0 — 2026-08-14

WF 外部技能迁出至独立项目（CG-20260814-003），治理文档 WF 引用清理。

- `waterproofing-expert` 整目录迁出至独立项目 `D:\QoderWork-Files\_项目工作\建筑专业辅材技能合集\`
- `shared/redlines-registry.md` 移除 WF 标识映射行、标识分配说明 WF 条款、§20.2 待注册行；已注册技能 15/16→15/15（合集内全部已注册）；红线总数 178 不变
- `shared/interface-contracts.md` 移除 WF 标识映射行、BK→WF 路由、低优先级表厨卫→外部防水条目、source_skill 枚举中 WF
- `程序文件/sync_skill_backup.py` SKILL_DIRS 移除 waterproofing-expert
- QoderWork/WorkBuddy 运行时移除 waterproofing-expert 安装
- 合集内技能从 16 个调整为 15 个（WF 不再属于本合集）

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

## v1.5.0 — 2026-08-13

SR IC-07 闭环（第三梯队备忘录 §5.2 唯一剩余 P1）：为标准复核技能补齐接收方契约锚定、红线全局编号化、分层标注与 QA 基线，附办观察项 CG-20260807-019 文义矛盾修复。

- `prefab-standards-reviewer` 升级至 v2.2.0：新增多文件认知架构表（A-D 分层）、IC-07/IC-10 接收方接口契约节（请求 4 必填字段、响应枚举、缺参降级），原 5 条本地红线重构为 14 条全局编号摘要表并附历史映射
- `shared/redlines-registry.md` SR 补注册 3 条（SR-R-P0-3 超越专业边界 / SR-R-P1-7 臆造条款号 / SR-R-P2-4 推荐品牌，均按合集同族先例定级），SR 红线 11→14 条，全合集红线总数 164→167（P0 51 / P1 71 / P2 45）
- `shared/standards-reasoning-rules.md` 升级至 v1.2.1：修复头部"不低于 A 级"与 §4.5 七类变更分级的文义矛盾（观察项 CG-20260807-019 闭环），改为按类别定级表述，推理逻辑零变更
- 新建 QA 基线 `sr_ic07_compliance_test.py`（20 例 5 组，TestDocAnchor 三向比对，首跑 20/20 PASS）；sre_regression_test.py 复跑 23/23 PASS
- 四层镜像同步：治理 3 文件 + SR 2 文件，L1 ↔ 技能仓备份 ↔ QoderWork 运行时 ↔ WorkBuddy 运行时哈希一致、CRLF=0
- 新增治理记录 CG-20260813-038

## v1.5.1 — 2026-08-14

ME 通用专家红线注册（CG-20260814-001）：为唯一未注册直面用户技能补齐红线全局编号与分级体系。

- `shared/redlines-registry.md` 注册 ME 红线 10 条（P0×2 超越专业边界/隐瞒不确定性 + P1×5 混用产品标准/伪装数据来源/忽略标准替代/跳过标准复核路由/咨询意见不得等同检测报告 + P2×3 地方标准差异须标注/数据分级标注/产品时效标注），新增§十八 ME 章节；全合集红线总数 167→177（P0 53 / P1 76 / P2 48），已注册技能 14→15（16 标识）；§十八→§十九 至 §二十一→§二十二 顺延
- `prefab-interior-materials-expert` 升级至 v2.0.1：原§六 7 条无分级禁止行为红线重构为 P0/P1/P2 分级体系（10 条全局编号 + 冲突仲裁规则 + 跨技能协同规则 + 本地红线来源追溯映射）
- 四层镜像同步：L1 开发源 ↔ 技能仓备份 ↔ QoderWork 运行时 ↔ WorkBuddy 运行时哈希一致、CRLF=0
- 新增治理记录 CG-20260814-001

## v1.6.0 — 2026-08-14

ACG IC-10/SRE 标准推理引擎接线（CG-20260814-002）：验收清单技能 Step 2 从静态查表升级为场景推理，合集内全部 16 个技能的治理链路完整。

- `prefab-acceptance-checklist-generator` 升级至 v2.2.0：Step 2 接入 IC-10（标准推理引擎）动态获取适用标准集；新增§10 多文件认知架构（A/B/C/D 四层映射）；新增§11 IC-10 集成调用（调用时机、响应使用、SRE 降级策略、与 IC-07 分工）；§7 跨技能路由表增 IC-10/SRE 行
- `shared/redlines-registry.md` 注册 AC-R-P1-5"严禁跳过 SRE 标准推理"（同族先例 PW-R-P1-9/FL-R-P1-1/WS-R-P1-5/CL-R-P1-5/BK-R-P1-5），AC 红线 12→13 条，全合集红线总数 177→178（P0 53 / P1 77 / P2 48）
- 四层镜像同步：L1 开发源 ↔ 技能仓备份 ↔ QoderWork 运行时 ↔ WorkBuddy 运行时哈希一致、CRLF=0
- 新增治理记录 CG-20260814-002
