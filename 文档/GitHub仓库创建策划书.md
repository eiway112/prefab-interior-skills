# GitHub 仓库创建与管理策划书

> 适用项目：装配式装修智能体合集 & 建筑装饰装修辅材智能体合集
> 编制日期：2026年6月

---

## 一、仓库规划原则与命名规范

### 1.1 规划原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个仓库对应一个独立的知识域或工具系统，便于版本管理和权限控制 |
| **模块化设计** | 按部品系统或功能维度拆分仓库，支持独立迭代和组合使用 |
| **渐进式建设** | 优先创建核心入口仓库，后续按需扩展专项仓库 |
| **私有优先** | 涉及核心知识库、算法逻辑、商业数据的仓库一律设为 Private |

### 1.2 命名规范

采用 **kebab-case（小写字母+连字符）** 格式，遵循"领域-功能"的命名模式：

```
[领域前缀]-[功能描述]
```

**领域前缀定义**：

| 前缀 | 对应领域 |
|------|---------|
| `prefab-` | 装配式装修（prefabricated interior） |
| `decoration-` | 装饰装修辅材 |

### 1.3 推荐仓库清单

#### 装配式装修智能体合集

| 仓库名称 | 用途 | 优先级 |
|---------|------|--------|
| `prefab-interior-systems-orchestrator` | 合集总入口与任务路由 | P0（最高） |
| `prefab-interior-materials-expert` | 综合专家子技能（材料、工艺、质量、选型兜底分析） | P0 |
| `prefab-partition-wall-solution` | 隔墙方案专项 | P1 |
| `prefab-ceiling-system` | 吊顶系统专项 | P1 |
| `prefab-floor-system` | 楼地面系统专项 | P1 |
| `prefab-bathroom-kitchen-system` | 厨卫系统专项 | P1 |
| `prefab-storage-system` | 收纳系统专项 | P2 |
| `prefab-mep-integration-system` | 机电集成专项 | P2 |
| `prefab-acceptance-checklist-generator` | 验收清单生成器 | P2 |
| `prefab-standards-reviewer` | 标准复核专项 | P1 |
| `prefab-standards-index` | 合集级标准版本索引 | P0 |

#### 建筑装饰装修辅材智能体合集

| 仓库名称 | 用途 | 优先级 |
|---------|------|--------|
| `decoration-auxiliary-orchestrator` | 辅材合集总入口 | P0 |
| `waterproofing-expert` | 防水专项 | P1 |
| `decoration-adhesive-sealant` | 胶粘剂与密封胶专项 | P1 |
| `decoration-fastener-hardware` | 紧固件与五金件专项 | P1 |
| `decoration-coating-paint` | 涂料与饰面专项 | P2 |
| `decoration-waterproof-materials` | 防水材料专项 | P1 |
| `decoration-insulation-materials` | 保温隔热材料专项 | P2 |
| `decoration-auxiliary-standards-index` | 辅材合集标准索引 | P0 |

### 1.4 仓库类型选择

| 仓库类型 | 适用场景 |
|---------|---------|
| **Private** | 所有智能体知识库、核心算法、商业数据 |
| **Public**（可选） | 开源工具脚本、通用模板、行业知识科普（后期考虑） |

---

## 二、权限配置最佳实践

### 2.1 Personal Access Token（PAT）权限选择

基于"私人仓库 + 团队协作"场景，推荐以下权限配置：

#### 必须勾选（核心权限）

| 权限项 | 勾选方式 | 用途 |
|--------|---------|------|
| **repo** | 勾选整个 `repo` 类别 | 私有仓库的克隆、推送、拉取、管理（含所有子项：仓库状态、仓库部署、公共仓库、仓库邀请、安全事件） |
| **workflow** | 勾选 | 管理 GitHub Actions，支持 CI/CD 自动化 |

#### 建议勾选（扩展权限）

| 权限项 | 勾选方式 | 用途 |
|--------|---------|------|
| **write:packages** + **read:packages** | 两者都勾选 | 发布和拉取 GitHub Packages（如 npm 包、Docker 镜像） |
| **delete_repo** | 勾选 | 后期清理废弃仓库 |
| **codespaces** | 勾选 | 使用 GitHub Codespaces 在线开发 |
| **project** → **read:project** | 勾选子项 | 查看 GitHub Projects 看板，管理任务 |

#### 按需勾选

| 权限项 | 勾选条件 | 用途 |
|--------|---------|------|
| **admin:public_key** → write + read | 计划使用 SSH 方式操作仓库时 | 管理 SSH 公钥 |
| **admin:gpg_key** → write + read | 计划启用提交签名验证时 | 管理 GPG 签名密钥 |
| **admin:ssh_signing_key** → write + read | 计划使用 SSH 签名提交时 | 管理 SSH 签名密钥 |

#### 不建议勾选

| 权限项 | 理由 |
|--------|------|
| `admin:enterprise` 及所有子项 | 企业版功能，个人账号不需要 |
| `admin:org_hook` | 组织级 Webhook 管理，个人使用不需要 |
| `gist` | 代码片段分享，与仓库管理无关 |
| `notifications` | 通知读取，非必需 |
| `admin:org` | 组织管理，除非在组织下管理仓库 |
| `manage_runners:enterprise` | 企业级 Runner 管理 |
| `scim:enterprise` | 企业 SSO 用户同步 |
| `audit-log` | 个人使用场景下不需要 |

### 2.2 Token 有效期设置

| 场景 | 建议有效期 | 理由 |
|------|-----------|------|
| 日常开发 | **90 天** | 平衡安全性与便利性 |
| CI/CD 集成 | **无过期（No expiration）** | 避免自动化流程中断，但需加强保管 |
| 临时调试 | **30 天** | 短期使用，过期自动失效 |

### 2.3 权限最小化原则

1. **按需授权**：仅勾选当前实际需要的权限，后续需要时可重新生成
2. **分级管理**：不同用途创建不同 Token（如"日常开发"和"CI/CD"分开）
3. **及时回收**：不再使用的 Token 立即在 GitHub 中删除
4. **定期轮换**：即使 Token 未过期，建议每 90 天轮换一次

---

## 三、安全令牌（PAT）创建与管理流程

### 3.1 创建流程（分步操作）

#### 第一步：进入 PAT 创建页面

1. 登录 GitHub → 点击右上角头像 → **Settings**
2. 左侧菜单滚动到最底部 → **Developer settings**
3. 左侧菜单 → **Personal access tokens** → **Tokens (classic)**
4. 点击 **Generate new token** → **Generate new token (classic)**

#### 第二步：配置 Token 基本信息

| 配置项 | 建议值 | 说明 |
|--------|--------|------|
| **Note**（令牌名称） | `Qoder - 装配式装修智能体` | 清晰描述用途，便于后续管理 |
| **Expiration**（有效期） | `90 days` | 日常开发推荐 |

#### 第三步：勾选权限范围

按照本文"第二章 权限配置最佳实践"中的表格逐项勾选。

#### 第四步：生成并保存 Token

1. 滚动到页面底部，点击绿色 **Generate token** 按钮
2. **立即复制**生成的 Token（以 `ghp_` 开头的字符串）
3. 将 Token 保存到安全位置（推荐方式见下方）

> **警告**：Token 只显示一次！关闭或刷新页面后将无法再次查看。如果忘记复制，只能删除重新生成。

#### 第五步：验证 Token 是否生效

在终端中执行：

```bash
git clone https://<GitHub用户名>:<Token>@github.com/<用户名>/<仓库名>.git
```

如能成功克隆，说明 Token 配置正确。

### 3.2 Token 安全存储

| 存储方式 | 安全性 | 推荐度 |
|---------|--------|--------|
| **Git Credential Manager** | 高（系统级加密存储） | 推荐 |
| **环境变量** | 中（仅限本地开发） | 可用 |
| **密码管理器**（如 Bitwarden） | 高 | 推荐 |
| **明文文件** | 低 | 不推荐 |
| **聊天工具/邮件** | 极低 | 禁止 |

**配置 Git Credential Manager（推荐）**：

```bash
# 启用凭证管理器（Windows 系统自带）
git config --global credential.helper manager
```

配置后，首次克隆/推送时输入用户名和 Token，后续自动使用缓存凭证。

### 3.3 Token 管理清单

建议维护一份 Token 管理记录（存放在密码管理器中）：

| 字段 | 示例值 |
|------|--------|
| 名称 | Qoder - 装配式装修智能体 |
| 前缀 | ghp_xxxx...xxxx |
| 创建日期 | 2026-06-06 |
| 过期日期 | 2026-09-04 |
| 权限范围 | repo, workflow, read:packages, write:packages |
| 状态 | 使用中 / 已过期 / 已撤销 |
| 用途说明 | 用于 Qoder 克隆和管理装配式装修智能体仓库 |

### 3.4 Token 轮换流程

1. 在 GitHub 创建新 Token（相同权限配置）
2. 更新本地 Git 凭证（删除旧凭证 → 使用新 Token）
3. 更新 CI/CD 中的 Secret（如有）
4. 在 GitHub 删除旧 Token
5. 验证新 Token 正常工作

**清除旧凭证命令（Windows）**：

```powershell
# 删除 Windows 凭证管理器中的 GitHub 凭证
cmdkey /delete:git:https://github.com
```

---

## 四、仓库初始化配置

### 4.1 创建仓库（网页端操作）

1. GitHub 首页 → 右上角 **+** → **New repository**
2. 填写配置：

| 配置项 | 值 |
|--------|-----|
| **Repository name** | 按命名规范填写（合集总入口用 `prefab-interior-systems-orchestrator`，综合专家子技能用 `prefab-interior-materials-expert`） |
| **Description** | 装配式装修专家 — 材料、工艺、质量与选型综合专家子技能 |
| **Public / Private** | **Private** |
| **Add a README file** | 勾选 |
| **Add .gitignore** | 暂不勾选（手动创建） |
| **Choose a license** | 暂不勾选（私有仓库可选） |

3. 点击 **Create repository**

### 4.2 README.md 模板

```markdown
# 装配式装修专家（prefab-interior-materials-expert）

> 装配式装修智能体合集 — 综合专家子技能

## 概述

以装配式装修产业化为导向，整合规范标准、产品技术、工艺工法及工程案例，
形成覆盖"设计选型—生产制作—现场施工—质量验收"全链路的知识体系，
为行业专业人员提供专业、精准、可落地的技术解决方案。

本技能不作为合集总入口。跨部品系统任务、技能导航和任务拆解应先进入
`prefab-interior-systems-orchestrator`，再按问题归属路由到本技能或其他专项技能。

## 能力范围

- 规范标准查询与解读
- 产品技术咨询与选型对比
- 工艺方案编制
- 质量问题诊断
- 材料选型推荐
- 行业趋势分析

## 覆盖部品系统

隔墙 | 吊顶 | 楼地面 | 墙面 | 厨房 | 卫浴 | 收纳 | 门窗套 | 管线集成

## 技术栈

- Qoder Agent Skill
- Markdown 知识库
- 标准规范索引系统

## 合集结构

本技能属于 **装配式装修智能体合集**，合集内各专项技能见：
- [合集总入口](../prefab-interior-systems-orchestrator)
- [隔墙方案专项](../prefab-partition-wall-solution)
- [标准复核专项](../prefab-standards-reviewer)

## 维护者

装配式装修智能体团队
```

### 4.3 .gitignore 模板

```gitignore
# ===== 操作系统文件 =====
.DS_Store
Thumbs.db
Desktop.ini
ehthumbs.db

# ===== IDE 与编辑器 =====
.vscode/
.idea/
*.swp
*.swo
*~

# ===== Qoder 相关 =====
.qoder/
.qoderwork/

# ===== Node.js（如有） =====
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# ===== 环境变量 =====
.env
.env.local
.env.*.local

# ===== 构建产物 =====
dist/
build/
.next/
out/

# ===== 日志 =====
*.log
logs/

# ===== 临时文件 =====
*.tmp
*.bak
*.cache
.cache/

# ===== 数据库文件（不纳入版本控制） =====
*.db
*.sqlite
*.sqlite3
prisma/dev.db
```

### 4.4 许可证选择（私有仓库可选）

| 场景 | 建议 |
|------|------|
| 纯私有商业项目 | 不添加许可证（默认"所有权利保留"） |
| 未来可能开源 | MIT License（宽松）或 Apache 2.0 |
| 希望开源但保护专利 | Apache 2.0 |

### 4.5 分支策略

```
main          ← 稳定版本（生产环境使用的知识版本）
  └── develop ← 日常开发与知识更新
       └── feature/xxx ← 新功能或新知识模块开发
```

**分支保护规则（Settings → Branches）**：

| 规则 | 配置 |
|------|------|
| 保护 `main` 分支 | 禁止直接推送，需通过 Pull Request |
| 要求 Code Review | 至少 1 人审核（个人账号可跳过） |
| 要求 CI 通过 | 如有自动化检查，需通过后才能合并 |

---

## 五、仓库架构设计建议

### 5.1 装配式装修智能体 — 仓库架构

#### 合集总入口（prefab-interior-systems-orchestrator）

```
prefab-interior-systems-orchestrator/
├── .qoder/skills/prefab-interior-systems-orchestrator/
│   ├── SKILL.md                  # 合集路由与任务分派技能定义
│   ├── examples.md               # 跨系统协作示例
│   └── reference.md              # 合集级参考文档
├── standards-index.md            # 合集级标准版本索引（统一入口）
├── README.md
├── .gitignore
└── CHANGELOG.md                  # 版本变更记录
```

#### 综合专家子技能（prefab-interior-materials-expert）— 当前已有

```
prefab-interior-materials-expert/
├── .qoder/skills/prefab-interior-materials-expert/
│   ├── SKILL.md                  # 综合专家技能定义（角色、能力、原则、模板）
│   ├── examples.md               # 四类输出示例（规范/产品/工艺/诊断）
│   └── reference.md              # 详细参考（知识域、能力矩阵、标准体系）
├── knowledge/                    # 知识库文档
│   ├── standards/                # 标准规范摘要与解读
│   ├── products/                 # 产品技术资料
│   ├── processes/                # 工艺工法文档
│   └── cases/                    # 工程案例分析
├── README.md
├── .gitignore
└── CHANGELOG.md
```

#### 专项技能（以隔墙方案专项为例）

```
prefab-partition-wall-solution/
├── .qoder/skills/prefab-partition-wall-solution/
│   ├── SKILL.md                  # 隔墙专项技能定义
│   ├── examples.md               # 隔墙方案输出示例
│   └── reference.md              # 隔墙系统详细参考
├── knowledge/
│   ├── wall-types/               # 隔墙类型（条板/龙骨/模块）
│   ├── acoustic-design/          # 隔声设计
│   ├── fire-resistance/          # 耐火设计
│   └── installation/             # 安装工艺
├── templates/                    # 方案模板
├── README.md
├── .gitignore
└── CHANGELOG.md
```

### 5.2 建筑装饰装修辅材智能体 — 仓库架构

#### 辅材合集总入口（decoration-auxiliary-orchestrator）

```
decoration-auxiliary-orchestrator/
├── .qoder/skills/decoration-auxiliary-orchestrator/
│   ├── SKILL.md                  # 辅材合集路由与任务分派
│   ├── examples.md               # 辅材选型输出示例
│   └── reference.md              # 辅材知识体系参考
├── standards-index.md            # 辅材合集标准索引
├── knowledge/
│   ├── categories/               # 辅材分类体系
│   │   ├── adhesives.md          # 胶粘剂
│   │   ├── sealants.md           # 密封胶
│   │   ├── fasteners.md          # 紧固件
│   │   ├── coatings.md           # 涂料
│   │   └── insulation.md         # 保温材料
│   ├── brands/                   # 品牌技术路线对比（不含推荐）
│   └── compatibility/            # 材料相容性矩阵
├── calculators/                  # 用量计算模板
├── README.md
├── .gitignore
└── CHANGELOG.md
```

#### 胶粘剂与密封胶专项（decoration-adhesive-sealant）

```
decoration-adhesive-sealant/
├── .qoder/skills/decoration-adhesive-sealant/
│   ├── SKILL.md                  # 胶粘剂/密封胶专项技能定义
│   ├── examples.md               # 选型与诊断示例
│   └── reference.md              # 详细技术参考
├── knowledge/
│   ├── tile-adhesive/            # 瓷砖胶（C1/C2/C2TES1）
│   ├── structural-adhesive/      # 结构胶
│   ├── silicone-sealant/         # 硅酮密封胶
│   ├── polyurethane-sealant/     # 聚氨酯密封胶
│   └── ms-polymer-sealant/       # MS聚合物密封胶
├── standards/                    # 相关标准摘要
│   ├── JC-T-547.md              # 陶瓷砖胶粘剂
│   ├── GB-T-14683.md            # 硅酮和改性硅酮建筑密封胶
│   └── JC-T-881.md              # 混凝土建筑接缝用密封胶
├── README.md
├── .gitignore
└── CHANGELOG.md
```

### 5.3 共享标准索引仓库

```
prefab-standards-index/
├── standards-index.md            # 统一标准版本索引（所有合集共享）
├── changelog.md                  # 标准更新动态
├── deprecated.md                 # 已废止标准记录
├── README.md
└── .gitignore
```

> 各合集仓库中的 `standards-index.md` 应引用此共享仓库的数据，避免重复维护。

### 5.4 仓库间关系图

```
                    ┌─────────────────────────────────┐
                    │  prefab-standards-index          │
                    │  （共享标准索引）                   │
                    └──────────┬──────────────────────┘
                               │ 引用
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼─────────┐ ┌───────▼────────┐ ┌────────▼────────┐
│ prefab-interior-  │ │ decoration-    │ │  （未来扩展）    │
│ systems-          │ │ auxiliary-     │ │                 │
│ orchestrator      │ │ orchestrator   │ │                 │
│ （装配式总入口）    │ │ （辅材总入口）   │ │                 │
└─────────┬─────────┘ └───────┬────────┘ └─────────────────┘
          │                    │
    ┌─────┼─────┐        ┌────┼────┐
    │     │     │        │    │    │
   隔墙  吊顶  地面    胶粘  紧固  涂料
   专项  专项  专项    专项  专项  专项
   ...   ...   ...    ...   ...   ...
```

---

## 六、后续维护与协作工作流程

### 6.1 日常开发工作流

```
1. 拉取最新代码
   git checkout develop
   git pull origin develop

2. 创建功能分支
   git checkout -b feature/新增隔墙知识模块

3. 编辑知识文件并提交
   git add .
   git commit -m "feat: 新增一体化双空腔轻钢龙骨隔墙施工工艺"

4. 推送到远程
   git push origin feature/新增隔墙知识模块

5. 在 GitHub 创建 Pull Request → 合并到 develop

6. 稳定后合并到 main
   git checkout main
   git merge develop
   git push origin main
```

### 6.2 知识更新流程

| 触发条件 | 操作 | 责任人 |
|---------|------|--------|
| 新标准发布 | 更新 `standards-index.md`，通知相关专项仓库 | 标准管理员 |
| 标准废止/替代 | 更新索引 + 检查所有引用处 + 添加替代说明 | 标准管理员 |
| 用户反馈错误 | 执行 SKILL.md 中的"用户反馈纠正流程" | 技能维护者 |
| 新工艺/新产品 | 在对应专项仓库新增知识文件 | 内容编辑 |
| 季度审查 | 全面核查标准时效性、市场数据时效性 | 技能维护者 |

### 6.3 Commit 消息规范

采用 **Conventional Commits** 格式：

```
<类型>: <简要描述>

[可选的详细说明]
```

**类型定义**：

| 类型 | 用途 | 示例 |
|------|------|------|
| `feat` | 新增知识内容/功能 | `feat: 新增GB 55038-2025住宅项目规范解读` |
| `fix` | 修正错误内容 | `fix: 修正JC/T 547-2017瓷砖胶等级描述错误` |
| `update` | 更新现有内容 | `update: 更新2026年SPC地板市场价格区间` |
| `docs` | 文档结构调整 | `docs: 重构隔墙系统知识目录` |
| `refactor` | 重构/优化 | `refactor: 优化标准引用准确性保障体系` |
| `chore` | 维护性工作 | `chore: 更新.gitignore` |
| `deprecate` | 标记过时内容 | `deprecate: 标记GB 18580-2017为已替代` |

### 6.4 版本发布管理

使用 **GitHub Releases** 管理知识版本：

| 版本类型 | 格式 | 示例 |
|---------|------|------|
| 重大更新（新增部品系统） | vX.0.0 | v2.0.0 |
| 知识内容更新 | v0.X.0 | v1.3.0 |
| 修正/小幅更新 | v0.0.X | v1.2.1 |

### 6.5 协作模式（后期扩展）

#### 角色与权限分配

| 角色 | 仓库权限 | 职责 |
|------|---------|------|
| **Owner** | 全部权限 | 仓库管理、权限分配、最终审核 |
| **Writer** | 读写权限 | 知识编辑、代码提交、创建 PR |
| **Reader** | 只读权限 | 查阅知识库、提出 Issue |

#### 协作流程

1. **Issue 驱动**：所有知识更新需求先创建 Issue 描述
2. **分支开发**：基于 Issue 创建功能分支
3. **PR 审核**：提交 Pull Request，至少一人审核后合并
4. **Release 发布**：积累到一定更新后发布新版本

### 6.6 备份策略

| 备份方式 | 频率 | 说明 |
|---------|------|------|
| GitHub 仓库自身 | 实时 | GitHub 提供冗余存储 |
| 本地完整克隆 | 每周 | `git clone --mirror` 完整备份 |
| 导出知识库文档 | 每月 | 导出 `knowledge/` 目录为 PDF/ZIP |

**本地备份命令**：

```bash
# 完整镜像备份（含所有分支和历史）
git clone --mirror https://<用户名>@github.com/<用户名>/prefab-interior-materials-expert.git
# 打包保存
tar -czf prefab-interior-materials-expert-backup-$(date +%Y%m%d).tar.gz prefab-interior-materials-expert.git/
```

---

## 七、快速启动清单

按以下顺序执行，即可完成第一个仓库的创建与初始化：

- [ ] **Step 1**：在 GitHub 网页创建私有仓库（勾选 README）
- [ ] **Step 2**：创建 Personal Access Token（按本文权限配置）
- [ ] **Step 3**：在本地克隆仓库
  ```bash
  git clone https://<用户名>:<Token>@github.com/<用户名>/prefab-interior-materials-expert.git
  ```
- [ ] **Step 4**：配置 Git 凭证管理器
  ```bash
  git config --global credential.helper manager
  ```
- [ ] **Step 5**：配置 Git 用户信息
  ```bash
  git config --global user.name "您的姓名"
  git config --global user.email "your-email@example.com"
  ```
- [ ] **Step 6**：将现有 Qoder Skill 文件复制到仓库目录
- [ ] **Step 7**：创建 `.gitignore` 文件
- [ ] **Step 8**：首次提交
  ```bash
  git add .
  git commit -m "feat: 初始化装配式装修专家技能仓库"
  git push origin main
  ```
- [ ] **Step 9**：验证远程仓库已同步
- [ ] **Step 10**：创建 `develop` 分支
  ```bash
  git checkout -b develop
  git push origin develop
  ```

---

> 本策划书基于 GitHub 平台特性和装配式装修智能体项目特点编制，具体执行时请根据实际情况调整。
