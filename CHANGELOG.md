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

