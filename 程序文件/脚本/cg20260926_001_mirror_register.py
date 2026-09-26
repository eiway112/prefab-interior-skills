# -*- coding: utf-8 -*-
"""CG-20260926-001 治理镜像面登记（第三轮）：`shared/change-governance.md` 因本批头部快照链、§九 新行与 §11.2 台账编辑再漂指纹，按 N 类逐列补登。

口径沿 CG-20260924-003 批（原工作面 `第十一批b_登记CG003镜像.py`，现已归档）：§九 表行逐列写明该列承担的治理语义；
§十一 台账行逐列同理；头部快照行逐物理行成文、行内理由绑定本行 CG 编号；裸「>」续行为结构件。
本件只登记本键，不动清单中其他键的条目，也不改 baseline 中非失效条目。

判据来源：shared/data-classification.md §一 类别定义＋§三 来源列纪律；结构约束由 validate_governance.py 检查 10 承担。
复跑安全：已登记单元跳过；失效条目按本键摘除；未预期表头／列名即停（fail-closed，不猜类别）。
残量计数不手抄：由 main() 现算打印，并与 `--data-class-only` 门禁读数对账。
"""
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(REPO / '程序文件'))
import validate_governance as vg  # noqa: E402

KEY = 'shared/change-governance.md'
MIRROR = REPO / '技能仓备份' / 'shared' / 'change-governance.md'
LIST_L1 = REPO / '_专题_技能合集策划' / '数据分类复核清单.json'

CG_ROLE = {
    '变更编号': '变更编号（本文件 §九 的行键）',
    '日期': '变更日期，属本文件成文的登记时点',
    '级别': '变更定级结论，判据取本文件 §一 定义表与 §二 流程的成文条款',
    '变更内容': '本批改动面、写面件数、判定单元数与登记计数等过程叙述',
    '影响范围': '本批零改面与终态读数的对账叙述',
    '状态': '本批授权与发布状态陈述',
}
PL_ROLE = {
    '编号': '遗留事项编号（本文件 §十一 台账的行键）',
    '事项': '遗留事项的问题描述，属本文件成文的治理叙述，不主张任何材料参数或规范限值',
    '来源登记': '指向本文件 §九 变更日志的指针编号，真值源在被指向行',
    '登记日期': '台账记账时点，属本文件成文的登记日期',
    '到期日': '台账复查时点，按 §11.1 TTL 规则由登记日期现算，属治理日程而非工程数值',
    '状态': '台账三值状态陈述（待处置／已闭合／已裁定不做），判据取本文件 §11.1 成文条款',
    '处置批次/依据': '处置结论的叙述与指向其他载体（CG 编号／PL 编号／核验报告）的指针，其真值源在被指向件',
}


def cell_segments(text):
    """按未转义的「|」切列，返回 (起始, 结束, 列号)；列号为 None 者属分隔符与空白，非单元格。"""
    pipes, i = [], 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text) and text[i + 1] == '|':
            i += 2
            continue
        if text[i] == '|':
            pipes.append(i)
        i += 1
    if not pipes or pipes[0] != 0:
        return []
    out = [(0, pipes[0] + 1, None)]
    for k in range(len(pipes) - 1):
        out.append((pipes[k] + 1, pipes[k + 1] + 1, k))
    if pipes[-1] + 1 < len(text):
        out.append((pipes[-1] + 1, len(text), None))
    return out


def header_reason(line):
    cg = re.search(r'CG-\d{8}-\d{3}', line)
    cid = cg.group(0) if cg else '无编号'
    return (f'头部「最后更新」快照行（{cid}）：本行是该批变更的过程叙述与自证计数（写面件数、门禁读数、登记计数），'
            f'并自带指向被改件的锚；行内出现的坡度值与标准号均为对被转述载体既有表述的引用，其真值源在对应技能件正文，'
            f'本文件不充当这些数值的真值源，也不据本行主张任何材料参数或规范限值。非数据断言')


def main():
    raw = MIRROR.read_bytes()
    units = vg.data_content_units(KEY, raw)['units']
    text = io.open(LIST_L1, encoding='utf-8', newline='').read()
    review = json.loads(text)
    if json.dumps(review, ensure_ascii=False, indent=2) + '\n' != text.replace('\r\n', '\n'):
        print('清单序列化往返不等（缩进／行尾形态与本脚本写回口径不一致），停')
        return 1
    observed = {u['id'] for u in units}
    before_r, before_b = len(review['records']), len(review['baseline'])
    dead_r = [k for k in list(review['records']) if k.split('#')[0] == KEY and k not in observed]
    dead_b = [k for k in list(review['baseline']) if k.split('#')[0] == KEY and k not in observed]
    for k in dead_r:
        del review['records'][k]
    for k in dead_b:
        del review['baseline'][k]
    print(f'摘失效 records {len(dead_r)}／baseline {len(dead_b)}')
    added = 0
    for u in units:
        uid = u['id']
        if uid in review['records'] or uid in review['baseline']:
            continue
        body = u['text']
        if u['kind'] == 'table_row':
            header = u['context']['header']
            role_map = CG_ROLE if header and header[0] == '变更编号' else (
                PL_ROLE if header and header[0] == '编号' else None)
            if role_map is None:
                print(f'未预期表头 {header}，停（line {u["line"]}）')
                return 1
            table = '§九 变更日志' if role_map is CG_ROLE else '§十一 遗留事项台账'
            cells = [c for c in cell_segments(body) if c[2] is not None]
            if len(cells) != len(header):
                print(f'列数 {len(cells)} ≠ 表头 {len(header)}，停（line {u["line"]}）')
                return 1
            segments = []
            for start, end, col in cell_segments(body):
                if col is None:
                    frag = body[start:end]
                    detail = ('行尾换行符' if frag.strip() == '' else
                              'Markdown 表格行首的分隔符' if frag.strip() == '|' else '分隔符与空白')
                    segments.append({'start': start, 'end': end, 'class': 'N',
                                     'reason': f'{detail}，无断言内容。非数据断言'})
                    continue
                name = header[col]
                role = role_map.get(name)
                if role is None:
                    print(f'未预期列名「{name}」，停')
                    return 1
                segments.append({'start': start, 'end': end, 'class': 'N',
                                 'reason': f'{table}列「{name}」：{role}；本列内容为本文件成文的治理陈述与可复算自证计数，'
                                           f'不主张材料本征量、规范规定限值或派生计算结果，其中所引数值与标准号均为指向其他载体的转述。非数据断言'})
        elif u['kind'] in ('raw', 'paragraph'):
            if body.strip().strip('>').strip() == '':
                segments = [{'start': 0, 'end': len(body), 'class': 'N',
                             'reason': '头部引用块链的裸「>」续行（结构件），无断言内容。非数据断言'}]
            else:
                segments = [{'start': 0, 'end': len(body), 'class': 'N',
                             'reason': header_reason(body)}]
        else:
            print(f'未预期 kind {u["kind"]}（line {u["line"]}），停')
            return 1
        cursor = 0
        for seg in segments:
            assert seg['start'] == cursor and seg['end'] > seg['start'], (u['line'], seg, cursor)
            cursor = seg['end']
        assert cursor == len(body), (u['line'], cursor, len(body))
        review['records'][uid] = {'segments': segments}
        added += 1
        print(f'  ＋ line {u["line"]} {u["kind"]} 段数 {len(segments)}')
    review['records'] = {k: review['records'][k] for k in sorted(review['records'])}
    payload = json.dumps(review, ensure_ascii=False, indent=2) + '\n'
    LIST_L1.write_bytes(payload.replace('\n', '\r\n').encode('utf-8'))
    print(f'写回完成（保持既有纯 CRLF 形态，字节数 {len(payload.encode("utf-8"))}）：{LIST_L1}')
    print(f'新登 {added} 条；records {len(review["records"])}／baseline {len(review["baseline"])}')
    return 0


sys.exit(main())
