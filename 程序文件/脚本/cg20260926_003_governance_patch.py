# -*- coding: utf-8 -*-
"""CG-20260926-003 治理登记面写入（P1 线收尾补登批）：头部快照链轮换＋§九 新行。

写面对象＝`成果/2026-09-25_项目全面审视与下一阶段执行方案.md` §五「执行重点」的补登段（该节自设
「需要外部条件的工作必须明确等待对象」的要求，但等待对象从未成文）。本批零动技能件正文与台账状态。

落点依据＝工作区《_管理规范/文件与项目管理规范》§3.7（可复用 .py → `程序文件/脚本/`）＋C2 程序文件隔离。
安全口径（《登记面长行拼接安全》纪律）：每处编辑先断言唯一锚命中数＝1 再写；写后自检
（新行存在、旧行降级且唯一、§九 行列数与表头相符、CR 计数不变、纯 LF 保持）。
复跑幂等：本批行已登记即原样退出。
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / '程序文件'))
import validate_governance as vg  # noqa: E402  （只借 md_cells 与表头现读做写后自检）

CG = REPO / '_专题_技能合集策划' / 'change-governance.md'
assert CG.exists(), f'治理面未找到：{CG}'

PREV = 'CG-20260926-002'
OLD_HEAD_ANCHOR = f'> **最后更新**：2026-09-26，{PREV}（'
DEMOTED_ANCHOR = '> **此前更新（历史快照）**：2026-09-26，CG-20260926-002（'

NEW_HEAD = (
    '> **最后更新**：2026-09-26，CG-20260926-003（**C 级登记批**，P1 线收尾补登）：'
    '`成果/2026-09-25_项目全面审视与下一阶段执行方案.md` §五「执行重点」按**该节自设要求**'
    '（「需要外部条件的工作必须明确等待对象」）补登六条工作线的逐线等待对象与到位后可自开动作表——'
    '原文两段判断按快照纪律**不改写**，以「执行重点更新（2026-09-26）」追加；'
    '表内显式标出两条无外部输入即可推进的半面（声学模型验证的方法审查面、冻结机制修订的加载关系机算面），'
    '并把「总单↔台账↔执行记录对账」线的闭合事实（CG-20260926-002）登记入表；'
    '新表**不抄 PL 名单、不填任何计数**（待处置项／到期日真值源＝本文件 §11.2 现读，抄入即成第二份台账）。'
    '零动技能件正文、零动台账状态与列结构、零改校验器与门禁判据。'
    '§九 CG 行 146→**147**；台账 **82 行不变**、状态分布 待处置 20／已闭合 61／已裁定不做 1。'
    '历史快照保留如下，终态以本批执行记录为准。\n>\n'
)

CG_ROW = (
    '| CG-20260926-003 | 2026-09-26 | '
    'C 级（定级依据＝§一 C 级「文档结构优化、措辞改善、格式统一等不影响功能和准确性的变更」——'
    '写面系既有执行方案载体补登一段自设要求从未成文的启动判据，零动标准限值／检测数值／经验域／公式常数、'
    '零动技能件正文、零动台账状态与列结构、零改判据本体，故不触 B 级「新增内容、修正错误」；'
    '级别不继承前批，按§五「级别不继承登记批」独立定级） | '
    '① 补登判据＝`成果/2026-09-25_项目全面审视与下一阶段执行方案.md` §五 新增「执行重点更新（2026-09-26，CG-20260926-003，C 级）」'
    '六行表（工作线按 §五 原表行序｜现态｜等待对象（谁在动）｜到位后我方可自开的动作），'
    '补齐该节 :151 自身要求「需要外部条件的工作必须明确等待对象」却从未落文的执行面；'
    '② 快照纪律＝原 :149／:151 两段作为交付当时判断**保留不改写**，新表以追加形态写入，'
    '且判据列（责任与必要输入／最小交付／验收标准／停止条件）声明以 §五 原表为唯一来源、新表不重复承载；'
    '③ 无外部依赖半面显式化＝纠正「整线挂缺外部真值」的读法：声学模型验证在无检测数据时按该行停止条件'
    '自身许可仅做方法审查（校准与评价样本分离、评价量／频段／试验条件可比），'
    '冻结机制修订的「实际加载关系」属本仓可现读面（唯排除项是否影响行为的裁定须发起人定级，'
    '其停止条件＝无法解释即不得直接豁免）；'
    '④ 一线闭合登记＝「总单与实际成果对账」线转已闭合（CG-20260926-002，最小交付落在总单 §十七／§十八），'
    '该线不设续批；⑤ 反台账复制条款＝新表明写不抄 PL 名单与计数，真值源指向 §11.2 | '
    '影响范围＝`成果/` 单件追加（该载体不属三层声明治理件、不入 `sync_skill_backup.py` 同步范围，'
    '亦不在检查 10 扫描面 57 键内——键集现读不含 `成果/`、`文档/`、`记录/`、`CHANGELOG.md`，'
    '故本批不触发残量登记）；本文件侧仅头部快照链与 §九 一行。'
    '零改面＝15 技能目录全部内容件、标准限值／检测数值／经验域／公式常数、契约／红线／索引本体／'
    '分类判据本体、`validate_governance.py` 与十二门禁判据、§九 历史 CG 行、§11.2 台账全部 82 行、'
    '冻结基准 v1—v3、`素材/`。回滚＝`git checkout HEAD -- 成果/2026-09-25_项目全面审视与下一阶段执行方案.md '
    '_专题_技能合集策划/change-governance.md`，成本低 | '
    '已登记（发起人 2026-09-26 指令「开。请根据优先级启动，我需要开新线，本轮已经压缩多次」；'
    '本批系把上一轮只存在于对话里的「两条新线怎么开」结论改写为仓内载体可核事实，'
    '不新增任何未经请求的工作线，C 级按§二 由发起人直接执行并记录变更日志）；'
    '§九 CG 行 146→**147**、台账 **82 行不变**且状态分布零改；'
    '写面与验收读数以 记录/2026-09-26_CG-20260926-003_逐线等待对象补登批执行记录.md 为准；'
    'commit 随本批（T1 免逐次授权），push 不随批（T2，须发起人当轮明文整句） |\n'
)


def main():
    raw = CG.read_bytes()
    text = raw.decode('utf-8')
    cr_before, lf_before = text.count('\r'), text.count('\n')
    if cr_before:
        print('本文件含 CR，与既有纯 LF 形态不符，停')
        return 1
    if '| CG-20260926-003 | ' in text:
        print('已登记（§九 CG-20260926-003 行存在），幂等退出')
        return 0
    if text.count(OLD_HEAD_ANCHOR) != 1:
        print(f'头部锚命中 {text.count(OLD_HEAD_ANCHOR)}，非唯一，停')
        return 1

    out = text.replace(OLD_HEAD_ANCHOR, DEMOTED_ANCHOR, 1)
    out = out.replace(DEMOTED_ANCHOR, NEW_HEAD + DEMOTED_ANCHOR, 1)

    lines = out.split('\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(f'| {PREV} | ')]
    if len(idx) != 1:
        print(f'§九 {PREV} 行命中 {len(idx)}，停')
        return 1
    header = next((h for h in lines[:idx[0]] if h.startswith('| 变更编号 |')), None)
    if header is None:
        print('§九 表头未现读找到，停（不猜列数）')
        return 1
    ncol = len(vg.md_cells(header))
    if len(vg.md_cells(CG_ROW.rstrip('\n'))) != ncol:
        print(f'本批行列数 {len(vg.md_cells(CG_ROW.rstrip(chr(10))))} ≠ 表头 {ncol}，停')
        return 1
    lines.insert(idx[0] + 1, CG_ROW.rstrip('\n'))
    out = '\n'.join(lines)

    CG.write_bytes(out.encode('utf-8'))
    check = CG.read_bytes().decode('utf-8')
    now = [l for l in check.split('\n') if l.startswith('| CG-20260926-003 | ')]
    print('写入完成：')
    print(f'  头部新行存在＝{"> **最后更新**：2026-09-26，CG-20260926-003（" in check}')
    print(f'  旧行已降级且唯一＝{check.count(DEMOTED_ANCHOR) == 1}')
    print(f'  §九 新行唯一＝{check.count("| CG-20260926-003 | ") == 1}')
    print(f'  §九 新行列数＝{len(vg.md_cells(now[0])) if now else "缺行"}（表头 {ncol}）')
    print(f'  收尾竖线在位＝{now[0].rstrip().endswith("|") if now else "缺行"}')
    print(f'  行数 {lf_before} → {check.count(chr(10))}（预期 +3＝头部新增两物理行＋§九 新行一行）')
    print(f'  CR 计数＝{check.count(chr(13))}（预期 0）')
    print(f'  字节 {len(raw)} → {len(out.encode("utf-8"))}')
    return 0


sys.exit(main())
