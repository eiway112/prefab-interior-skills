# IC-08 / IC-10 形式化 JSON Schema 草案

> **文件定位**：IC-03 模式的形式化扩展草案，为 interface-contracts.md 中 IC-08（楼地面→ACE 撞击声隔声）和 IC-10（任何技能→SRE 场景查询）补充字段约束表与 JSON Schema（draft 2020-12）。
>
> **参照基准**：IC-03 字段约束表 + JSON Schema（interface-contracts.md v1.2，2026-06-17）
>
> **草案版本**：v1.0

---

## 一、IC-08：楼地面技能 → 隔声计算引擎

### IC-08 字段约束表（向形式化 schema 过渡）

> 以下为 IC-08 接口的结构化字段约束，用于 skill-qa-tester 自动校验参数完整性。后续建仓时可据此生成机器可校验的 JSON Schema。

*请求参数约束*：

| 字段名 | 类型 | 必填/可选 | 取值范围 / 枚举 | 降级行为 |
|-------|------|----------|---------------|---------|
| 调用方标识.技能标识 | string | 必填 | 固定值："FL" | 缺失时返回"参数不足"并列出 |
| 调用方标识.计算类型 | string | 必填 | 固定值："撞击声隔声" | 缺失时返回"参数不足" |
| 调用方标识.评价量 | string | 必填 | 枚举：Ln,w / ΔL | 缺失时返回"参数不足"并列出 |
| 构造描述.构造类型 | string | 必填 | 枚举：浮筑 / 架空 / 干法调平 / 快装 | 缺失时返回"参数不足" |
| 构造描述.板材层 | 数组[object] | 必填 | 每层含：材料类别(string)、厚度_mm(number)、面密度_kg_m2(number, 可选) | 缺失时返回"参数不足" |
| 构造描述.板材层[].材料类别 | string | 必填 | 枚举：混凝土楼板 / 细石混凝土 / 橡胶垫 / 弹性垫层 / 水泥砂浆 / OSB板 / 硅酸钙板 / 隔声垫 / 其他 | 缺失时返回"参数不足" |
| 构造描述.板材层[].厚度_mm | number | 必填 | 正数，单位 mm，合理范围 1-300 | 缺失时返回"参数不足" |
| 构造描述.板材层[].面密度_kg_m2 | number | 可选 | 正数，单位 kg/㎡，合理范围 1-500 | 缺失时由 ACE 根据材料类别+厚度推算 |
| 构造描述.支撑/连接系统.支撑类型 | string | 必填 | 枚举：浮筑垫层 / 架空支撑 / 调平螺栓 / 直铺 / 其他 | 缺失时返回"参数不足" |
| 构造描述.支撑/连接系统.弹性垫动态刚度_MN_m3 | number | 可选 | 正数，单位 MN/m³，合理范围 5-100 | 缺失时 ACE 使用典型值并标注假设 |
| 构造描述.密封方式 | string | 可选 | 枚举：MS密封胶 / 隔声密封条 / 普通密封 / 未指定 | 默认"未指定"并标注密封风险 |

*响应参数约束*：

| 字段名 | 类型 | 必返回 | 取值范围 / 枚举 | 备注 |
|-------|------|--------|---------------|------|
| 计算结果.隔声估算区间.下限_dB | number | 是 | ≥0，单位 dB | 区间下限（撞击声场景下越低越好） |
| 计算结果.隔声估算区间.上限_dB | number | 是 | ≥下限_dB，单位 dB | 区间上限 |
| 计算结果.隔声估算区间.评价量 | string | 是 | 枚举：Ln,w / ΔL | 须与发起方请求的评价量一致 |
| 计算结果.隔声估算区间.置信度 | string | 是 | 枚举：高 / 中 / 低 | 估算结果的可信程度 |
| 风险识别.声桥风险等级.等级 | string | 是 | 枚举：无 / 低 / 中 / 高 | 声桥风险等级 |
| 风险识别.声桥风险等级.风险点 | 数组[string] | 是 | — | 具体风险点列表，不可为空 |
| 风险识别.声桥风险等级.说明 | string | 是 | — | 风险说明文本 |
| 风险识别.密封评估.结论 | string | 是 | 枚举：充分 / 需确认 / 不足 / 无法判断 | 密封状态评估 |
| 风险识别.密封评估.依据 | string | 是 | — | 评估依据文本 |
| 风险识别.密封评估.改进建议 | 数组[string] | 否 | — | 密封改进措施建议列表 |
| 关键假设说明 | 数组[string] | 是 | — | 计算中使用的前提假设列表，不可为空 |
| 适用边界声明 | string | 是 | — | 本次计算适用的场景和精度声明 |
| 超出范围提示 | 数组[string] | 是 | — | 本次计算未涵盖的因素列表，不可为空 |

---

### IC-08 形式化 JSON Schema（v1.0）

> 以下 JSON Schema 由上方字段约束表自动生成，可用于 skill-qa-tester 自动校验。建仓后可直接用于 CI/CD 管线中的接口契约校验。

*请求 Schema（IC-08-Request）*：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "IC-08-Request",
  "title": "楼地面技能→隔声计算引擎 请求参数",
  "type": "object",
  "required": ["调用方标识", "构造描述"],
  "properties": {
    "调用方标识": {
      "type": "object",
      "required": ["技能标识", "计算类型", "评价量"],
      "properties": {
        "技能标识": {
          "type": "string",
          "const": "FL",
          "description": "发起方技能标识，固定为 FL（楼地面技能）"
        },
        "计算类型": {
          "type": "string",
          "const": "撞击声隔声",
          "description": "计算类型，固定为撞击声隔声"
        },
        "评价量": {
          "type": "string",
          "enum": ["Ln,w", "ΔL"],
          "description": "撞击声评价量：Ln,w（计权规范化撞击声压级）或 ΔL（撞击声改善量）"
        }
      },
      "additionalProperties": false
    },
    "构造描述": {
      "type": "object",
      "required": ["构造类型", "板材层", "支撑/连接系统"],
      "properties": {
        "构造类型": {
          "type": "string",
          "enum": ["浮筑", "架空", "干法调平", "快装"],
          "description": "楼地面构造类型"
        },
        "板材层": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["材料类别", "厚度_mm"],
            "properties": {
              "材料类别": {
                "type": "string",
                "enum": ["混凝土楼板", "细石混凝土", "橡胶垫", "弹性垫层", "水泥砂浆", "OSB板", "硅酸钙板", "隔声垫", "其他"],
                "description": "该层材料类别"
              },
              "厚度_mm": {
                "type": "number",
                "minimum": 1,
                "maximum": 300,
                "description": "该层厚度，单位 mm"
              },
              "面密度_kg_m2": {
                "type": "number",
                "minimum": 1,
                "maximum": 500,
                "description": "该层面密度，单位 kg/㎡；缺失时由 ACE 推算"
              }
            },
            "additionalProperties": false
          },
          "minItems": 1,
          "description": "各构造层描述，从上到下或从下到上排列"
        },
        "支撑/连接系统": {
          "type": "object",
          "required": ["支撑类型"],
          "properties": {
            "支撑类型": {
              "type": "string",
              "enum": ["浮筑垫层", "架空支撑", "调平螺栓", "直铺", "其他"],
              "description": "支撑/连接系统类型"
            },
            "弹性垫动态刚度_MN_m3": {
              "type": "number",
              "minimum": 5,
              "maximum": 100,
              "description": "弹性垫动态刚度，单位 MN/m³；缺失时 ACE 使用典型值并标注假设"
            }
          },
          "additionalProperties": false
        },
        "密封方式": {
          "type": "string",
          "enum": ["MS密封胶", "隔声密封条", "普通密封", "未指定"],
          "default": "未指定",
          "description": "密封处理方式"
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

*响应 Schema（IC-08-Response）*：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "IC-08-Response",
  "title": "隔声计算引擎→楼地面技能 响应参数",
  "type": "object",
  "required": ["计算结果", "风险识别", "关键假设说明", "适用边界声明", "超出范围提示"],
  "properties": {
    "计算结果": {
      "type": "object",
      "required": ["隔声估算区间"],
      "properties": {
        "隔声估算区间": {
          "type": "object",
          "required": ["下限_dB", "上限_dB", "评价量", "置信度"],
          "properties": {
            "下限_dB": {
              "type": "number",
              "minimum": 0,
              "description": "撞击声隔声估算区间下限，单位 dB"
            },
            "上限_dB": {
              "type": "number",
              "minimum": 0,
              "description": "撞击声隔声估算区间上限，单位 dB，须 ≥ 下限_dB"
            },
            "评价量": {
              "type": "string",
              "enum": ["Ln,w", "ΔL"],
              "description": "须与发起方请求的评价量一致"
            },
            "置信度": {
              "type": "string",
              "enum": ["高", "中", "低"],
              "description": "估算结果的可信程度"
            }
          },
          "additionalProperties": false
        }
      },
      "additionalProperties": false
    },
    "风险识别": {
      "type": "object",
      "required": ["声桥风险等级", "密封评估"],
      "properties": {
        "声桥风险等级": {
          "type": "object",
          "required": ["等级", "风险点", "说明"],
          "properties": {
            "等级": {
              "type": "string",
              "enum": ["无", "低", "中", "高"]
            },
            "风险点": {
              "type": "array",
              "items": { "type": "string" },
              "minItems": 1,
              "description": "具体风险点列表"
            },
            "说明": {
              "type": "string",
              "description": "声桥风险说明文本"
            }
          },
          "additionalProperties": false
        },
        "密封评估": {
          "type": "object",
          "required": ["结论", "依据"],
          "properties": {
            "结论": {
              "type": "string",
              "enum": ["充分", "需确认", "不足", "无法判断"]
            },
            "依据": {
              "type": "string",
              "description": "密封评估依据文本"
            },
            "改进建议": {
              "type": "array",
              "items": { "type": "string" },
              "description": "密封改进措施建议列表"
            }
          },
          "additionalProperties": false
        }
      },
      "additionalProperties": false
    },
    "关键假设说明": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "description": "计算中使用的前提假设列表，不可为空"
    },
    "适用边界声明": {
      "type": "string",
      "description": "本次计算适用的场景和精度声明，如：适用于浮筑地面的撞击声改善量估算，精度约 ±4-6 dB"
    },
    "超出范围提示": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "description": "本次计算未涵盖的因素列表，如：现场侧向传声未纳入模型"
    }
  },
  "additionalProperties": false
}
```

---

## 二、IC-10：任何技能 → 标准推理引擎（场景查询）

### IC-10 字段约束表（向形式化 schema 过渡）

> 以下为 IC-10 接口的结构化字段约束，用于 skill-qa-tester 自动校验参数完整性。后续建仓时可据此生成机器可校验的 JSON Schema。

*请求参数约束*：

| 字段名 | 类型 | 必填/可选 | 取值范围 / 枚举 | 降级行为 |
|-------|------|----------|---------------|---------|
| 项目类型 | string | 必填 | 枚举：住宅 / 酒店 / 医院 / 学校 / 办公 / 商业 / 其他 | 缺失时返回"参数不足"并列出 |
| 空间类型 | string | 必填 | 自由文本，如：分户墙 / 客房隔墙 / 走廊隔墙 / 卫生间 / 楼地面 / 吊顶 等 | 缺失时返回"参数不足"并列出 |
| 项目所在地 | string | 可选 | 省/市名称，如：北京市 / 浙江省 / 广东省 | 缺失时默认"全国"并标注"未筛选地方标准" |
| 构造体系 | string | 可选 | 自由文本，如：轻钢龙骨 / 条板 / 模块化 / 浮筑地面 / 架空地面 等 | 缺失时返回全构造体系适用标准 |
| 性能需求 | 数组[string] | 必填 | 枚举：隔声 / 耐火 / 防火 / 环保 / 验收 / 抗震 / 防水 / 其他 | 缺失时返回"参数不足"并列出 |

*响应参数约束*：

| 字段名 | 类型 | 必返回 | 取值范围 / 枚举 | 备注 |
|-------|------|--------|---------------|------|
| 适用标准集 | 数组[object] | 是 | — | 按层级和权限排序的标准列表，不可为空 |
| 适用标准集[].标准编号 | string | 是 | 如 GB 55038-2025 / GB 50118-2010 等 | 标准正式编号 |
| 适用标准集[].标准名称 | string | 是 | — | 标准全称 |
| 适用标准集[].层级 | string | 是 | 枚举：L1 / L2 / L3 / L4 | L1=强制性国标, L2=推荐性国标/行标, L3=地方标准, L4=团体/企业标准 |
| 适用标准集[].权限 | string | 是 | 枚举：red_line / binding_support / reference | red_line=红线不可突破, binding_support=约束性支撑, reference=参考性 |
| 适用标准集[].角色 | string | 是 | 枚举：mandatory_check / design_basis / verification_reference / construction_guide / prefab_evaluation | 该标准在本场景中的角色定位 |
| 适用标准集[].地域适用性 | string | 是 | 枚举：全国 / 项目所在地适用 / 不适用仅作对比 | 标准的地域适用范围 |
| 适用标准集[].时间状态 | string | 是 | 枚举：现行有效 / 过渡期 / 即将实施 / 已废止 | 标准的时间有效性状态 |
| 适用标准集[].替代警告 | string | 否 | — | 如有部分替代情况，说明具体替代条文；无替代时省略此字段 |
| 推理路径 | string | 是 | — | 场景→领域→标准族的推理链路描述 |
| 未覆盖领域 | 数组[string] | 否 | — | 性能领域中无明确适用标准的部分，附建议咨询方向 |

---

### IC-10 形式化 JSON Schema（v1.0）

> 以下 JSON Schema 由上方字段约束表自动生成，可用于 skill-qa-tester 自动校验。建仓后可直接用于 CI/CD 管线中的接口契约校验。

*请求 Schema（IC-10-Request）*：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "IC-10-Request",
  "title": "任何技能→标准推理引擎 请求参数",
  "type": "object",
  "required": ["项目类型", "空间类型", "性能需求"],
  "properties": {
    "项目类型": {
      "type": "string",
      "enum": ["住宅", "酒店", "医院", "学校", "办公", "商业", "其他"],
      "description": "项目类型，决定适用的建筑分类标准体系"
    },
    "空间类型": {
      "type": "string",
      "minLength": 1,
      "description": "具体空间类型，如：分户墙、客房隔墙、走廊隔墙、卫生间、楼地面、吊顶等"
    },
    "项目所在地": {
      "type": "string",
      "description": "省/市名称，如：北京市、浙江省、广东省；缺失时默认全国范围，不筛选地方标准"
    },
    "构造体系": {
      "type": "string",
      "description": "构造体系名称，如：轻钢龙骨、条板、模块化、浮筑地面、架空地面等；缺失时返回全构造体系适用标准"
    },
    "性能需求": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["隔声", "耐火", "防火", "环保", "验收", "抗震", "防水", "其他"]
      },
      "minItems": 1,
      "description": "性能需求领域列表，决定检索的标准领域范围"
    }
  },
  "additionalProperties": false
}
```

*响应 Schema（IC-10-Response）*：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "IC-10-Response",
  "title": "标准推理引擎→任何技能 响应参数",
  "type": "object",
  "required": ["适用标准集", "推理路径"],
  "properties": {
    "适用标准集": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["标准编号", "标准名称", "层级", "权限", "角色", "地域适用性", "时间状态"],
        "properties": {
          "标准编号": {
            "type": "string",
            "description": "标准正式编号，如 GB 55038-2025"
          },
          "标准名称": {
            "type": "string",
            "description": "标准全称"
          },
          "层级": {
            "type": "string",
            "enum": ["L1", "L2", "L3", "L4"],
            "description": "标准层级：L1=强制性国标, L2=推荐性国标/行标, L3=地方标准, L4=团体/企业标准"
          },
          "权限": {
            "type": "string",
            "enum": ["red_line", "binding_support", "reference"],
            "description": "标准权限等级：red_line=红线不可突破, binding_support=约束性支撑, reference=参考性"
          },
          "角色": {
            "type": "string",
            "enum": ["mandatory_check", "design_basis", "verification_reference", "construction_guide", "prefab_evaluation"],
            "description": "该标准在本场景中的角色定位"
          },
          "地域适用性": {
            "type": "string",
            "enum": ["全国", "项目所在地适用", "不适用仅作对比"],
            "description": "标准的地域适用范围"
          },
          "时间状态": {
            "type": "string",
            "enum": ["现行有效", "过渡期", "即将实施", "已废止"],
            "description": "标准的时间有效性状态"
          },
          "替代警告": {
            "type": "string",
            "description": "如有部分替代情况，说明具体替代条文；无替代时可省略"
          }
        },
        "additionalProperties": false
      },
      "minItems": 1,
      "description": "按层级和权限排序的适用标准列表"
    },
    "推理路径": {
      "type": "string",
      "minLength": 1,
      "description": "场景→领域→标准族的推理链路描述"
    },
    "未覆盖领域": {
      "type": "array",
      "items": { "type": "string" },
      "description": "性能领域中无明确适用标准的部分，附建议咨询方向"
    }
  },
  "additionalProperties": false
}
```

---

## 三、Schema 扩展路径说明

当前已完成 JSON Schema 形式化的接口：

| 接口 | 状态 | Schema ID |
|------|------|-----------|
| IC-03 | 已完成 (v1.2) | IC-03-Request / IC-03-Response |
| IC-08 | 本草案 (v1.0) | IC-08-Request / IC-08-Response |
| IC-10 | 本草案 (v1.0) | IC-10-Request / IC-10-Response |

**后续建议**：
- IC-08 / IC-10 经 prefab-standards-reviewer 复核后，合并至 interface-contracts.md 对应章节
- IC-09（吊顶→ACE）可参照 IC-08 模式补充，仅需调整评价量枚举（Rw+C/Rw+Ctr）和构造描述字段（增加空腔层、吊杆参数）
- IC-07（标准复核工具）可参照 IC-10 模式补充，字段结构更简单
