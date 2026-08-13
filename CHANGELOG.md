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

## v1.2.2 — 2026-08-13

SRE 引擎化第一阶段：将声明式标准推理规则升级为可执行规则包 + 推理器 + 证据对象 + 决策轨迹 + 回归测试集，并完成 IC-10 契约升级与 SRE 红线注册。

- `shared/standards-reasoning-rules.md` 升级至 v1.2：新增§七结构化规则包与引擎化规范，定义规则包组成、推理器接口、证据对象、决策轨迹、成熟度分级与 IC-10 同步要求
- `shared/interface-contracts.md` IC-10 升级至 v1.5.8：响应新增 `证据对象` 与 `决策轨迹`，请求新增 `return_trace`，同步更新 JSON Schema 与字段约束表
- `shared/redlines-registry.md` 注册 SRE 专属红线 3 条（SR-R-P1-5 / P1-6 / P2-3），SR 红线总数 8→11，全合集红线总数 130→133
- `prefab-standards-reviewer` 升级至 v2.1.0：内置 `sre_reasoner.py` 参考推理器与 `sre_regression_test.py` 回归测试集（23 用例全绿），SKILL.md 更新成熟度声明与平台动作建议
- 四层镜像同步：L1 开发源 ↔ 技能仓备份 ↔ QoderWork 运行时 ↔ WorkBuddy 运行时保持一致
- 新增治理记录 CG-20260813-035

## v1.2.1 — 2026-08-13

S2 运行时契约锚定补丁：在 OR/ST/WS 三个消费端 SKILL.md 路由表中显式标注 IC-02/IC-06/IC-05，消除 interface-contracts v1.5.7 与运行时之间的引用漂移。

- `prefab-interior-systems-orchestrator` v2.1.0 → v2.1.1：兜底 ME 路由标注 IC-02
- `prefab-storage-system` v2.1.0 → v2.1.1：§7 跨技能路由新增 IC-06 入墙式/壁挂柜体对隔墙承载力、厚度要求路由
- `prefab-wall-surface-system` v2.1.3 → v2.1.4：§11 PW 路由标注 IC-05
- 新增治理记录 CG-20260813-033

