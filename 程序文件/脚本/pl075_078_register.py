#!/usr/bin/env python3
"""PL-075—PL-078 整改批（CG-20260926-001）残量登记：更新数据分类复核清单

两轮同工单，均为「移除失效条目＋按整改后正文重登记判定单元」：

ROUND 1（本批首轮写面后）：移除 26 条（9 STALE_REVIEW ＋ 17 STALE_BASELINE），
  重登记 28 条（含本批新增的效力分离单元与出处注行）。
ROUND 2（§二 复核结论落地的二次写面后）：移除 23 条（17 STALE_REVIEW ＋ 6
  STALE_BASELINE，其中 6 条系 ROUND 1 自身登记的单元因二次编辑再漂指纹），
  重登记 24 条。

两轮合计移除 49 条、重登记 52 条；残量计数不手抄，由 main() 按
len(STALE_RECORD_IDS)／len(STALE_BASELINE_IDS) 现算打印，并与门禁读数对账。

判据来源：shared/data-classification.md §一（类别定义）＋§三（来源列纪律）；
结构约束（本脚本据此选段）：validate_governance.py 检查 10
  - kind==N 的段不查来源（2995—2996 行），非 N 段须有可定位来源（3057 行 MISSING_SOURCE）
  - table_row 的来源 span 必须等于完整来源单元格（3045 行），故无来源列的表行不判非 N
  - 单一来源列的 table_row 省略 source_spans 即由门禁自动绑定该格（3036—3037 行）
  - A 类段须带 verified_on，缺失只 WARN A_VERIFY_DATE（3062—3071 行）

复跑安全：已登记的单元 id 跳过；STALE 条目不存在时只告警不失败；
  ROUND 1 单元因 ROUND 2 编辑而离开扫描面时，须同时出现在 STALE_RECORD_IDS 中
  才允许跳过（否则判 ERROR，防「指纹漂了但没人负责收口」的静默漏登）。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / '_专题_技能合集策划' / '数据分类复核清单.json'
RUNTIME = Path.home() / '.qoder' / 'skills'

GB55030 = '成果/标准核验/GB 55030-2022_核验报告_20260925.md'
GB50209 = '成果/标准核验/GB 50209-2010_核验报告_20260925.md'
VERIFIED = '2026-09-25'

STALE_RECORD_IDS = [
    'prefab-bathroom-kitchen-system/SKILL.md#2ec989c4dc7e93ff13f8dd7400ec7f9900f630f5e16bc2cb16f62819c953ebe8:1',
    'prefab-bathroom-kitchen-system/examples.md#d0a0acbc82b3f934a826850d388a99d125fda4a13712156e1449c32a4a0d742a:1',
    'prefab-bathroom-kitchen-system/reference.md#584f6484a14d955ab5f8738fae54954516c5c29abf6136837aa3b3fe2a461b1e:1',
    'prefab-bathroom-kitchen-system/reference.md#60cf11645d2ba2ab25ab8700ca4cff6096861df1d625700461005245610595af:1',
    'prefab-bathroom-kitchen-system/reference.md#8a27bbf3fb5dfeac070e43c9913d75a4769328555fb49456107322db6206edc1:1',
    'prefab-interior-materials-expert/SKILL.md#219b5d2bb32a53113a6dd57e33ab3dfa833757c9fb384fb0382eb585c4032e21:1',
    'prefab-mep-integration-system/SKILL.md#d1e36a32cc8ded331d5b0afd70d33235e084437e94ec9ef380b50f4256d7fb16:1',
    'prefab-storage-system/reference.md#f7dfa609e7f3a89a1d74faaec18606f795db2285398521fbe9c73af44a6f4148:1',
    'shared/redlines-registry.md#62e8e8f43bc4bae81516a375130b62b179dc5e29935b73be06c3975fa3e90d45:1',
]

STALE_BASELINE_IDS = [
    'prefab-bathroom-kitchen-system/SKILL.md#79b59cb33756edaf82e189ca96201ffe136d1b13656c5e2d3549cba8354cde7e:1',
    'prefab-bathroom-kitchen-system/reference.md#0da7e57e44ca0b6d2c3d34add72513b37b3b3dc6723da7d23eec835d470d9626:1',
    'prefab-bathroom-kitchen-system/reference.md#5e585af8b81467d11a0a3fd59c3f1572fc8a11bb3c7b87465f66f8c968896e36:1',
    'prefab-bathroom-kitchen-system/reference.md#cda071266ecb6c754cbe185cbd628900712fe2c2b64dbd074541d584679f9f88:1',
    'prefab-floor-system/SKILL.md#e3e5f06b61cf9cb331a475be8357a35d1e27a893219b92da2e6200e7c5507b2d:1',
    'prefab-floor-system/examples.md#61080b0850048bf7e97bc67339448ac4ba09c29fc4bbbe88474fd8391a28bc2a:1',
    'prefab-floor-system/examples.md#628def2ac23240056a9ac6262e4f7b13683e31a3fa8603153c8e85976fff0e43:1',
    'prefab-floor-system/examples.md#66e7f44c6eeaebcaa9c7d17305cb962a7476806f799d28a3864b7413f2b8bc87:1',
    'prefab-floor-system/examples.md#d6fd48706f67ca6e0d2b06d5e00fd3f4feaf8d8f74300e3a64561f198b3bb2ab:1',
    'prefab-floor-system/reference.md#6f0c3c574d1a2fb03172158cb9de31ce0d734cab79f0069a3b8320b1d9c7e971:1',
    'prefab-floor-system/reference.md#85f6e0d67979bafe6fab1d50df2127d5582f5eb7aeada0373727d3c12a047ddd:1',
    'prefab-floor-system/reference.md#b11cadae9a69d3247a4e862a8fd9bfb8e4b97e6b2ec3a59717a6fa169e348a7b:1',
    'prefab-floor-system/reference.md#e3a3ef2a631ebe86dc4dda3cb76afafd219a4e1f21418cdb44882668a5a994f5:1',
    'prefab-floor-system/reference.md#e700f57bbd824920150728692c71fb5a19aecebb0249b12d9f471ac11a65a8f5:1',
    'prefab-floor-system/reference.md#fdb1f19beb5e63a70ea8d4887643db2198d8602478c90564aa9750850f1aa21d:1',
    'prefab-mep-integration-system/SKILL.md#af32f0dec2673f59fc50fee285db1b8c8755405b7d18881f39882742c6535b7d:1',
    'shared/redlines-registry.md#8b33e8d4d22d55d23992bdf7bc3fabdd74ade131c0ebb2f56d545c5204f0196c:1',
]

# 每段：cut＝下一段起始锚（None＝直至单元末）；source＝[起始锚, 结束锚]，
# 结束锚的区间右端取「该锚之后一个字符」；两者均须在本单元正文内唯一命中。
NEW_UNITS = {
    # ── BK SKILL.md ─────────────────────────────────────────
    'prefab-bathroom-kitchen-system/SKILL.md#949cf5c2c9b4092413b45fe3507fe67681efe27503d53e6f41950ea9b0dbf931:1': [
        {'class': 'N', 'cut': None,
         'reason': 'P0 红线登记行（表列 编号／红线／说明／触发后标准应对，本表无来源列）：本行系红线行为约束的治理陈述；其中「排水坡度不应小于1.0%」与「淋浴区≥1.5%」的取值与效力主张不在本行独立成立——条文级逐字真值与本批改判依据在 prefab-bathroom-kitchen-system/reference.md §B3 表2 两条数据行单元登记（GB 55030-2022 第4.6.3条，2026-09-25 官方出版物核验，凭据＝' + GB55030 + '），本行为其转述指针。登记为 N 系门禁结构判据（表格来源须绑定完整来源单元格，本表无该列），非因本行无数值'}],
    'prefab-bathroom-kitchen-system/SKILL.md#99882e69f3e0356b12348d44a5f60373cef73aa98f91c6e04f77d87aad59b845:1': [
        {'class': 'N', 'cut': None,
         'reason': 'P0 红线登记行（本表无来源列）：「蓄水深度≥20mm、时间≥24h；防水层和饰面层完成后均应蓄水」的条文级真值与逐字核验在 reference.md §B3 闭水试验行与 §C7 检查项 1 两条单元登记（GB 55030-2022 第6.0.12条第1款、第4款，2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）；本行为红线触发后的应对话术，不另立来源，故判非数据断言而非免除溯源——溯源义务由上述真值源面承担'}],

    # ── BK examples.md ──────────────────────────────────────
    'prefab-bathroom-kitchen-system/examples.md#b97fc6c406bdcfb2cfaa5c3c28abd85ace5fda3c03064760388c0d8b2ec1e2a1:1': [
        {'class': 'N', 'cut': None,
         'reason': '示例 1（酒店客房整体卫浴）整块代码示例：本批改写其中坡度行与闭水行的来源列，但块内所有取值主张均为对真值源面的转述——坡度 1.0%／加严值 1.5%、闭水 20mm／24h 的条文级逐字真值在 reference.md §B3 表2 与 §C7 单元同批登记（GB 55030-2022 第4.6.3条、第6.0.12条第1款，2026-09-25 官方出版物核验）；选型比较表各列（防水可靠性／装饰效果／工期／成本／推荐度）为文字等级评定，「4-8h/套」「4.5㎡」为示例给定与行业工期经验；块内 GB 50015-2019 水封≥50mm、坑距 300/400mm、混水阀距地 900-1100mm、220V/2.5mm²、DN100 系既有存量演示参数，本批未逐字核验，其核验义务随既有台账，不因本条登记宣称已核'}],

    # ── BK reference.md ─────────────────────────────────────
    'prefab-bathroom-kitchen-system/reference.md#b5b3d208b469c3b47be6398c87a3e93300f57d98d1723b76ead61ce66b52b320:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§B3 防水排水验证框架「关键判据」列：蓄水≥20mm、≥24h 无渗漏与「防水层和饰面层完成后均应做蓄水试验」逐字对应 GB 55030-2022 第6.0.12条第1款、第4款（2026-09-25 官方出版物逐字核验，凭据＝' + GB55030 + '）。本批订正原误引的 GB 50210-2018 条文号（建筑地面工程蓄水检验不在 GB 50210 体系内），数值本体不变；来源格「S1」系渠道标注，本行合格判据取 §一 A 类三条而非渠道'}],
    'prefab-bathroom-kitchen-system/reference.md#02124e409f8ecf541396394c0b61b37c69d413eeb50a83778fb2a13bc6350de9:1': [
        {'class': 'N', 'cut': None,
         'reason': '§B3 表2 结构题行：本行确立「一般地面＝规范规定值、淋浴区＝合集加严值」的效力分离口径（PL-063 效力分离在本批的具体落实），自身不主张数值 → 非数据断言；两类数值断言在其下两条数据行单元分别登记'}],
    'prefab-bathroom-kitchen-system/reference.md#838865a85a2fab83091aec269f4b13753654eb25d329fc1722ce22fc4b101bc0:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§B3 表2「有防水要求的楼地面｜坡度≥1%」：与 GB 55030-2022 第4.6.3条「排水坡度不应小于1.0%」逐字一致（2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）；本批改判＝原登记判为经验工艺控制值（非规范规定值），与该条文冲突，现按第4.6.3条改判 A 类，并保留「设计文件有更严规定时从设计文件」的接口声明'}],
    'prefab-bathroom-kitchen-system/reference.md#1468fa10b6c9ecca76c8a2bacf30861b00d83e2c11febae0a2e494d4a730b4df:1': [
        {'class': 'D', 'cut': None,
         'reason': '§B3 表2「淋浴区｜坡度≥1.5%」：系本合集在第4.6.3条 1.0% 之上的加严工艺控制值；2026-09-25 官方出版物逐条比对 GB 55030-2022 第4.6 节，未见淋浴区专用坡度条文，故不判 A（不判 A 系无标准出处，非该值无据）；按 §一 D 类判据成立——工艺可达（底盘工厂模压成型可稳定实现）且不与验收规范冲突，来源格已声明「设计文件或项目标准有规定时从其规定」'}],
    'prefab-bathroom-kitchen-system/reference.md#8a8c82e1ed63a00a47b7375978ca0dfc1fe1944fff6c6c855f2c8fd65dd5c72d:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§C7 验收检查清单 序号 1：蓄水≥20mm／24h 无渗漏的合格标准逐字对应 GB 55030-2022 第6.0.12条第1款（2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）；本批将原引 GB 50210-2018 订正为该条，「无破损」观感判据与「目测+闭水试验」检测方法列不构成量化主张'}],
    'prefab-bathroom-kitchen-system/reference.md#ee4bb6109351660cc6db3bda9ab40084aa7a1cb6f6fe68f8cd751728c908c63a:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§C7 验收检查清单 序号 2：「有防水要求的楼地面排水坡度不应小于1.0%」逐字对应 GB 55030-2022 第4.6.3条（2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）；本行来源格按效力分列口径声明——坡度值属本类，「坡向正确、无积水」属观感判据（S3，D 类性质），二者已在来源列显式区分，故本段按承重断言（坡度值）判 A，观感判据不借本段获得 A 类效力'}],

    # ── FL SKILL.md ─────────────────────────────────────────
    'prefab-floor-system/SKILL.md#fe3891113dfa2f521492c4201234105f7885adf1cb9af0e354edd6028b39886b:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§4 关键约束汇总「面层平整度」行：架空活动地板≤2.0mm/2m（表6.1.8 板块面层档）、水泥砂浆≤4mm/2m、水泥混凝土≤5mm/2m、自流平≤2mm/2m（表5.1.7 整体面层档）逐字对应 GB 50209-2010（2026-09-25 官方出版物核验，凭据＝' + GB50209 + '）。本批订正＝原载「≤2mm/2m（架空/干法）、≤3mm/2m（浮筑砂浆面）」以单一数值概括多档且「浮筑砂浆 ≤3mm」无标准档位对应；同列「干法板材面层按表6.1.8 对应面层种类取值（本合集未逐档核验）」不主张具体数值，其取数义务挂本批新登台账，不因本条登记宣称已核'}],

    # ── FL examples.md（D7 核验行，本表无来源列）─────────────
    'prefab-floor-system/examples.md#991034ae516abbeb9aec832661d37a982cc2a373189ca850efd790b6eaec09b9:1': [
        {'class': 'N', 'cut': None,
         'reason': '示例 1 Step 4 的 D7 平整度核验行（表列 维度／编号／结果／说明，本表无来源列）：其中水泥砂浆找平面 ≤4mm/2m 与瓷砖档位的条文级真值在 reference.md §A1 性能指标表（GB 50209-2010 表5.1.7／表6.1.8，2026-09-25 官方出版物核验）单元登记，本行为其转述与示例应用 → 非数据断言；「原载 ≤3mm 无标准档位对应，如需采用属企业内控加严值」系本批对该档位效力的澄清，不另立数值'}],
    'prefab-floor-system/examples.md#98f72e944faad0a6fa3736ecb5525bbd4f8cb150451d41d39e1555ddd78e7bb1:1': [
        {'class': 'N', 'cut': None,
         'reason': '示例 1 标准输出的 D7-平整度行（本表无来源列）：≤4mm/2m 系对 reference.md §A1 表5.1.7 水泥砂浆档（GB 50209-2010，2026-09-25 官方出版物核验）的转述；瓷砖接缝高低差按表6.1.8 档位一行不主张具体数值（本合集未逐档核验）→ 非数据断言'}],
    'prefab-floor-system/examples.md#a9f8b9637931806d6040a17c4d27da6ceb6d35d9bd22d0039c6db14957a4fc0e:1': [
        {'class': 'N', 'cut': None,
         'reason': '示例 4（地暖兼容浮筑地面）Step 4 的 D7 平整度核验行（本表无来源列）：与示例 1 同行同判据——档位真值源在 reference.md §A1，本行转述；瓷砖档未逐档核验故不主张数值 → 非数据断言'}],
    'prefab-floor-system/examples.md#358fe436a7cb0607dd9f3ff4993fe86798fb3eeea7d10ee72b158c127abc9d9a:1': [
        {'class': 'N', 'cut': None,
         'reason': '示例 4 标准输出的 D7-平整度行（本表无来源列）：≤4mm/2m 系对 reference.md §A1 表5.1.7 水泥砂浆档（GB 50209-2010，2026-09-25 官方出版物核验）的转述；瓷砖接缝高低差档位不主张数值 → 非数据断言'}],

    # ── FL reference.md ─────────────────────────────────────
    'prefab-floor-system/reference.md#02615437126d2c43bf7c8d565ace27d0101a465fe53b70e6b840fce63f369d9b:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§A1 其他性能指标「面层平整度｜架空活动地板 ≤2.0mm/2m」：逐字对应 GB 50209-2010 表6.1.8（该表经第6.1.8条、第6.7.14条引用；2026-09-25 官方出版物核验，凭据＝' + GB50209 + '）；本批以「允许偏差按面层种类分档，不以单一数值概括」替换原「≤2mm/2m（架空/干法）」合并写法，干法档不主张具体数值（见同表次二行）'}],
    'prefab-floor-system/reference.md#a3267a8c122e2fefd72f15bd688e6594f2f4b14f971fbb906b99553f605b6aac:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§A1 整体面层分档行：水泥混凝土≤5mm/2m、水泥砂浆≤4mm/2m、自流平≤2mm/2m、普通水磨石≤3mm/2m、高级水磨石≤2mm/2m 逐字对应 GB 50209-2010 表5.1.7（2026-09-25 官方出版物核验，凭据＝' + GB50209 + '）；本批新增该档表以取代原单一数值，各档互不合并'}],
    'prefab-floor-system/reference.md#73369e6fe45d97f7887a4248d002a9fcc80673dacd522eb219a15d6eded59364:1': [
        {'class': 'N', 'cut': None,
         'reason': '§A1 板块面层指针行：本行不主张任何具体数值，仅声明「干法板材面层、陶瓷砖等按表6.1.8 对应面层种类取值」，且来源列自陈「本合集未逐档核验」→ 非数据断言；该未核验面的取数义务见 change-governance.md §11.2 本批新登 PL，登记本行为 N 不构成对该缺口已闭合的宣称'}],
    'prefab-floor-system/reference.md#cf33901fdbb362a37a84bbdb8044cbee8c098396e17a2fccebceb0854467fe3b:1': [
        {'class': 'N', 'cut': None,
         'reason': '§A5 平整度验收「表面平整度」行（表列 验收标准／检测方法／允许偏差，本表无来源列）：本行档位值（架空≤2.0、水泥砂浆≤4、水泥混凝土≤5、自流平≤2、普通水磨石≤3、高级水磨石≤2）逐字真值在 §A1 两行与表后「出处」注行单元登记（GB 50209-2010 表5.1.7／表6.1.8，2026-09-25 官方出版物核验），本行为其转述检查表；登记为 N 系门禁结构判据（本表无来源列，来源须绑完整来源单元格），非因本行无数值'}],
    'prefab-floor-system/reference.md#4baeb07d7f548a2289a82cb5413062ee90074f022aee0102b86e2fe5106d2061:1': [
        {'class': 'N', 'cut': None,
         'reason': '§A5 平整度验收「相邻板块高差」行（本表无来源列）：本批实质数值订正＝木、竹面层由原载 ≤1.0mm 改为 ≤0.5mm，取 GB 50209-2010 表7.1.8 实值（2026-09-25 官方出版物核验，凭据＝' + GB50209 + '），原值偏松于标准属「假合格」方向故必改；该真值的逐字核验与出处在本表后「出处」注行单元登记，本行为检查表转述 → 非数据断言；陶瓷砖等板块档本合集未逐档核验，不主张数值'}],
    'prefab-floor-system/reference.md#3d1989acd982c780d33138d713b31c8b415e8f9df478cfd5c7d222554f8abfed:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'source': ['出处：表面平整度＝GB 50209-2010 表5.1.7', '（2026-09-25 官方出版物核验）'],
         'reason': '§A5 平整度验收表后「出处」注行（本批新增）：承载本表全部档位的条文级出处与核验凭据——表面平整度＝GB 50209-2010 表5.1.7（整体面层）与表6.1.8（板块面层，经第6.1.8条、第6.7.14条引用），相邻板材高差＝表7.1.8，均 2026-09-25 官方出版物逐字核验（凭据＝' + GB50209 + '）；行末「干法板材、陶瓷砖等板块面层的逐档数值本合集未逐档核验」为未覆盖面的显式披露，其取数义务挂本批新登台账，不因本条 A 类登记宣称已核'}],
    'prefab-floor-system/reference.md#143663b9508808b1d8309e0a85120d135fdf99103f82f1ee781007f3c4c7e4ff:1': [
        {'class': 'N', 'cut': None,
         'reason': '§11.5 通用验收检查清单「表面平整度」行（表列 检查项／验收标准／检查方法／适用范围，本表无来源列）：档位值系对 §A1 与 §A5「出处」注行已核验真值（GB 50209-2010 表5.1.7／表6.1.8，2026-09-25 官方出版物核验）的转述，本行不另立来源 → 非数据断言'}],
    'prefab-floor-system/reference.md#350b36d1caf77dcbd19f44c216bed8b7d7ced93f8724dacd456619304e4cc88d:1': [
        {'class': 'N', 'cut': None,
         'reason': '§11.5 通用验收检查清单「相邻板块高差」行（本表无来源列）：木、竹面层 ≤0.5mm 系本批按 GB 50209-2010 表7.1.8 实值的订正转述，其逐字核验真值源在 §A5「出处」注行单元登记（2026-09-25 官方出版物核验）；陶瓷砖等档位未逐档核验、不主张数值 → 本行非数据断言'}],

    # ── materials-expert / MI / ST ──────────────────────────
    'prefab-interior-materials-expert/SKILL.md#bd8d5a7cc2b6073f4c7e21425e60c3f00617a729eda863461084d0e811c64618:1': [
        {'class': 'N', 'cut': None,
         'reason': '「标准引用安全规则」条款号替代写法的示例句（小节内散文）：仅含标准编号与条文号定位，无物理量数值与限值符号 → 非数据断言。本批把该示例的真值源由误引的 GB 50210-2018 第7.1.3条换为 GB 50209-2010 第3.0.24条第3款与 GB 55030-2022 第6.0.12条第1款（2026-09-25 官方出版物核验），其条文级真值与核验凭据在 prefab-bathroom-kitchen-system/reference.md §B3／§C7 单元及 ' + GB55030 + ' 承载，本句不重复主张取值'}],
    'prefab-mep-integration-system/SKILL.md#d31c06a73379a32f5618828a2582a93a72b54181ef50a3fec4a5c5e08502c891:1': [
        {'class': 'A', 'cut': '，套管与管道间作密封处理', 'verified_on': VERIFIED,
         'source': ['（S1：GB 55030-2022 第4.6.6条第3款', '2026-09-25 官方出版物核验）'],
         'reason': '§2.1 管线分离原则：「套管应高出装饰层完成面且不应小于 20mm」逐字对应 GB 55030-2022 第4.6.6条第3款（2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）；本批订正＝原以「管线不得穿越防水层」作规范禁止性条文引用，现行已核验条文中无该禁令，改以第4.6.6条第3款的套管要求表达同一约束'},
        {'class': 'N', 'cut': None,
         'reason': '同段后半：套管与管道间密封做法声明为本合集接口控制要求（S3），并显式披露「本批未逐字核验该条其余款项」；末句为禁令引用撤除的行为澄清，无取值主张 → 非数据断言。该条其余款项的取数义务挂本批新登台账，不因本段登记宣称已核'}],
    'prefab-mep-integration-system/SKILL.md#4a3cc890aa1ac7beb0d99bb54ecf863e94a93882af14d086b93d2da8438b8de1:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§2.5 冲突识别清单「防水冲突」行：来源格按效力分列——套管高度≥20mm 逐字对应 GB 55030-2022 第4.6.6条第3款（2026-09-25 官方出版物核验，凭据＝' + GB55030 + '），密封做法系合集接口控制要求（S3，D 类性质）；本行按承重断言（套管高度）判 A，密封做法不借本段获得 A 类效力，原与 examples.md 的内部矛盾（同点位一处称禁令一处称做法）随本批消解'}],
    'prefab-storage-system/reference.md#184e76758d09955178095a9d3e735e17d7315b5ed78d690e188d543718a3cdc0:1': [
        {'class': 'D', 'cut': None,
         'reason': '§4.2 关键工序交叉控制「柜体与地面防水」行：控制要求「厨卫防水完成+闭水合格后再装柜体」系安装顺序断言，本合集工序控制（S3/D 类），非规范条文规定值；其中「闭水合格」的判据真值按 GB 55030-2022 第6.0.12条第1款（2026-09-25 官方出版物核验）在 prefab-bathroom-kitchen-system/reference.md §C7 单元登记，来源格已按此分列。本批改判＝原登记只标安装顺序、未区分两处效力，现显式分离，避免顺序控制借 A 类获得规范效力'}],

    # ── redlines-registry.md（L1＝运行时 shared 同一 SOT）─────
    'shared/redlines-registry.md#ee02e9762e96b1b7a43a9c290218980b34b014c803fbd1e0c22467cf980d9601:1': [
        {'class': 'N', 'cut': None,
         'reason': '红线注册表 BK-R-P0-3 行（表列 全局编号／内部编号／红线名称／说明／触发后行为，本表无来源列）：与 prefab-bathroom-kitchen-system/SKILL.md 同名为运行时唯一加载面，本行系该红线的镜像登记；1.0%（GB 55030-2022 第4.6.3条）与 1.5%（合集加严值）的取值与效力真值在 reference.md §B3 表2 两条数据行单元登记（2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）→ 本行为转述指针，判非数据断言'}],
    'shared/redlines-registry.md#3acd41b1718ed4c6d70ba235888fb29ad33b8bf7ec1b6c723ac89d02033b4766:1': [
        {'class': 'N', 'cut': None,
         'reason': '红线注册表 BK-R-P0-5 行（本表无来源列）：闭水试验 20mm/24h 与蓄水时点的条文级真值在 prefab-bathroom-kitchen-system/reference.md §B3 与 §C7 单元登记（GB 55030-2022 第6.0.12条第1款，2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）；本行为红线应对话术的镜像登记，不另立来源 → 非数据断言'}],
}

# ── ROUND 2：§二 复核结论落地的二次写面后的残量 ────────────────
# 起因＝本批首轮登记后，复核又推翻四处（跨层漂移／「无渗漏」越逐字主张／
# 第4.6.6条第3款逐字对象过宽／第6.0.12条第4款与工序表矛盾），改面即改指纹。
# 其中 6 条为 ROUND 1 自己登记的单元再漂指纹，故先移除再按新指纹承判。
STALE_RECORD_IDS += [
    'prefab-bathroom-kitchen-system/SKILL.md#4f390760d2913eb86b61e07958a0520fcaacd1694ccd25b95b38ba02b71dd908:1',
    'prefab-bathroom-kitchen-system/SKILL.md#99882e69f3e0356b12348d44a5f60373cef73aa98f91c6e04f77d87aad59b845:1',
    'prefab-bathroom-kitchen-system/examples.md#b97fc6c406bdcfb2cfaa5c3c28abd85ace5fda3c03064760388c0d8b2ec1e2a1:1',
    'prefab-bathroom-kitchen-system/reference.md#8a8c82e1ed63a00a47b7375978ca0dfc1fe1944fff6c6c855f2c8fd65dd5c72d:1',
    'prefab-bathroom-kitchen-system/reference.md#8ce0068019ea445f09df2d3fc632b446b5ff3307ef7309a96a8fca368f6b5203:1',
    'prefab-bathroom-kitchen-system/reference.md#8f830bb9e1de2577762a191e41c07457fda8eafb993a1ce4495931cc99b5d822:1',
    'prefab-bathroom-kitchen-system/reference.md#b5b3d208b469c3b47be6398c87a3e93300f57d98d1723b76ead61ce66b52b320:1',
    'prefab-floor-system/SKILL.md#fe3891113dfa2f521492c4201234105f7885adf1cb9af0e354edd6028b39886b:1',
    'prefab-floor-system/examples.md#991034ae516abbeb9aec832661d37a982cc2a373189ca850efd790b6eaec09b9:1',
    'prefab-floor-system/reference.md#3d1989acd982c780d33138d713b31c8b415e8f9df478cfd5c7d222554f8abfed:1',
    'prefab-floor-system/reference.md#a3267a8c122e2fefd72f15bd688e6594f2f4b14f971fbb906b99553f605b6aac:1',
    'prefab-floor-system/reference.md#cf33901fdbb362a37a84bbdb8044cbee8c098396e17a2fccebceb0854467fe3b:1',
    'prefab-interior-materials-expert/SKILL.md#bd8d5a7cc2b6073f4c7e21425e60c3f00617a729eda863461084d0e811c64618:1',
    'prefab-mep-integration-system/SKILL.md#4a3cc890aa1ac7beb0d99bb54ecf863e94a93882af14d086b93d2da8438b8de1:1',
    'prefab-mep-integration-system/SKILL.md#d31c06a73379a32f5618828a2582a93a72b54181ef50a3fec4a5c5e08502c891:1',
    'prefab-mep-integration-system/examples.md#65573e7bb470c132699f57274c510b4a15a6a3d0ba81515e593c2e4510aca1aa:1',
    'shared/redlines-registry.md#3acd41b1718ed4c6d70ba235888fb29ad33b8bf7ec1b6c723ac89d02033b4766:1',
]

STALE_BASELINE_IDS += [
    'prefab-floor-system/examples.md#5b27c601455fbf9adc64a66d7a1d2ecd1d5464fd734d49701f8f02c63a652de8:1',
    'prefab-floor-system/reference.md#72736e19af3c4be63207cfb5683ce01d50dbc9fb521fc1fde28106a328de9af3:1',
    'prefab-floor-system/reference.md#7fe674ea3efd139da531cba16a2dc6c33e66b2959745266f7d568a0414968711:1',
    'prefab-floor-system/reference.md#8c4140ecef3b0ad74edca45b03e0853f08331bdc587a178d25f17d3c284bfc63:1',
    'prefab-floor-system/reference.md#f1e51ab7a2556540e30298c9bf84a003873e4999647f5d338f7c0866401595cd:1',
    'prefab-floor-system/reference.md#f6913a3d3eb2da07cfaeb6b22684f5a0d5834368368c0337a85f337513553a67:1',
]

# 每段：cut＝下一段起始锚（None＝直至单元末）；source＝[起始锚, 结束锚]，
# 结束锚的区间右端取「该锚之后一个字符」；两者均须在本单元正文内唯一命中。
NEW_UNITS.update({
    # ── BK SKILL.md ＋ 红线镜像面 ────────────────────────────
    'prefab-bathroom-kitchen-system/SKILL.md#5328b7e37e12271cdf9f0b2a455854c661657c1eaed06c33acae4d08dddb880d:1': [
        {'class': 'N', 'cut': None,
         'reason': '验证执行检查清单整块（B 层代码块，本块无来源列可绑）：□3／□4 两行的取值均为对真值源面的转述——「一般区域≥1%、淋浴区≥1.5%」的条文级逐字真值与效力分离在 reference.md §B3 表2 两条数据行单元登记（GB 55030-2022 第4.6.3条＋合集加严值，2026-09-25 官方出版物核验，凭据＝' + GB55030 + '），「蓄水≥20mm、时间≥24h、饰面层完成后须二次蓄水」在 §B3 闭水试验行与 §C7 序号 1 单元登记（同条第1款、第4款）；其余检查项（输入分类、设备接口、专业边界、数据分级、输出模板）为流程与判据索引，不主张取值 → 非数据断言。本条判 N 不削弱其约束力：□4 的闭水时点字面与□9 的地漏预埋／末端篦子字面恰是第十二门禁 P4／P7／R2—R4 的正向锚所在面，撤字面即复红'}],
    'prefab-bathroom-kitchen-system/SKILL.md#f933ccd983dcc44de5a5afd500f611d247556512afb29bab7944ffa7fd604bc8:1': [
        {'class': 'N', 'cut': None,
         'reason': 'P0 红线登记行（表列 编号／红线／说明／触发后标准应对，本表无来源列）：本行系红线行为约束的治理陈述；「蓄水最浅处高度≥20mm、蓄水时间≥24h」与「防水层完成后和饰面层完成后均应蓄水」的条文级真值在 reference.md §B3 闭水试验行与 §C7 序号 1 两条单元登记（GB 55030-2022 第6.0.12条第1款、第4款，2026-09-25 官方出版物核验，凭据＝' + GB55030 + '），并在 shared/redlines-registry.md 镜像行同批判 N。本行相对 ROUND 1 的改动＝补写「最浅处」限定与两款分列（原写法把第4款的两次蓄水并成一句）→ 判类不变。登记为 N 系门禁结构判据（表格来源须绑定完整来源单元格，本表无该列），非因本行无数值'}],
    'shared/redlines-registry.md#8e44f500d75e7dfc20885f5fa9d8457f0ccf65d8447071e2ad764a2512a35343:1': [
        {'class': 'N', 'cut': None,
         'reason': '红线注册表 BK-R-P0-5 行（表列 全局编号／内部编号／红线名称／说明／触发后行为，本表无来源列）：与 prefab-bathroom-kitchen-system/SKILL.md 同名行互为镜像（该件系运行时唯一加载面），本行系其注册登记；闭水 20mm/24h 与两款分别蓄水的条文级真值在 reference.md §B3 与 §C7 单元登记（GB 55030-2022 第6.0.12条第1款、第4款，2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）→ 本行为转述指针，判非数据断言。本批二次编辑使 SKILL.md 与注册表两层同步改写，其字节全等由检查 9 机算（跨层一致），本条不代其宣称'}],

    # ── BK examples.md ＋ reference.md ───────────────────────
    'prefab-bathroom-kitchen-system/examples.md#5bafd1d8eef5f6d1b52c002e013e10e5ad900978a82836ffad3477f754e1499c:1': [
        {'class': 'N', 'cut': None,
         'reason': '示例 1（酒店客房整体卫浴）整块代码示例：块内所有取值主张均为对真值源面的转述——坡度 1.0%／加严值 1.5%、闭水 20mm／24h 的条文级逐字真值在 reference.md §B3 表2 与 §C7 单元同批登记（GB 55030-2022 第4.6.3条、第6.0.12条第1款、第4款，2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）；选型比较表各列（防水可靠性／装饰效果／工期／成本／推荐度）为文字等级评定，「4-8h/套」「4.5㎡」系示例给定与行业工期经验；块内 GB 50015-2019 水封≥50mm、坑距 300/400mm、混水阀距地 900-1100mm、220V/2.5mm²、DN100 系既有存量演示参数，本批未逐字核验，其核验义务随既有台账，不因本条登记宣称已核。本块相对 ROUND 1 的改动＝闭水行把「观感无渗漏」从 S1 逐字范围撤出并标 S3、并补写「SMC 底盘即饰面故一次试验覆盖两款」的适用性注与干法两次蓄水的分界（该注系第十二门禁 P3／R3 判据面）→ 判类不变'}],
    'prefab-bathroom-kitchen-system/reference.md#8f64fbffb3cf617ac83008f327f4320a1dc3ffc8a7751063764cc78e08c8d871:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§B3 防水排水验证框架「关键判据」列：楼、地面最小蓄水高度不应小于20mm、蓄水时间不应少于24h 与厕浴间楼地面防水层和饰面层完成后均应进行蓄水试验，逐字对应 GB 55030-2022 第6.0.12条第1款、第4款（2026-09-25 官方出版物逐字核验，凭据＝' + GB55030 + '）。本批二次订正＝原登记把「无渗漏」一并挂在 S1 逐字主张下，经复核该两款正文未载「无渗漏」三字，现从逐字范围撤出并在判据列显式标 S3（本合集合格判据表述）；判 A 的承重断言仅为蓄水高度、蓄水时间与两次蓄水的规范要求，数值本体不变'}],
    'prefab-bathroom-kitchen-system/reference.md#ff873c14f861230c494250e3ccca0a49035d709429a4c3975814f356604a5e6c:1': [
        {'class': 'N', 'cut': None,
         'reason': '§5.2 干法装配式卫浴典型工序整块（代码块，无来源列可绑）：块内坡度≥1%／淋浴区≥1.5%、蓄水≥20mm／≥24h 均为对 §B3 表2 两条数据行与 §C7 序号 1、2 已核验真值单元的转述（GB 55030-2022 第4.6.3条、第6.0.12条第1款，2026-09-25 官方出版物核验，凭据＝' + GB55030 + '），条文级出处与核验日期不在本块重复主张 → 非数据断言。本块的承重内容是工序时点：第 5 步地漏预埋本体／法兰先于第 6 步防水层、第 7 步闭水在防水层与节点加强完成后、第 10 步（本批新增）饰面层完成后蓄水、第 11 步末端篦子在饰面之后——该序系第十二门禁 R2／R3／R4 与正向锚 P7 的取数面，故 GB 55030-2022 第6.0.12条第4款自此进入生效路径，不再是只写在口径注里的装饰性引用；「与第 7 步各为一次、不得互相替代」系本合集对两款关系的适用性判据，其真值源为同条两款文本'}],
    'prefab-bathroom-kitchen-system/reference.md#3e4d05cc8ff2f8df0f494c93e5771048df5c54bdfa917134cff41946b33611e4:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§C7 验收检查清单 序号 1：合格标准列「楼、地面最小蓄水高度不应小于20mm、蓄水时间不应少于24h」逐字对应 GB 55030-2022 第6.0.12条第1款，检查项目列「防水层完成后与饰面层完成后各做一次蓄水试验」与「两次试验不得互相替代」对应同条第4款（2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）。本批二次订正＝原把观感项「无渗漏」写进本行合格判据并随来源格挂 S1，现从来源格逐字范围撤出、在来源列显式标为 S3 观感判据，故判 A 的承重断言不含观感项；原误引的 GB 50210-2018 条文号已订正为该条，数值本体不变'}],
    'prefab-bathroom-kitchen-system/reference.md#6f4620c121deb0fbba0c69a52fc6af01e98b552e4dcf1e694f5c54564d56aa70:1': [
        {'class': 'N', 'cut': None,
         'reason': '§5.2 工序块后「工序与试验覆盖口径」注：段内不出现任何取值（20mm／24h 均未写入），内容为各步试验的覆盖对象、时点边界与两款不得互替的适用性判据，以及对 SMC 一体底盘等效关系的界定 → 非数据断言。其中「第 10 步系 GB 55030-2022 第6.0.12条第4款（全文强制）要求」的条文文本与效力真值在 §B3 闭水试验行与 §C7 序号 1 单元登记（凭据＝' + GB55030 + '，2026-09-25 官方出版物核验）；「对当时尚未形成的接口不得宣称已验」与「通水／泼水不构成蓄水试验的替代」系本合集结论表述纪律，分别随第十二门禁正向锚 P2 与 R3 的字面守，不借本条登记取得标准效力'}],

    # ── FL SKILL.md ＋ examples.md ───────────────────────────
    'prefab-floor-system/SKILL.md#ce0ec1085e075fdcc51ece20299ea6d1c3c87d5c684ff0d15b8cbe807468e930:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§4 关键约束汇总「面层平整度」行：本批把原「≤2mm/2m（架空/干法）、≤3mm/2m（浮筑砂浆面）」的单一归并写法改为逐档列值——整体面层＝表5.1.7 九档（水泥混凝土／防油渗混凝土和不发火（防爆）≤5mm、水泥砂浆／硬化耐磨 ≤4mm、普通水磨石 ≤3mm、高级水磨石／自流平／涂料／塑胶 ≤2mm）、架空活动地板 ≤2.0mm/2m（表6.1.8）、木竹面层 2.0~3.0mm/2m（表7.1.8 按品种），逐字对应 GB 50209-2010（2026-09-25 官方出版物核验，凭据＝' + GB50209 + '）。行末「陶瓷砖等其余板块面层按表6.1.8 对应档取值（本合集未逐档核验）」为未覆盖面的显式披露，其取数义务挂本批新登台账，不因本条 A 类登记宣称已核；三表逐档真值的完整面在 reference.md §A1 三行与 §A5「出处」注行单元同批登记'}],
    'prefab-floor-system/examples.md#f8a80d7bc930b06b3dd4b71728e57f8a5ca5ca4d3a7bd09c62202f99e8629a44:1': [
        {'class': 'N', 'cut': None,
         'reason': '示例 1 Step 4 的 D7 平整度核验行（表列 维度／编号／结果／说明，本表无来源列）：其中「水泥砂浆找平面按表5.1.7 ≤4mm/2m」与「瓷砖按表6.1.8 对应档」的条文级真值在 reference.md §A1 三行与 §A5「出处」注行单元登记（GB 50209-2010，2026-09-25 官方出版物核验，凭据＝' + GB50209 + '），本行为其转述与示例应用 → 非数据断言。本批二次订正＝原载「水泥砂浆面 ≤3mm」经逐表核对无该档对应（表5.1.7 砂浆档为 4mm、3mm 档系普通水磨石），现改按 ≤4mm 并保留「如需采用 ≤3mm 属企业内控加严值」的效力界定；瓷砖档「本合集未逐档核验」的缺口不因本条登记闭合'}],
    'prefab-floor-system/examples.md#5dec91806fb7630e588abc87d8b44574213fe47df9efa65c06a89e4e0ba79eb6:1': [
        {'class': 'N', 'cut': None,
         'reason': '示例 3 Step 4 的 LVT（塑胶面层）验收起（表列 验收阶段／验收标准／方法，本表无来源列）：「表面平整度 ≤2mm/2m」的条文级真值在 reference.md §A1 表5.1.7 九档行单元登记（塑胶面层档 ≤2mm，GB 50209-2010，2026-09-25 官方出版物核验，凭据＝' + GB50209 + '），本行为转述；本批二次订正＝为该值补出档位出处，并把原直写的「相邻板块高差」改按「本合集未逐档核验、按表6.1.8 对应档与设计文件取值」的指针处理 → 判非独立数据断言，未核验面不因本条登记宣称已核'}],

    # ── FL reference.md（§1.3 四行／§A1 两行／§A5 两行／§6.2 一行）──
    'prefab-floor-system/reference.md#bd0c31eb770e4de5f0ca7965de02db0c38872da991c74fa604af096d27c14d3f:1': [
        {'class': 'N', 'cut': None,
         'reason': '§1.3 分类→验证方式映射「浮筑地面」行（表列 分类／隔声验证方式／承载验证方式／平整度验证方式，本表无来源列）：本批撤除原「≤3mm/2m」归并值，改为「按面层种类取 GB 50209-2010 表5.1.7／表6.1.8 对应档（见 §A1），不用单一归并值」——本行只给验证方法与指针，不主张档位数值，逐档真值在 §A1 三行与 §A5「出处」注行单元同批登记 → 非数据断言。原归并值无标准档位对应（浮筑面层的实际面层多为水泥砂浆，标准档为 4mm），故属实质订正而非改写措辞'}],
    'prefab-floor-system/reference.md#935b00d979f3505d502bd8717901fc44682b376be53052c224bff6021d5689df:1': [
        {'class': 'N', 'cut': None,
         'reason': '§1.3「架空地面」行（本表无来源列）：本行 ≤2.0mm/2m 系对 §A1 架空活动地板档（GB 50209-2010 表6.1.8，2026-09-25 官方出版物核验，凭据＝' + GB50209 + '）的转述，且已在行内把「已核档」与「其余面层按对应档取值」显式分列——真值源面在 §A1／§A5 单元登记 → 非数据断言。分列的目的即防止转述面借已核档为未核档取得同等效力'}],
    'prefab-floor-system/reference.md#2b5f2cd0a862571f696b884458a49d590394cf0b6cbbba20ec7efdffb6d5913a:1': [
        {'class': 'N', 'cut': None,
         'reason': '§1.3「干法调平」行（本表无来源列）：本行不主张数值，仅声明「板材面层按表6.1.8 对应档取值（本合集未逐档核验）」→ 非数据断言；该未核验面的取数义务挂本批新登台账，登记本行为 N 不构成对该缺口已闭合的宣称'}],
    'prefab-floor-system/reference.md#85183d7bfcaedde8848f8921ffeb419dd70bf000b5a2c04c5ab77cba06325959:1': [
        {'class': 'N', 'cut': None,
         'reason': '§1.3「快装地面」行（本表无来源列）：「基层平整度按设计文件，面层按对应档取值」系验证路径指向，段内无具体数值与限值 → 非数据断言；本批未改写本行的判定内容，指纹变动源自同节其余三行的编辑'}],
    'prefab-floor-system/reference.md#8c883f654dcfc7f51416dd43d4bf298b8711cd86255b6b4159d40d09a614cf72:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§A1 其他性能指标「整体面层按表5.1.7 分档」行：九档逐一载明（水泥混凝土 ≤5mm/2m、防油渗混凝土和不发火（防爆）面层 ≤5mm/2m、水泥砂浆 ≤4mm/2m、硬化耐磨面层 ≤4mm/2m、普通水磨石 ≤3mm/2m、高级水磨石 ≤2mm/2m、自流平 ≤2mm/2m、涂料面层 ≤2mm/2m、塑胶面层 ≤2mm/2m）并显式写明「不存在单一归并值」，逐字对应 GB 50209-2010 表5.1.7（2026-09-25 官方出版物核验，凭据＝' + GB50209 + '）；检验方法逐字为「用 2m 靠尺和楔形塞尺检查」，在本行与 §A5 同步载明。本批改判＝原表仅举三档并以归并值概括，余档缺载会使读者按所举档位判定其他面层，故按九档全列'}],
    'prefab-floor-system/reference.md#6c101d35065741d9c0c0b9c70df95594fe476224f9db1e76994fb92cd617ac46:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§A1「木、竹面层表面平整度按表7.1.8 分档 2.0~3.0mm/2m（按品种取值）」行（本批新增）：逐字对应 GB 50209-2010 表7.1.8（2026-09-25 官方出版物核验，凭据＝' + GB50209 + '）。设立本行的直接原因＝原表把木竹面层的平整度并入整体／板块面层的单一数值，缺该档，读者会按 ≤2mm 判定木竹面层（偏松方向）；同表相邻板材高差 0.5mm 的档位真值在 §A5 表后「出处」注行单元承载，本行不重复主张'}],
    'prefab-floor-system/reference.md#3cdfa6102ef40fd12a9fb160f144ba606e64a91f6dc2fbf654b24b61d64c75c7:1': [
        {'class': 'N', 'cut': None,
         'reason': '§A5 平整度验收「表面平整度」行（表列 验收标准／检测方法／允许偏差，本表无来源列）：本批把原直写的各档数值改为「按面层种类取对应档，逐档数值见本手册 §A1 三行」的指针，检测方法列保留表5.1.7 逐字「用 2m 靠尺和楔形塞尺检查」→ 本行不主张档位数值，真值源在 §A1 三行与表后「出处」注行单元同批登记（GB 50209-2010，2026-09-25 官方出版物核验，凭据＝' + GB50209 + '）。登记为 N 系门禁结构判据（本表无来源列，来源须绑完整来源单元格），非因本行无数值'}],
    'prefab-floor-system/reference.md#d5f711fe6c1687a61126b35edcefa0162e6ce642f7b7b1c2f8998a4d77468338:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'source': ['出处：表面平整度＝GB 50209-2010 表5.1.7', '（2026-09-25 官方出版物核验）'],
         'reason': '§A5 平整度验收表后「出处」注行：承载本表全部档位的条文级出处与核验凭据——表面平整度＝GB 50209-2010 表5.1.7（整体面层九档）、表6.1.8（板块面层，经第6.1.8条、第6.7.14条引用）与表7.1.8（木、竹面层 2.0~3.0mm 按品种分档），相邻板材高差＝表7.1.8（木、竹面层 0.5mm），检验方法＝表5.1.7 逐字「用 2m 靠尺和楔形塞尺检查」，均 2026-09-25 官方出版物逐字核验（凭据＝' + GB50209 + '）。本批二次订正＝原注行只列两表，现补表7.1.8 与检验方法逐字，末句保留未覆盖面的显式披露（干法板材、陶瓷砖等板块面层的逐档数值本合集未逐档核验，其取数义务挂本批新登台账，不因本条 A 类登记宣称已核）'}],
    'prefab-floor-system/reference.md#9d682cba2a023dcfb092e4b0d3907f2eddda4e8197c92fdbe7d3e8b1bfa0b687:1': [
        {'class': 'N', 'cut': None,
         'reason': '§6.2 湿式浮筑 vs 干式浮筑对比「平整度」行（表列 维度／湿式浮筑／干式浮筑，本表无来源列）：本批把该维度名改为「平整度（本合集工艺控制值，非标准逐档值；标准档位见 §A1）」，≤3mm/2m、≤2mm/2m 系本合集两条构造路线的工艺控制目标，与 GB 50209-2010 表5.1.7 的按面层分档不同层，本行不主张标准值 → 非数据断言（判 N 系门禁结构判据：本表无来源列，来源须绑完整来源单元格；不因此免除溯源——本行已在维度名内写明「非标准逐档值」并把标准档位指向 §A1，A 类真值不借本行取得标准效力）'}],

    # ── materials-expert ＋ MI ───────────────────────────────
    'prefab-interior-materials-expert/SKILL.md#dc8d4a345f84ea79aca4c615c3264ca2350f8c11eaa2eee22d0a40f79f0d18a1:1': [
        {'class': 'N', 'cut': None,
         'reason': '「标准引用安全规则」条款号替代写法的示例句（小节内散文）：本批二次订正＝原句在括号内写死了 GB 50209-2010 第3.0.24条第3款与 GB 55030-2022 第6.0.12条第1款的条文号及两标准就蓄水高度取值不一致的裁决，与本条规则自身「条款号不确定时不写条款号」相抵触，且跨面复述同一真值（真值单源纪律），现改为指向 shared/standards-index.md 官方核验记录表 GB 55030-2022／GB 50209-2010 行的指针 → 本句不主张取值，判非数据断言。条文级真值与不一致裁决的承载面＝该行（2026-09-25 条文级核验，已另批判 N）与 成果/标准核验/ 两份核验报告'}],
    'prefab-mep-integration-system/SKILL.md#d349429d95e7d77400879b4413e6097e83f003d53929ffbc5247a660df98e86a:1': [
        {'class': 'A', 'cut': '，套管与管道间作密封处理', 'verified_on': VERIFIED,
         'source': ['（S1：GB 55030-2022 第4.6.6条第3款', '2026-09-25 官方出版物核验'],
         'reason': '§2.1 管线分离原则前段：「套管应高出装饰层完成面且不应小于 20mm」逐字对应 GB 55030-2022 第4.6.6条第3款（2026-09-25 官方出版物核验，凭据＝' + GB55030 + '）。本批二次订正＝把该款逐字对象显式限定为「穿过楼板的防水套管」，并声明该值不推广到仅穿防水层而未穿楼板的部位——ROUND 1 的写法把套管要求泛化为「穿越防水层须设套管」，属对条文适用面的外推；本批首轮订正（原以「管线不得穿越防水层」作规范禁止性条文引用）仍成立：现行已核验条文中无该禁令'},
        {'class': 'N', 'cut': None,
         'reason': '同段后半：套管与管道间密封做法声明为本合集接口控制要求（S3），并显式披露「本批未逐字核验该条其余款项」；末句为禁令引用撤除后的行为澄清，无取值主张 → 非数据断言。该条其余款项的取数义务挂本批新登台账，不因本段登记宣称已核'}],
    'prefab-mep-integration-system/SKILL.md#f199d404dcd6798c1cd0d8451ee39b57a99bfb2e0d0beb23d7af8d8fe1376bb6:1': [
        {'class': 'A', 'cut': None, 'verified_on': VERIFIED,
         'reason': '§2.5 冲突识别清单「防水冲突」行：来源格按效力分列——套管高度≥20mm 逐字对应 GB 55030-2022 第4.6.6条第3款（2026-09-25 官方出版物核验，凭据＝' + GB55030 + '），并在来源格内与本表判定列一致地把逐字对象限定为「穿过楼板的防水套管」、声明不推广到仅穿防水层部位；密封做法系合集接口控制要求（S3，D 类性质）→ 本行按承重断言（套管高度）判 A，密封做法不借本段获得 A 类效力。本批二次订正＝补写逐字对象限定，并消解与 examples.md 同点位的旧矛盾（一处称规范禁令、一处称本合集做法）'}],
    'prefab-mep-integration-system/examples.md#e5cc61c7abd3c830e58f7ba2bc92f110166c450489d4344caea91309bf1cfda4:1': [
        {'class': 'N', 'cut': None,
         'reason': '示例 4（P0 红线触发处理）整块代码示例（无来源列可绑）：块内「穿楼板的防水套管应高出装饰层完成面且高度不应小于 20mm」系对 SKILL.md §2.1／§2.5 已登记真值单元的转述（GB 55030-2022 第4.6.6条第3款，2026-09-25 官方出版物核验，凭据＝' + GB55030 + '），「套管与管道间的密封做法」标 S3 合集接口控制要求；余下四行为红线触发后的处置清单（套管预埋、密封填充、附加层覆盖根部、闭水合格后封板），系工序与检查节点，不主张标准值 → 非数据断言。本批在该块内补写的「穿楼板」限定与本技能 MI-R-P0-4 红线的表述一致：该红线是本合集的行为约束，其规范抓手是第4.6.6条第3款的套管要求，不是并不存在的「管线不得穿越防水层」禁令'}],
})


def locate(text, marker, what):
    hits = text.count(marker)
    if hits != 1:
        print(f'ERROR: marker {what} 命中 {hits} 次（须唯一）：{marker[:40]!r}')
        sys.exit(1)
    return text.index(marker)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.path.insert(0, str(REPO / '程序文件'))
    from validate_governance import data_content_units

    registry = json.loads(REGISTRY.read_bytes().decode('utf-8-sig'))
    before_r, before_b = len(registry['records']), len(registry['baseline'])
    pre_existing = set(registry['records'])

    # 1. 移除失效条目
    gone_r = gone_b = 0
    for sid in STALE_RECORD_IDS:
        if sid in registry['records']:
            del registry['records'][sid]
            gone_r += 1
        else:
            print(f'WARN: records 未命中（可能已移除）：{sid[:70]}')
    for sid in STALE_BASELINE_IDS:
        if sid in registry['baseline']:
            del registry['baseline'][sid]
            gone_b += 1
        else:
            print(f'WARN: baseline 未命中（可能已移除）：{sid[:70]}')
    print(f'移除：records {gone_r} ＋ baseline {gone_b} ＝ {gone_r + gone_b}'
          f'（声明面 {len(STALE_RECORD_IDS)} ＋ {len(STALE_BASELINE_IDS)} ＝ '
          f'{len(STALE_RECORD_IDS) + len(STALE_BASELINE_IDS)}，差额＝复跑时已移除项）')

    # 2. 现读扫描面，取本批受影响文件的单元正文
    affected = sorted({uid.split('#')[0] for uid in NEW_UNITS})
    unit_text, unit_ids = {}, set()
    for rel in affected:
        parsed = data_content_units(rel, (RUNTIME / rel).read_bytes())
        for u in parsed['units']:
            unit_ids.add(u['id'])
            unit_text[u['id']] = u['text']

    missing = [uid for uid in NEW_UNITS if uid not in unit_ids]
    for uid in missing:
        if uid not in pre_existing:
            print(f'ERROR: 单元不在扫描面：{uid[:70]}')
            sys.exit(1)
        if uid not in set(STALE_RECORD_IDS):
            print(f'ERROR: 声明的单元已离开扫描面但未列入 STALE_RECORD_IDS，'
                  f'无人负责收口：{uid[:70]}')
            sys.exit(1)
    if missing:
        print(f'跳过 {len(missing)} 条已登记但正文再变的单元'
              f'（其判定由同批 STALE 移除＋新指纹承判条目接管）')
    not_registered = sorted(set(uid for uid in unit_ids
                                if uid not in registry['records']
                                and uid not in registry['baseline']
                                and uid not in NEW_UNITS))
    if not_registered:
        for uid in not_registered:
            print(f'ERROR: 扫描面存在未登记且本批未覆盖的单元：{uid[:70]}')
        sys.exit(1)

    # 3. 按 marker 解析偏移并登记
    added = 0
    for uid, specs in NEW_UNITS.items():
        if uid in registry['records']:
            print(f'SKIP（已登记）：{uid[:70]}')
            continue
        if uid not in unit_text:
            continue  # 上一轮条目：正文已再变，判定由本批新指纹承接（missing 分支已校验）
        text = unit_text[uid]
        segments, cursor = [], 0
        for spec in specs:
            end = len(text) if spec['cut'] is None else locate(text, spec['cut'], 'cut')
            if not cursor < end <= len(text):
                print(f'ERROR: 段区间非法 {cursor}→{end}：{uid[:60]}')
                sys.exit(1)
            seg = {'start': cursor, 'end': end, 'class': spec['class'], 'reason': spec['reason']}
            if 'verified_on' in spec:
                seg['verified_on'] = spec['verified_on']
            if spec.get('source'):
                if len(spec['source']) != 2:
                    print(f'ERROR: source 须为 [起始锚, 结束锚] 两元：{uid[:60]}')
                    sys.exit(1)
                ms, me = spec['source']
                s = locate(text, ms, 'source_start')
                e = locate(text, me, 'source_end') + len(me)
                if not 0 <= s < e <= len(text):
                    print(f'ERROR: 来源片段非法：{uid[:60]}')
                    sys.exit(1)
                seg['source_spans'] = [[s, e]]
            segments.append(seg)
            cursor = end
        if cursor != len(text):
            print(f'ERROR: 末段未覆盖全文（{cursor} ≠ {len(text)}）：{uid[:60]}')
            sys.exit(1)
        registry['records'][uid] = {'segments': segments}
        added += 1
        print(f"  + [{segments[0]['class']}] {uid[:70]}…（{len(segments)} 段）")

    # 4. 棘轮核对：baseline 只减不增；records 净增须等于「新增数 − 移除数」
    assert len(registry['baseline']) <= before_b, 'baseline 出现增长，违反迁移棘轮'
    after_r = len(registry['records'])
    print(f'计数：records {before_r} → {after_r}（＋{added} −{gone_r}）；'
          f'baseline {before_b} → {len(registry["baseline"])}（−{gone_b}）')

    payload = json.dumps(registry, ensure_ascii=False, indent=2) + '\n'
    REGISTRY.write_bytes(payload.replace('\n', '\r\n').encode('utf-8'))
    print(f'写回完成（保持既有纯 CRLF 形态，字节数 {len(payload.encode("utf-8"))}）：{REGISTRY}')


if __name__ == '__main__':
    main()
