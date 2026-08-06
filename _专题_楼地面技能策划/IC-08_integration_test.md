# IC-08 集成测试文档：FL → ACE 撞击声计算接口

> **文档版本**：v1.0  
> **创建日期**：2026-07-10  
> **关联契约**：interface-contracts.md 第八节待注册接口 — 楼地面技能（FL）→ 隔声计算引擎（ACE）  
> **测试目标**：验证 IC-08 调用流程的端到端完整性，覆盖浮筑地面（M5 模型）、架空地面（MSM 模型）和极端隔声场景（模型边界检测）三条核心路径  
> **前置依赖**：IC-08 契约详细定义（待注册）、ACE M5/MSM 计算模型实现

---

## 一、IC-08 接口契约草案

> 本节为 IC-08 的临时契约定义，供集成测试使用。正式版本应在楼地面技能 v2 重构时注册至 interface-contracts.md。

### 1.1 IC-08 基本信息

| 项目 | 说明 |
|------|------|
| **契约编号** | IC-08 |
| **调用场景** | B2 验证协议 Step 3（计算验证），需要估算撞击声改善量或浮筑后撞击声压级 |
| **调用方向** | prefab-floor-system → acoustic-calculation-engine |
| **调用时机** | SRE 标准推理完成（Step 0）、输入解析完成（Step 1）、三原则审查通过（Step 2）之后 |
| **降级策略** | ACE 不可用 → 使用 reference.md A2 简化估算（M5 公式手算），标注"简化估算（隔声计算引擎暂不可用）" |

### 1.2 IC-08 请求 Schema（IC-08-Request 草案）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "IC-08-Request",
  "title": "楼地面技能→隔声计算引擎 请求参数（撞击声）",
  "type": "object",
  "required": ["calculation_type", "evaluation_metric", "construction"],
  "properties": {
    "calculation_type": {
      "type": "string",
      "enum": ["impact_sound"],
      "description": "计算类型，固定为撞击声"
    },
    "evaluation_metric": {
      "type": "string",
      "enum": ["Ln,w", "L'nT,w", "Delta_L"],
      "description": "目标评价量，由 IC-10 SRE 推理确定"
    },
    "construction": {
      "type": "object",
      "required": ["slab_type", "slab_thickness_mm", "slab_density_kgm2"],
      "properties": {
        "slab_type": {
          "type": "string",
          "enum": ["钢筋混凝土", "预应力混凝土", "钢-混凝土组合楼板", "其他"],
          "description": "结构楼板类型"
        },
        "slab_thickness_mm": {
          "type": "number",
          "minimum": 80,
          "maximum": 300,
          "description": "结构楼板厚度，单位 mm"
        },
        "slab_density_kgm2": {
          "type": "number",
          "minimum": 150,
          "maximum": 800,
          "description": "结构楼板面密度，单位 kg/m²"
        },
        "construction_type": {
          "type": "string",
          "enum": ["floating", "elevated", "dry_leveling", "direct_lay"],
          "description": "地面构造类型：浮筑/架空/干法调平/直铺"
        },
        "floating_layer": {
          "type": "object",
          "required": ["elastic_pad_material", "elastic_pad_stiffness_MNm3", "floating_mass_kgm2"],
          "properties": {
            "elastic_pad_material": {
              "type": "string",
              "description": "弹性垫层材料名称"
            },
            "elastic_pad_stiffness_MNm3": {
              "type": "number",
              "minimum": 1,
              "maximum": 100,
              "description": "弹性垫层动态刚度，单位 MN/m³"
            },
            "elastic_pad_thickness_mm": {
              "type": "number",
              "minimum": 2,
              "maximum": 60,
              "description": "弹性垫层厚度，单位 mm"
            },
            "floating_mass_kgm2": {
              "type": "number",
              "minimum": 10,
              "maximum": 300,
              "description": "浮筑层面密度（弹性垫以上所有构造层总质量），单位 kg/m²"
            }
          },
          "description": "浮筑层参数（construction_type=floating 时必填）"
        },
        "elevated_layer": {
          "type": "object",
          "required": ["cavity_depth_mm", "board_material", "board_thickness_mm", "board_density_kgm2"],
          "properties": {
            "cavity_depth_mm": {
              "type": "number",
              "minimum": 20,
              "maximum": 300,
              "description": "架空空腔深度，单位 mm"
            },
            "board_material": {
              "type": "string",
              "description": "基层板材料"
            },
            "board_thickness_mm": {
              "type": "number",
              "minimum": 8,
              "maximum": 40,
              "description": "基层板厚度，单位 mm"
            },
            "board_density_kgm2": {
              "type": "number",
              "minimum": 5,
              "maximum": 60,
              "description": "基层板面密度，单位 kg/m²"
            },
            "surface_material": {
              "type": "string",
              "description": "面层材料"
            },
            "surface_thickness_mm": {
              "type": "number",
              "description": "面层厚度，单位 mm"
            },
            "surface_density_kgm2": {
              "type": "number",
              "description": "面层密度，单位 kg/m²"
            },
            "cavity_fill": {
              "type": "string",
              "enum": ["无", "岩棉", "玻璃棉", "其他"],
              "default": "无",
              "description": "空腔填充材料"
            },
            "support_spacing_mm": {
              "type": "number",
              "description": "支撑脚间距，单位 mm"
            }
          },
          "description": "架空层参数（construction_type=elevated 时必填）"
        }
      }
    },
    "detail_level": {
      "type": "string",
      "enum": ["standard", "detailed"],
      "default": "standard",
      "description": "计算精度等级"
    }
  }
}
```

### 1.3 IC-08 响应 Schema（IC-08-Response 草案）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "IC-08-Response",
  "title": "隔声计算引擎→楼地面技能 响应参数（撞击声）",
  "type": "object",
  "required": ["calculation_status", "f0_Hz", "improvement", "sound_bridge_risk", "assumptions"],
  "properties": {
    "calculation_status": {
      "type": "string",
      "enum": ["success", "boundary_warning", "parameter_insufficient", "out_of_scope"],
      "description": "计算状态"
    },
    "model_used": {
      "type": "string",
      "enum": ["M5", "MSM", "M5+MSM", "none"],
      "description": "使用的计算模型"
    },
    "f0_Hz": {
      "type": "object",
      "properties": {
        "value": { "type": "number", "description": "共振频率，单位 Hz" },
        "evaluation": {
          "type": "string",
          "enum": ["优秀(<80Hz)", "良好(80-150Hz)", "一般(150-250Hz)", "差(≥250Hz)"],
          "description": "共振频率评价"
        }
      }
    },
    "improvement": {
      "type": "object",
      "required": ["DeltaLw_lower", "DeltaLw_upper"],
      "properties": {
        "DeltaLw_lower": { "type": "number", "description": "改善量区间下限，单位 dB" },
        "DeltaLw_upper": { "type": "number", "description": "改善量区间上限，单位 dB" },
        "precision_statement": { "type": "string", "description": "精度声明文本" }
      }
    },
    "Lnw_estimate": {
      "type": "object",
      "properties": {
        "bare_slab_Lnw": { "type": "number", "description": "裸板 Ln,w 基准值，单位 dB" },
        "Lnw_lower": { "type": "number", "description": "构造后 Ln,w 估算下限" },
        "Lnw_upper": { "type": "number", "description": "构造后 Ln,w 估算上限" }
      },
      "description": "撞击声压级估算（仅当 evaluation_metric 包含 Ln,w 时返回）"
    },
    "sound_bridge_risk": {
      "type": "object",
      "required": ["level", "description"],
      "properties": {
        "level": { "type": "string", "enum": ["无", "低", "中", "高"] },
        "description": { "type": "string" },
        "risk_items": {
          "type": "array",
          "items": { "type": "string" },
          "description": "具体风险点列表"
        }
      }
    },
    "boundary_warning": {
      "type": "object",
      "properties": {
        "is_boundary": { "type": "boolean" },
        "details": { "type": "string" },
        "recommendation": { "type": "string" }
      },
      "description": "模型边界警告（calculation_status=boundary_warning 时必填）"
    },
    "assumptions": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "description": "计算假设说明列表"
    }
  }
}
```

### 1.4 IC-08 调用约束

| 约束项 | 规则 |
|--------|------|
| ACE 不做合规判断 | ACE 仅返回技术计算结果，"是否满足标准要求"由 FL 的 A1 性能指标表判断 |
| 精度声明强制 | ACE 返回的改善量必须附带精度声明（±3-5 dB for ΔLw，±4-6 dB for Ln,w） |
| 模型选择由 ACE 决定 | FL 传递 construction_type，ACE 根据构造类型自动选择 M5/MSM 模型 |
| 参数不足时降级 | 缺少必填参数时返回 parameter_insufficient 状态并列明缺失字段 |
| 超出边界时警告 | 参数超出模型适用范围时返回 boundary_warning，FL 据此触发降级路径 |

---

## 二、测试场景 1：住宅浮筑地面（典型浮筑构造，M5 模型路径）

### 2.1 场景描述

| 项目 | 参数 |
|------|------|
| **场景名称** | 住宅分户楼板 — 标准湿式浮筑地面 |
| **建筑类型** | 住宅 |
| **空间类型** | 分户楼板 |
| **适用标准** | GB 55038-2025（强制性） |
| **评价量** | L'nT,w（现场标准化撞击声压级） |
| **限值** | L'nT,w ≤ 65 dB |
| **构造类型** | 浮筑地面（floating） |

**构造层次（自上而下）**：

| 层次 | 材料 | 厚度 | 面密度 |
|------|------|------|--------|
| 面层 | 瓷砖 | 10mm | ~25 kg/m² |
| 浮筑砂浆层 | 水泥砂浆 | 40mm | ~80 kg/m² |
| 弹性垫层 | 橡胶隔声垫 | 5mm | — |
| 结构楼板 | 钢筋混凝土 | 120mm | 288 kg/m² |

**关键参数**：
- 浮筑层面密度 m' = 80 + 15 ≈ 95 kg/m²（砂浆 + 面层，不含弹性垫自身质量）
- 弹性垫动态刚度 s = 15 MN/m³ = 15 × 10⁶ N/m³

### 2.2 IC-08 请求 JSON

```json
{
  "calculation_type": "impact_sound",
  "evaluation_metric": "L'nT,w",
  "construction": {
    "slab_type": "钢筋混凝土",
    "slab_thickness_mm": 120,
    "slab_density_kgm2": 288,
    "construction_type": "floating",
    "floating_layer": {
      "elastic_pad_material": "橡胶隔声垫",
      "elastic_pad_stiffness_MNm3": 15,
      "elastic_pad_thickness_mm": 5,
      "floating_mass_kgm2": 95
    }
  },
  "detail_level": "standard"
}
```

### 2.3 预期计算过程（手算验证基准）

**f₀ 共振频率计算**：

```
f₀ = (1/2π) × √(s / m')
   = (1/2π) × √(15×10⁶ / 95)
   = (1/2π) × √(157,895)
   = (1/2π) × 397.4
   = 63.2 Hz
```

**f₀ 评价**：63.2 Hz < 80 Hz → **优秀**（全频段有效改善）

**ΔLw 改善量计算（M5 模型，C=10，s 取 MN/m³ 口径）**：

```
ΔLw ≈ 18·log₁₀(m') - 10·log₁₀(s) + C
    = 18·log₁₀(95) - 10·log₁₀(15) + 10
    = 18 × 1.978 - 10 × 1.176 + 10
    = 35.6 - 11.8 + 10
    = 33.8 dB
```

> **更正说明（2026-08-06，CG-20260806-008）**：本节原按 N/m³ 口径计算（10·log₁₀(15×10⁶)=71.8，得 −26.2 后"取绝对值→21.5 dB"）为错误记录。M5 经验常数 C=10 按 MN/m³ 口径标定，N/m³ 口径会引入固定偏移导致结果失真。按 MN/m³ 口径更正为 33.8 dB，与策划方案、QA 测试、examples 的既有计算一致（量纲分析与三文件自洽校核，E4 专家判断，经用户确认仲裁）。
>
> **置信度警示**：公式计算值 33.8 dB 高于该构造浮筑楼板的典型实测改善量区间（ΔLw ≈ 18-25 dB，S3 经验常数），偏高约 9-16 dB。33.8 dB 应视为公式乐观上限而非预期实测值；稳健估算取经验区间 18-25 dB。ACE 实现时须同时输出公式值与置信度警示，不得仅输出单一口径。

**浮筑后撞击声压级估算**：

```
裸板基准 Ln,w ≈ 76-80 dB（120mm 钢筋混凝土，取中值 78 dB）
公式点估计：78 - 33.8 ≈ 44.2 dB（乐观上限，见置信度警示）
稳健估算：按经验改善区间 18-25 dB → Ln,w ≈ 53-60 dB
判据基准：取稳健区间 53-60 dB 用于合规判断
```

### 2.4 预期 ACE 响应 JSON

```json
{
  "calculation_status": "success",
  "model_used": "M5",
  "f0_Hz": {
    "value": 63.2,
    "evaluation": "优秀(<80Hz)"
  },
  "improvement": {
    "DeltaLw_formula": 33.8,
    "DeltaLw_lower": 18,
    "DeltaLw_upper": 25,
    "confidence_note": "公式值 33.8 dB（MN/m³ 口径）高于经验区间 18-25 dB，公式值仅为乐观上限，稳健估算以经验区间为准",
    "precision_statement": "ACE 专业估算，ΔLw 精度 ±3-5 dB，Ln,w 精度 ±4-6 dB"
  },
  "Lnw_estimate": {
    "bare_slab_Lnw": 78,
    "Lnw_lower": 53,
    "Lnw_upper": 60
  },
  "sound_bridge_risk": {
    "level": "低",
    "description": "标准浮筑构造，声桥风险取决于施工质量",
    "risk_items": [
      "边缝隔声垫连续性须施工过程控制",
      "管道穿越处须设弹性套管隔离",
      "门槛处须做隔声断开处理"
    ]
  },
  "boundary_warning": {
    "is_boundary": false,
    "details": null,
    "recommendation": null
  },
  "assumptions": [
    "裸板 Ln,w 基准值基于 120mm 钢筋混凝土典型值（78 dB），实际值因楼板配筋和饰面可能偏差 ±2 dB",
    "弹性垫动态刚度 s=15 MN/m³ 为产品标称值，实际值受长期压缩和温度影响",
    "浮筑层面密度 m'=95 kg/m² 假设砂浆层厚度均匀且密实",
    "M5 模型假设弹性垫层为理想弹簧，忽略阻尼影响",
    "未考虑侧向传声和施工质量对现场检测结果的影响"
  ]
}
```

### 2.5 FL 解读与合规判断逻辑

**Step 1：接收 ACE 响应**

FL 解析 ACE 返回的 `calculation_status`，确认为 `success`，继续处理。

**Step 2：提取关键结果**

| 提取项 | ACE 返回值 | FL 使用方式 |
|--------|-----------|------------|
| ΔLw 公式值 | 33.8 dB（乐观上限） | 仅作方向性参考，不作定量判据 |
| ΔLw 经验区间 | 18-25 dB（附置信度警示） | 用于估算浮筑后 Ln,w |
| Ln,w 估算区间 | 53-60 dB | 直接用于合规判断 |
| f₀ | 63.2 Hz（优秀） | 评价隔声机理有效性 |
| 声桥风险 | 低 | 整合到 D4 核验维度 |

**Step 3：合规判断**

```
适用标准：GB 55038-2025
评价量：L'nT,w（现场标准化撞击声压级）
限值：≤ 65 dB

ACE 估算 Ln,w 区间：53-60 dB
注意：ACE 返回的是 Ln,w（实验室评价量），FL 需要说明 Ln,w 与 L'nT,w 的关系

FL 判断逻辑：
- Ln,w 估算上限 60 dB < 限值 65 dB
- 考虑现场条件可能使 L'nT,w 与 Ln,w 存在差异（通常 ±2-4 dB）
- 即使考虑最不利情况（L'nT,w ≈ Ln,w + 4 dB），60 + 4 = 64 dB < 65 dB
- 结论：达标（有余量），但建议现场检测确认

精度声明附加：
"ACE 专业估算，精度 ±4-6 dB，最终确认应以现场 L'nT,w 检测为准"
```

**Step 4：D 维度核验**

| 维度 | 结果 | 说明 |
|------|------|------|
| D1-隔声 | ✓ | Ln,w 估算 53-60 dB，低于 L'nT,w ≤ 65 dB 限值，余量充足 |
| D2-标高 | ✓ | 构造总厚度 55mm（5+40+10），标高影响可控 |
| D3-承载 | ✓ | 恒荷载增量约 1.1 kN/m²，住宅楼板一般可承载 |
| D4-声桥 | ✓ | 声桥风险低，须施工过程控制 |
| D5-边缝 | — | 须补充边缝隔声垫方案（≥55mm 宽闭孔 PE 垫条） |
| D7-平整度 | ✓ | 砂浆面层平整度 ≤3mm/2m，满足瓷砖铺贴要求 |

### 2.6 集成测试 Pass/Fail 判定标准

| 测试点 | Pass 条件 | Fail 条件 |
|--------|----------|----------|
| IC-08 请求格式 | JSON 符合 IC-08-Request Schema，所有必填字段完整 | Schema 校验失败或必填字段缺失 |
| ACE 模型选择 | ACE 正确识别 construction_type=floating，选择 M5 模型 | ACE 错误选择 MSM 或其他模型 |
| f₀ 计算 | 返回 60-66 Hz 范围内的值（手算 63.2 Hz ±5%） | 计算结果偏差 >10% 或未返回 |
| ΔLw 估算 | 返回公式值 ≈33.8 dB（MN/m³ 口径）及经验区间 18-25 dB，并附置信度警示 | 返回旧 N/m³ 口径错误值 21.5 dB，或仅返回单一口径无警示 |
| Ln,w 估算 | 返回区间 53-60 dB（或 ±4 dB 容差范围内） | 未返回估算区间或数值严重偏离 |
| 声桥风险 | 返回风险评估且等级合理（低/中） | 未评估声桥风险 |
| 假设声明 | 返回非空假设列表（≥3 条） | 假设列表为空 |
| FL 合规判断 | FL 正确判断达标且附加精度声明 | FL 输出"满足"但不附加精度声明（违反 FL-R-P0-3） |
| FL 评价量使用 | FL 使用 L'nT,w 作为住宅判据，不使用 Ln,w 或 Rw | FL 混用评价量（违反 FL-R-P0-1） |

**场景 1 总结判定**：全部 9 个测试点 Pass → 场景 1 通过。

---

## 三、测试场景 2：酒店架空地面（非浮筑构造，MSM 模型路径）

### 3.1 场景描述

| 项目 | 参数 |
|------|------|
| **场景名称** | 酒店客房地面 — 架空构造 + 管线分离 |
| **建筑类型** | 酒店 |
| **空间类型** | 客房 |
| **适用标准** | GB 50118-2010（非住宅部分仍有效） |
| **评价量** | Ln,w（实验室计权撞击声压级） |
| **限值** | Ln,w ≤ 55 dB（高要求级） |
| **构造类型** | 架空地面（elevated） |

**构造层次（自上而下）**：

| 层次 | 材料 | 厚度 | 面密度 |
|------|------|------|--------|
| 面层 | PVC 地板 | 8mm | ~11 kg/m² |
| 基层板 | 硅酸钙板 | 18mm | ~22 kg/m² |
| 架空空腔 | 空气层（含支撑脚） | 100mm | — |
| 结构楼板 | 钢筋混凝土 | 120mm | 288 kg/m² |

**关键参数**：
- 架空层总面质量 m₁ = 22 + 11 = 33 kg/m²（基层板 + 面层）
- 空腔深度 d = 100mm = 0.1m
- 无弹性垫层（非浮筑构造）
- 支撑脚间距 500mm（典型值）

### 3.2 IC-08 请求 JSON

```json
{
  "calculation_type": "impact_sound",
  "evaluation_metric": "Ln,w",
  "construction": {
    "slab_type": "钢筋混凝土",
    "slab_thickness_mm": 120,
    "slab_density_kgm2": 288,
    "construction_type": "elevated",
    "elevated_layer": {
      "cavity_depth_mm": 100,
      "board_material": "硅酸钙板",
      "board_thickness_mm": 18,
      "board_density_kgm2": 22,
      "surface_material": "PVC 地板",
      "surface_thickness_mm": 8,
      "surface_density_kgm2": 11,
      "cavity_fill": "无",
      "support_spacing_mm": 500
    }
  },
  "detail_level": "standard"
}
```

### 3.3 预期计算过程（手算验证基准）

**MSM 模型（质量-弹簧-质量系统）**：

架空地面不能直接使用 M5 模型（M5 仅适用于浮筑构造的弹簧-质量系统），应使用 MSM 模型。

**空腔空气层等效刚度**：

```
s_air = ρ₀ × c² / d
      = 1.2 × 343² / 0.1
      = 1.2 × 117,649 / 0.1
      = 1,411,788 N/m³
      ≈ 1.41 × 10⁶ N/m³
```

**MSM 共振频率**：

```
f₀_MSM = (1/2π) × √(s_air × (1/m₁ + 1/m₂))

其中：
  m₁ = 33 kg/m²（架空层面板质量）
  m₂ = 288 kg/m²（结构楼板质量）
  1/m₁ + 1/m₂ = 1/33 + 1/288 = 0.0303 + 0.00347 = 0.03378

f₀_MSM = (1/2π) × √(1.41×10⁶ × 0.03378)
       = (1/2π) × √(47,630)
       = (1/2π) × 218.2
       = 34.7 Hz
```

> 注：纯 MSM 模型的 f₀ 约 34.7 Hz，看似较低，但架空构造的隔声机理与浮筑不同——架空层的隔声改善主要依赖面板质量和空腔吸声，而非弹簧-质量隔振。MSM 模型的改善量估算需考虑面板质量比和空腔阻尼。

**架空层撞击声改善量估算**：

基于 reference.md 7.6 节参考数据：
- 硅酸钙板 15mm + 空腔 100mm → ΔLw ≈ 8-13 dB（L6 理论估算）
- 本场景 18mm 板 + 100mm 空腔 → ΔLw ≈ 10-15 dB（估算）

**浮筑后撞击声压级估算**：

```
裸板 Ln,w ≈ 78 dB
架空后 Ln,w ≈ 78 - (10~15) = 63-68 dB
```

**合规判断**：Ln,w 63-68 dB > 55 dB（酒店高要求）→ **不达标**

### 3.4 预期 ACE 响应 JSON

```json
{
  "calculation_status": "success",
  "model_used": "MSM",
  "f0_Hz": {
    "value": 34.7,
    "evaluation": "优秀(<80Hz)"
  },
  "improvement": {
    "DeltaLw_lower": 10,
    "DeltaLw_upper": 15,
    "precision_statement": "ACE 专业估算（MSM 模型），ΔLw 精度 ±3-5 dB，架空构造精度低于浮筑构造"
  },
  "Lnw_estimate": {
    "bare_slab_Lnw": 78,
    "Lnw_lower": 63,
    "Lnw_upper": 68
  },
  "sound_bridge_risk": {
    "level": "中",
    "description": "架空构造存在多种声桥路径，需专项控制",
    "risk_items": [
      "支撑脚形成结构声桥——支撑脚直接连接基层板与结构楼板，振动可经支撑脚传递",
      "管道穿越架空层——管道与基层板接触处可形成声桥",
      "基层板接缝——板缝处理不当可导致振动传递",
      "空腔内缺乏吸声填充——无填充时空腔共振可能放大中频撞击声"
    ]
  },
  "boundary_warning": {
    "is_boundary": false,
    "details": null,
    "recommendation": null
  },
  "assumptions": [
    "MSM 模型假设空腔空气层为理想弹簧，实际空腔刚度受支撑脚排列和管线布局影响",
    "架空层面板质量 m₁=33 kg/m² 假设基层板和面层均匀铺设",
    "未考虑空腔内可能存在的管线对声场的散射和阻尼效应",
    "裸板 Ln,w 基准值基于 120mm 钢筋混凝土典型值（78 dB）",
    "MSM 模型精度低于 M5 模型，估算区间仅供参考"
  ]
}
```

### 3.5 FL 解读与合规判断逻辑

**Step 1：接收 ACE 响应**

FL 解析 ACE 返回的 `calculation_status`，确认为 `success`，`model_used` 为 `MSM`。

**Step 2：提取关键结果**

| 提取项 | ACE 返回值 | FL 使用方式 |
|--------|-----------|------------|
| 模型类型 | MSM | 确认为架空构造模型（非 M5） |
| ΔLw 区间 | 10-15 dB | 改善量有限 |
| Ln,w 估算区间 | 63-68 dB | 用于合规判断 |
| 声桥风险 | 中 | 整合到 D4 核验维度 |

**Step 3：合规判断**

```
适用标准：GB 50118-2010（非住宅部分）
评价量：Ln,w（实验室计权撞击声压级）
限值：≤ 55 dB（酒店高要求级）

ACE 估算 Ln,w 区间：63-68 dB
合规判断：63-68 dB > 55 dB → ❌ 不达标

差距分析：
- 最佳情况（63 dB）仍超出限值 8 dB
- 最不利情况（68 dB）超出限值 13 dB
- 纯架空构造无法满足酒店高要求级

FL 建议路径：
1. 方案升级：架空 + 浮筑复合构造（在架空基层板上增设弹性垫 + 浮筑面层）
2. 替代方案：采用隔声型架空地板系统（含阻尼层和吸声填充）
3. 专项声学设计：建议委托声学顾问进行专项设计
```

**Step 4：D 维度核验**

| 维度 | 结果 | 说明 |
|------|------|------|
| D1-隔声 | ✗ | Ln,w 估算 63-68 dB，超出 ≤55 dB 限值，不达标 |
| D2-标高 | ✓ | 构造总厚度 126mm（100+18+8），酒店标高通常可控 |
| D3-承载 | ✓ | 恒荷载增量约 0.4 kN/m²，轻量化 |
| D4-声桥 | ✗ | 声桥风险中等，支撑脚声桥路径显著 |
| D6-管线 | ✓ | 100mm 空腔可容纳电气管线和小管径给水管 |

**Step 5：风险识别输出**

FL 应识别以下风险并输出：
1. **隔声不达标风险**（❌）：纯架空构造 ΔLw 仅 10-15 dB，无法达到酒店高要求级 ≤55 dB
2. **声桥风险**（⚠️）：支撑脚形成刚性声桥，管道穿越处可能加剧声桥效应
3. **建议升级路径**：架空+浮筑复合构造或专项声学设计

### 3.6 集成测试 Pass/Fail 判定标准

| 测试点 | Pass 条件 | Fail 条件 |
|--------|----------|----------|
| IC-08 请求格式 | JSON 包含 elevated_layer 参数，construction_type=elevated | 请求中误用 floating_layer 或缺少 elevated_layer |
| ACE 模型选择 | ACE 正确识别架空构造，选择 MSM 模型（非 M5） | ACE 错误使用 M5 模型 |
| f₀_MSM 计算 | 返回 30-40 Hz 范围内（手算 34.7 Hz ±15%） | 计算结果严重偏离或未返回 |
| ΔLw 估算 | 返回区间在 8-18 dB 范围（架空构造典型区间） | 返回与浮筑构造相当的 ΔLw（>18 dB），说明模型选择错误 |
| 声桥风险评估 | 返回中等或以上风险，且识别支撑脚声桥 | 未识别支撑脚声桥风险（违反 FL-R-P1-6） |
| FL 合规判断 | FL 正确判断不达标，不使用"满足"表述 | FL 错误判断为达标 |
| FL 评价量使用 | FL 使用 Ln,w（非住宅），不使用 L'nT,w 或 Rw | FL 混用评价量 |
| FL 建议路径 | FL 给出方案升级建议（复合构造/专项设计） | FL 仅输出不达标结论但不提供改善路径 |
| FL 风险标记 | FL 输出中使用 ❌ 和 ⚠️ 确定性标记 | FL 不标注不确定性或风险 |

**场景 2 总结判定**：全部 9 个测试点 Pass → 场景 2 通过。

---

## 四、测试场景 3：极端隔声场景（录音室，模型边界检测）

### 4.1 场景描述

| 项目 | 参数 |
|------|------|
| **场景名称** | 录音室地面 — 极端隔声浮筑构造 |
| **建筑类型** | 特殊功能建筑（录音室/琴房） |
| **空间类型** | 录音室 |
| **适用标准** | 无统一强制标准，参照行业惯例 Ln,w ≤ 45-50 dB |
| **评价量** | Ln,w（实验室计权撞击声压级） |
| **限值** | Ln,w ≤ 50 dB（行业惯例参考值） |
| **构造类型** | 浮筑地面（floating），重型构造 |

**构造层次（自上而下）**：

| 层次 | 材料 | 厚度 | 面密度 |
|------|------|------|--------|
| 面层 | 硬木地板 | 15mm | ~11 kg/m² |
| 浮筑砂浆层 | 水泥砂浆 | 60mm | ~120 kg/m² |
| 弹性垫层 | 复合隔声垫 | 10mm | — |
| 结构楼板 | 钢筋混凝土 | 200mm | 480 kg/m² |

**关键参数**：
- 浮筑层面密度 m' = 120 + 11 = 131 kg/m²
- 弹性垫动态刚度 s = 8 MN/m³ = 8 × 10⁶ N/m³（极低刚度，高性能隔声垫）
- 结构楼板面密度 480 kg/m²（加厚楼板）

### 4.2 IC-08 请求 JSON

```json
{
  "calculation_type": "impact_sound",
  "evaluation_metric": "Ln,w",
  "construction": {
    "slab_type": "钢筋混凝土",
    "slab_thickness_mm": 200,
    "slab_density_kgm2": 480,
    "construction_type": "floating",
    "floating_layer": {
      "elastic_pad_material": "复合隔声垫（橡胶+发泡）",
      "elastic_pad_stiffness_MNm3": 8,
      "elastic_pad_thickness_mm": 10,
      "floating_mass_kgm2": 131
    }
  },
  "detail_level": "detailed"
}
```

### 4.3 预期计算过程（手算验证基准）

**f₀ 共振频率计算**：

```
f₀ = (1/2π) × √(s / m')
   = (1/2π) × √(8×10⁶ / 131)
   = (1/2π) × √(61,069)
   = (1/2π) × 247.1
   = 39.3 Hz
```

**f₀ 评价**：39.3 Hz < 80 Hz → **优秀**（远低于撞击声主要频段）

**ΔLw 改善量计算（M5 模型，C=10，s 取 MN/m³ 口径）**：

```
ΔLw ≈ 18·log₁₀(m') - 10·log₁₀(s) + C
    = 18·log₁₀(131) - 10·log₁₀(8) + 10
    = 18 × 2.117 - 10 × 0.903 + 10
    = 38.1 - 9.0 + 10
    = 39.1 dB
```

> **更正说明（2026-08-06，CG-20260806-008）**：本节原按 N/m³ 口径计算（38.1 − 69.0 + 10 = −20.9，后取 25.6 dB）为错误记录，已按 MN/m³ 口径更正为 39.1 dB，仲裁依据同场景 1。
>
> **边界判定**：公式值 39.1 dB 显著超出 M5 模型适用上限（约 ΔLw ≤ 25-28 dB），公式已进入外推区，计算结果仅作边界检测触发依据，不作定量判据。

**浮筑后撞击声压级估算**：

```
裸板基准 Ln,w ≈ 72-76 dB（200mm 钢筋混凝土，取中值 74 dB）
公式点估计：74 - 39.1 ≈ 34.9 dB（外推值，不可靠，不作为判断依据）
注：原文 45-52 dB 区间基于错误口径的 25.6 dB 推得，一并撤回；
边界场景以 boundary_warning 降级路径输出为准
```

### 4.4 预期 ACE 响应 JSON

```json
{
  "calculation_status": "boundary_warning",
  "model_used": "M5",
  "f0_Hz": {
    "value": 39.3,
    "evaluation": "优秀(<80Hz)"
  },
  "improvement": {
    "DeltaLw_formula": 39.1,
    "extrapolation_warning": "公式值 39.1 dB（MN/m³ 口径）超出 M5 适用上限（约 25-28 dB），结果处于外推区，不作为定量依据",
    "precision_statement": "ACE 专业估算（超出模型适用边界），定量精度不保证"
  },
  "Lnw_estimate": {
    "bare_slab_Lnw": 74,
    "Lnw_formula": 34.9,
    "note": "公式点估计 34.9 dB 为外推结果，不用于合规判断；边界场景以降级路径输出为准"
  },
  "sound_bridge_risk": {
    "level": "高",
    "description": "极端隔声场景下，任何声桥的负面影响将被放大",
    "risk_items": [
      "边缝隔声垫任何中断都将导致隔声显著劣化——极端隔声场景下声桥敏感度极高",
      "管道穿越必须采用独立弹性套管+双道隔声环——单道隔离不足以维持极端隔声性能",
      "浮筑砂浆层 60mm 厚度可能产生温度裂缝——裂缝处弹性垫暴露形成声桥",
      "硬木地板安装龙骨钉可能穿透浮筑层——须采用浮铺或胶粘方式",
      "200mm 厚结构楼板的侧向传声路径——楼板与墙体连接处需弹性隔离"
    ]
  },
  "boundary_warning": {
    "is_boundary": true,
    "details": "当前构造参数超出 M5 模型适用边界：(1) ΔLw 公式值 ≈ 39.1 dB（MN/m³ 口径）超出 M5 模型适用上限（约 ΔLw ≤ 25-28 dB），模型进入外推区，高频段吻合效应和阻尼损耗未被模型覆盖；(2) f₀=39.3 Hz 极低，可能与建筑结构低频模态耦合，M5 模型未考虑结构-声学交互效应；(3) 极端隔声场景（Ln,w < 50 dB）的精度显著降低，实际性能强烈依赖施工质量。",
    "recommendation": "建议进行专项声学设计，包括：(1) 实验室 ΔL 检测验证（GB/T 19889.8）；(2) 考虑架空+浮筑复合构造以获得更高隔声余量；(3) 委托具有声学设计资质的专业机构进行全频段 1/3 倍频程分析。"
  },
  "assumptions": [
    "裸板 Ln,w 基准值基于 200mm 钢筋混凝土典型值（74 dB），厚板低频段性能可能优于典型值",
    "弹性垫动态刚度 s=8 MN/m³ 为产品标称值，极低刚度垫层的实际性能受安装条件和长期压缩影响较大",
    "浮筑层面密度 m'=131 kg/m² 假设 60mm 砂浆层均匀密实，实际含水率变化可能影响面密度",
    "M5 模型在 ΔLw > 25 dB 区间的外推精度未经充分验证",
    "未考虑 200mm 厚楼板的弯曲刚度对撞击声频谱的影响",
    "未考虑建筑结构侧向传声（flanking transmission），在极端隔声场景下侧向传声可能成为主要限制因素"
  ]
}
```

### 4.5 FL 解读与降级处理逻辑

**Step 1：接收 ACE 响应**

FL 解析 ACE 返回的 `calculation_status`，识别为 `boundary_warning`。**触发 FL 降级路径**。

**Step 2：边界警告处理**

```
ACE 返回 boundary_warning 状态，FL 执行以下处理：

1. 停止基于 ACE 结果做确定性合规判断
2. 提取边界警告详情（boundary_warning.details）
3. 提取改善建议（boundary_warning.recommendation）
4. 在输出中标注"ACE 模型接近适用边界"
5. 不将 ACE 估算值表述为可靠结论（遵守 FL-R-P0-3）
```

**Step 3：降级输出**

FL 应输出以下内容（按 §9 模板结构）：

```
## 隔声估算

- 裸板基准：Ln,w = 72-76 dB（200mm 钢筋混凝土）
- ACE 公式值：ΔLw ≈ 39.1 dB（⚠️ 超出 M5 模型适用上限 25-28 dB，处于外推区）
- ACE 公式点估计：浮筑后 Ln,w ≈ 34.9 dB（外推值，不作为判断依据）
- 精度声明：定量精度不保证（超出模型适用边界）

⚠️ 模型边界警告：
ACE 隔声计算引擎提示当前构造参数超出 M5 模型适用范围。
ΔLw 公式值 39.1 dB 超出 M5 模型上限区间（25-28 dB），模型进入外推区，
高频吻合效应、结构-声学耦合效应和施工质量敏感性均未被模型覆盖。

❓ 需确认：
- 该估算结果仅供方向性参考，不作为合规判断依据
- 建议委托具有声学设计资质的专业机构进行专项分析
- 建议进行实验室 ΔL 检测（GB/T 19889.8）验证实际性能

## 合规判断
- 目标：Ln,w ≤ 50 dB（录音室行业惯例）
- ACE 公式点估计：34.9 dB（外推值，不可靠；名义达标但不作数）
- 判断：❓ 无法确定——需专项声学分析确认
```

**Step 4：D 维度核验**

| 维度 | 结果 | 说明 |
|------|------|------|
| D1-隔声 | 🔲 | ACE 边界警告，无法做出确定判断，需专项分析 |
| D2-标高 | ✓ | 构造总厚度 85mm（10+60+15），录音室通常标高充裕 |
| D3-承载 | ⚠️ | 恒荷载增量约 1.5 kN/m²（含 60mm 砂浆），需确认 200mm 楼板承载力 |
| D4-声桥 | ⚠️ | 声桥风险高，极端隔声场景下任何声桥影响被放大 |
| D5-边缝 | ⚠️ | 边缝处理要求极高，须采用专用隔声构造 |

### 4.6 集成测试 Pass/Fail 判定标准

| 测试点 | Pass 条件 | Fail 条件 |
|--------|----------|----------|
| IC-08 请求格式 | JSON 包含大厚度楼板（200mm）和低刚度垫层（8 MN/m³）参数 | 参数超出 Schema 允许范围但未处理 |
| ACE 边界检测 | ACE 返回 `boundary_warning` 状态，正确识别 ΔLw 公式值超出模型适用上限 | ACE 返回 `success` 状态，未检测到边界问题 |
| ACE 警告详情 | boundary_warning 包含 details 和 recommendation 字段 | 仅返回边界状态但不提供详情和建议 |
| ACE 精度降级 | 精度声明从 ±3-5 dB 降级为 ±4-6 dB 或更低 | 精度声明与常规场景相同（未降级） |
| FL 降级触发 | FL 识别 boundary_warning 并触发降级路径 | FL 忽略 boundary_warning，继续做确定性判断 |
| FL 确定性标记 | FL 使用 ❓（无法确定）标记，不使用 ✅ 或 ✗ | FL 输出 ✅ 达标 或 ❌ 不达标的确定结论（违反 FL-R-P0-3） |
| FL 建议转介 | FL 建议专项声学设计和实验室检测 | FL 不给出改善路径 |
| FL 精度声明 | FL 明确标注"接近模型适用边界"和降低的精度声明 | FL 使用标准精度声明（未降级） |
| 声桥风险 | ACE 返回"高"风险等级并列出极端场景特有的风险点 | 声桥风险评估与常规场景相同（未识别极端场景特殊性） |

**场景 3 总结判定**：全部 9 个测试点 Pass → 场景 3 通过。

---

## 五、跨场景一致性校验

### 5.1 IC-08 请求一致性

| 校验项 | 场景 1（浮筑） | 场景 2（架空） | 场景 3（极端） | 一致性要求 |
|--------|-------------|-------------|-------------|----------|
| calculation_type | impact_sound | impact_sound | impact_sound | 全部相同 |
| evaluation_metric | L'nT,w | Ln,w | Ln,w | 住宅用 L'nT,w，非住宅用 Ln,w |
| construction_type | floating | elevated | floating | 正确反映构造类型 |
| slab_type 必填 | ✓ | ✓ | ✓ | 全部包含 |
| 对应层参数 | floating_layer | elevated_layer | floating_layer | 与 construction_type 匹配 |

### 5.2 ACE 响应一致性

| 校验项 | 场景 1 | 场景 2 | 场景 3 | 一致性要求 |
|--------|--------|--------|--------|----------|
| calculation_status | success | success | boundary_warning | 常规场景 success，边界场景 boundary_warning |
| model_used | M5 | MSM | M5 | 浮筑→M5，架空→MSM |
| f₀ 返回 | ✓ | ✓ | ✓ | 全部返回且评价合理 |
| ΔLw 输出 | 公式值 33.8 + 经验区间 18-25 dB | 10-15 dB | 公式值 39.1（外推警示） | 常规场景双口径+警示，边界场景外推警示 |
| 声桥风险 | ✓（低） | ✓（中） | ✓（高） | 全部评估且等级递进合理 |
| 假设列表 | ✓（≥3 条） | ✓（≥3 条） | ✓（≥5 条） | 全部非空，极端场景更多假设 |

### 5.3 FL 行为一致性

| 校验项 | 场景 1 | 场景 2 | 场景 3 | 一致性要求 |
|--------|--------|--------|--------|----------|
| 评价量选择 | L'nT,w（住宅） | Ln,w（非住宅） | Ln,w（非住宅） | 与 SRE 推理结果一致 |
| 合规判断 | ✓ 达标 | ✗ 不达标 | 🔲 无法确定 | 三种结论类型覆盖 |
| 精度声明 | 标准声明 | 标准声明+MSM 说明 | 降级声明 | 声明级别与模型可信度匹配 |
| 红线合规 | 无红线触发 | 无红线触发 | FL-R-P0-3（不隐瞒不确定性）正确执行 | 所有场景不违反 P0 红线 |

---

## 六、回归测试与边界用例

### 6.1 参数不足降级测试

**测试输入**：发送缺少 `floating_layer.floating_mass_kgm2` 的请求。

**预期 ACE 响应**：

```json
{
  "calculation_status": "parameter_insufficient",
  "model_used": "none",
  "missing_fields": ["construction.floating_layer.floating_mass_kgm2"],
  "message": "浮筑层面密度未提供，无法执行 M5 模型计算。请提供弹性垫层以上所有构造层的总面密度（kg/m²）。"
}
```

**FL 预期行为**：FL 收到 parameter_insufficient 后，应向用户追问缺失参数，或使用典型值估算并标注假设。

### 6.2 IC-08 降级路径测试（ACE 不可用）

**测试条件**：模拟 ACE 服务不可用（超时/无响应）。

**FL 预期行为**：

```
1. FL 检测到 ACE 调用失败（超时/错误）
2. FL 切换至 reference.md A2 简化估算法（M5 公式手算）
3. FL 在输出中标注：
   "简化估算（隔声计算引擎暂不可用），精度降低，仅供方向性参考"
4. FL 使用 M5 公式手算 ΔLw，精度声明降级为 ±5-8 dB
5. FL 建议用户在 ACE 恢复后重新执行计算
```

### 6.3 评价量混用防护测试

**测试输入**：在场景 1（住宅）中，IC-08 请求的 evaluation_metric 误设为 "Rw+C"。

**预期 ACE 行为**：
- ACE 识别 Rw+C 为空气声评价量，不属于撞击声计算范畴
- 返回错误响应：`"evaluation_metric 'Rw+C' 不适用于撞击声计算，请使用 Ln,w / L'nT,w / Delta_L"`

**FL 预期行为**：
- FL 在 Step 2（三原则审查）中应捕获评价量不匹配
- 触发 FL-R-P0-1 红线（严禁混淆撞击声与空气声评价量）
- 修正评价量后重新提交 IC-08 请求

---

## 七、测试执行清单

### 7.1 测试矩阵

| 测试编号 | 场景 | 测试项 | 优先级 | 状态 |
|---------|------|--------|--------|------|
| T-08-01 | 场景 1 | IC-08 请求 Schema 校验 | P0 | ☐ |
| T-08-02 | 场景 1 | ACE M5 模型选择正确性 | P0 | ☐ |
| T-08-03 | 场景 1 | f₀ 计算精度（±5%） | P0 | ☐ |
| T-08-04 | 场景 1 | ΔLw 估算区间合理性 | P0 | ☐ |
| T-08-05 | 场景 1 | FL 合规判断与精度声明 | P0 | ☐ |
| T-08-06 | 场景 1 | FL 评价量使用正确性（L'nT,w） | P0 | ☐ |
| T-08-07 | 场景 2 | IC-08 请求 elevated_layer 参数 | P0 | ☐ |
| T-08-08 | 场景 2 | ACE MSM 模型选择正确性 | P0 | ☐ |
| T-08-09 | 场景 2 | FL 不达标判断正确性 | P0 | ☐ |
| T-08-10 | 场景 2 | FL 声桥风险识别 | P1 | ☐ |
| T-08-11 | 场景 2 | FL 方案升级建议 | P1 | ☐ |
| T-08-12 | 场景 3 | ACE 边界检测（boundary_warning） | P0 | ☐ |
| T-08-13 | 场景 3 | ACE 精度降级声明 | P1 | ☐ |
| T-08-14 | 场景 3 | FL 降级路径触发 | P0 | ☐ |
| T-08-15 | 场景 3 | FL 确定性标记（❓） | P0 | ☐ |
| T-08-16 | 场景 3 | FL 专项分析建议 | P1 | ☐ |
| T-08-17 | 通用 | 参数不足降级（6.1） | P1 | ☐ |
| T-08-18 | 通用 | ACE 不可用降级（6.2） | P1 | ☐ |
| T-08-19 | 通用 | 评价量混用防护（6.3） | P0 | ☐ |
| T-08-20 | 通用 | 跨场景一致性校验（5.1-5.3） | P1 | ☐ |

### 7.2 测试通过标准

| 等级 | 要求 | 对应测试编号 |
|------|------|------------|
| **全部通过** | 所有 20 个测试点 Pass | T-08-01 ~ T-08-20 |
| **核心通过** | 所有 P0 测试点 Pass | T-08-01~06, 07~09, 12, 14~15, 19 |
| **不通过** | 任一 P0 测试点 Fail | — |

### 7.3 红线合规验证矩阵

| 红线编号 | 验证场景 | 预期行为 | 对应测试编号 |
|---------|---------|---------|------------|
| FL-R-P0-1 | 6.3 评价量混用 | FL 捕获并修正评价量错误 | T-08-19 |
| FL-R-P0-2 | 全场景 | FL 不将 ACE 估算表述为检测值 | T-08-05, 09, 15 |
| FL-R-P0-3 | 场景 3 | FL 在边界场景标注不确定性 | T-08-15 |
| FL-R-P0-5 | 全场景 | FL 在输出前完成 B2 验证 | T-08-05, 09, 14 |
| FL-R-P1-3 | 场景 1 | FL 区分 Ln,w 与 L'nT,w | T-08-06 |
| FL-R-P1-6 | 场景 2 | FL 评估架空构造声桥风险 | T-08-10 |

---

## 八、附录：计算验证表

### A. 场景 1 手算验证

| 计算项 | 公式 | 输入值 | 计算结果 |
|--------|------|--------|---------|
| s 口径说明 | M5 经验式取 MN/m³，f₀ 式取 N/m³ | 15 MN/m³ | f₀ 用 15×10⁶ N/m³；ΔLw 用 15 MN/m³ |
| f₀ | (1/2π)×√(s/m') | s=15×10⁶, m'=95 | 63.2 Hz |
| log₁₀(m') | log₁₀(95) | — | 1.978 |
| log₁₀(s) | log₁₀(15) | — | 1.176 |
| 18·log₁₀(m') | 18×1.978 | — | 35.6 |
| 10·log₁₀(s) | 10×1.176 | — | 11.8 |
| ΔLw | 35.6 - 11.8 + 10 | — | 33.8 dB（公式值；高于经验区间 18-25，见置信度警示） |
| Ln,w(浮筑) | 78 - 33.8 | — | 44.2 dB（公式点估计，乐观；稳健区间 53-60 dB） |

### B. 场景 2 手算验证

| 计算项 | 公式 | 输入值 | 计算结果 |
|--------|------|--------|---------|
| s_air | ρ₀×c²/d | ρ₀=1.2, c=343, d=0.1 | 1.41×10⁶ N/m³ |
| 1/m₁ + 1/m₂ | 1/33 + 1/288 | — | 0.03378 |
| f₀_MSM | (1/2π)×√(s_air×(1/m₁+1/m₂)) | — | 34.7 Hz |
| ΔLw（参考值） | reference.md 7.6 节 | 18mm板+100mm空腔 | 10-15 dB |
| Ln,w(架空) | 78 - 12.5（中值） | — | 65.5 dB |

### C. 场景 3 手算验证

| 计算项 | 公式 | 输入值 | 计算结果 |
|--------|------|--------|---------|
| s 口径说明 | M5 经验式取 MN/m³，f₀ 式取 N/m³ | 8 MN/m³ | f₀ 用 8×10⁶ N/m³；ΔLw 用 8 MN/m³ |
| f₀ | (1/2π)×√(s/m') | s=8×10⁶, m'=131 | 39.3 Hz |
| log₁₀(m') | log₁₀(131) | — | 2.117 |
| log₁₀(s) | log₁₀(8) | — | 0.903 |
| 18·log₁₀(m') | 18×2.117 | — | 38.1 |
| 10·log₁₀(s) | 10×0.903 | — | 9.0 |
| ΔLw | 38.1 - 9.0 + 10 | — | 39.1 dB（超出模型上限 25-28，外推区） |
| Ln,w(浮筑) | 74 - 39.1 | — | 34.9 dB（外推值，不作为判据） |

---

> **文档维护说明**：本文档应在 IC-08 契约正式注册至 interface-contracts.md 后同步更新。测试用例中的预期数值应在 ACE 实现稳定后通过实际运行验证并更新。
