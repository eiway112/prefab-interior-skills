# -*- coding: utf-8 -*-
"""湿区构造与工序专项守卫（CG-20260924-001，承接 PL-062 静态面）。

判据（结构序＋正向锚，零文件白名单）：
  作用面＝运行时 prefab-bathroom-kitchen-system/ 三件（SKILL.md／reference.md／examples.md）
  R1 地面层序物理序：§2.2 地面层序块内 饰面板/瓷砖、保护层、防水层、找坡层、结构楼板
     五锚齐备且按自上→下行序递增（旧缺陷＝结构楼板画在找坡层之上／保护层缺席 → 红）
  R2 工序覆盖序：§5.2 工序块内 预埋本体/法兰 ＜ 防水层施工 ＜ 闭水试验 ＜ 保护层 ＜ 饰面 ＜ 末端篦子
     （旧缺陷＝闭水在找坡/地漏之前、地漏为单一末道工序 → 红）
  R3 闭水不得先于地漏节点形成：§5.2 内闭水试验行须晚于法兰/预埋本体行；无该行即红
  R4 预埋/末端分列：§5.2 须有预埋本体／法兰编号步与独立的末端篦子编号步；
     §3.2 节点表地漏行须同含「先于防水层」与「饰面完成后」
  P  正向锚（缺失报 P-MISS）：
     P1 §2.2 体系边界声明（体系边界／架空地面条件化示意／不混用字面）
     P2 §5.2 覆盖口径注记「不得宣称已验」
     P3 examples.md SMC 体系标签「仅适用 SMC 底盘一体体系」
     P4 SKILL.md 闭水时点字面「保护层与饰面施工前」
     P5 §5.2 标题体系标签「（独立防水层体系）」
     P6 数值本体保留：地面层序块找坡行须含「坡度≥1%，淋浴区≥1.5%」、
        §5.2 闭水行须含「蓄水≥20mm，≥24h」（数值本体属 PL-063 责任，本守卫防静默撤值）
  范围控制例：§5.1 SMC 工序（底盘闭水在第 5 步、无预埋步）与墙面层序块不得被 R1—R3 误伤。
负向注入以合成文本直调 check_wetzone，不落盘、不改任何技能件；
端到端以真实件副本注入旧缺陷必红。临时面落点由 gate_scratch.py 单源给出（工作区
`_整理与清理/<日期>/门禁临时面-*/`，不落 C 盘、不在工作区根新建常驻目录），跑后自清。
"""
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / '程序文件'))

import gate_scratch  # noqa: E402

TMP_ROOT = gate_scratch.scratch_dir('wetzone_construction_guard')
RUNTIME_DEFAULT = Path.home() / '.qoder' / 'skills' / 'prefab-bathroom-kitchen-system'
TARGET_FILES = ('SKILL.md', 'reference.md', 'examples.md')

FLOOR_ANCHORS = ('饰面板/瓷砖', '保护层', '防水层', '找坡层', '结构楼板')
PROC_ANCHORS = (
    ('embed', ('预埋本体', '法兰安装')),
    ('wp', ('防水层施工',)),
    ('bt', ('闭水试验',)),
    ('prot', ('保护层施工',)),
    ('fin', ('饰面板/瓷砖铺贴', '饰面')),
    ('grate', ('篦子',)),
)


def read_targets(runtime_dir=None):
    root = Path(runtime_dir) if runtime_dir is not None else RUNTIME_DEFAULT
    texts = {}
    for name in TARGET_FILES:
        p = root / name
        if p.is_file():
            with io.open(p, encoding='utf-8') as f:
                texts[name] = f.read()
        else:
            texts[name] = None
    return texts


def _fenced_all(text, marker):
    """marker 每次出现之后第一个围栏代码块内文列表（全量，防追加注入只取首块漏判）。"""
    blocks = []
    pos = 0
    while True:
        i = text.find(marker, pos)
        if i < 0:
            return blocks
        open_idx = text.find('```', i)
        if open_idx < 0:
            return blocks
        start = text.find('\n', open_idx)
        if start < 0:
            return blocks
        close = text.find('```', start + 1)
        if close < 0:
            return blocks
        blocks.append(text[start + 1:close])
        pos = close + 3


def floor_blocks(text):
    return _fenced_all(text, '地面层序（剖面自上→下）')


def wall_block(text):
    blocks = _fenced_all(text, '墙面（湿区）层序')
    return blocks[0] if blocks else None


def proc_blocks(text):
    return _fenced_all(text, '### 5.2')


def _line_idx(block, needles):
    """块内首行命中 needles 任一者之行序；无命中返回 None。"""
    if block is None:
        return None
    for n, line in enumerate(block.split('\n')):
        if any(k in line for k in needles):
            return n
    return None


def _layer_idx(block, layer):
    """层序块内首个以 [层名 起首的行序（结构匹配，不吃行内条件句子串）；无命中返回 None。"""
    if block is None:
        return None
    for n, line in enumerate(block.split('\n')):
        if line.lstrip().startswith('[' + layer):
            return n
    return None


def check_wetzone(texts):
    """texts: {文件名: 内容或 None}。返回 findings 列表（空＝绿）。"""
    findings = []
    ref = texts.get('reference.md')
    skill = texts.get('SKILL.md')
    ex = texts.get('examples.md')
    for name, text in (('SKILL.md', skill), ('reference.md', ref), ('examples.md', ex)):
        if text is None:
            findings.append(('MISSING', name, 0, '目标文件缺失或不可读'))
    if ref is None:
        return findings

    fbs = floor_blocks(ref)
    if not fbs:
        findings.append(('R1', 'reference.md', 0, '地面层序块缺失（标记或围栏不存在）'))
    for fb in fbs:
        idx = [(a, _layer_idx(fb, a)) for a in FLOOR_ANCHORS]
        missing = [a for a, i in idx if i is None]
        if missing:
            findings.append(('R1', 'reference.md', 0, f'地面层序物理序锚缺失：{missing}'))
        else:
            vals = [i for _, i in idx]
            if vals != sorted(vals) or len(set(vals)) != len(vals):
                findings.append(('R1', 'reference.md', 0,
                                 f'地面层序物理序倒置：{[(a, i) for (a, _), i in zip(idx, vals)]}'))
        slope_line = _layer_idx(fb, '找坡层')
        if slope_line is not None:
            line = fb.split('\n')[slope_line]
            if '坡度≥1%，淋浴区≥1.5%' not in line:
                findings.append(('P-MISS', 'reference.md', 0, 'P6 找坡行数值本体缺失（坡度≥1%，淋浴区≥1.5%）'))

    pbs = proc_blocks(ref)
    if not pbs:
        findings.append(('R2', 'reference.md', 0, '§5.2 工序块缺失'))
    for pb in pbs:
        pos = {key: _line_idx(pb, needles) for key, needles in PROC_ANCHORS}
        missing = [k for k, i in pos.items() if i is None]
        if missing:
            findings.append(('R2', 'reference.md', 0, f'工序覆盖序锚缺失：{missing}'))
        else:
            order = ['embed', 'wp', 'bt', 'prot', 'fin', 'grate']
            vals = [pos[k] for k in order]
            if vals != sorted(vals) or len(set(vals)) != len(vals):
                findings.append(('R2', 'reference.md', 0,
                                 f'工序覆盖序倒置：{list(zip(order, vals))}'))
        bt = pos.get('bt')
        node = pos.get('embed')
        if bt is None or node is None or bt <= node:
            findings.append(('R3', 'reference.md', 0,
                             f'闭水试验未晚于地漏法兰/预埋本体形成（bt={bt}, node={node}）'))
        if pos.get('embed') is None or pos.get('grate') is None or pos['embed'] == pos['grate']:
            findings.append(('R4', 'reference.md', 0, '预埋本体/法兰与末端篦子未分列为独立工序步'))
        slope_line = _line_idx(pb, ('找坡层施工',))
        if slope_line is not None and '坡度≥1%，淋浴区≥1.5%' not in pb.split('\n')[slope_line]:
            findings.append(('P-MISS', 'reference.md', 0, 'P6 工序找坡行数值本体缺失（坡度≥1%，淋浴区≥1.5%）'))
        bt_line = _line_idx(pb, ('闭水试验',))
        if bt_line is not None and '蓄水≥20mm，≥24h' not in pb.split('\n')[bt_line]:
            findings.append(('P-MISS', 'reference.md', 0, 'P6 闭水行数值本体缺失（蓄水≥20mm，≥24h）'))

    node_rows = [ln for ln in ref.split('\n') if ln.startswith('| 地漏周围 |')]
    if not node_rows:
        findings.append(('R4', 'reference.md', 0, '§3.2 节点表地漏行缺失'))
    elif any('先于防水层' not in ln or '饰面完成后' not in ln for ln in node_rows):
        findings.append(('R4', 'reference.md', 0, '节点表地漏行未分列预埋/末端时序'))

    anchors = (
        ('P1', 'reference.md', ref, '体系边界'),
        ('P1', 'reference.md', ref, '架空地面体系湿区（条件化示意'),
        ('P1', 'reference.md', ref, '不与本节层序混用'),
        ('P2', 'reference.md', ref, '不得宣称已验'),
        ('P5', 'reference.md', ref, '### 5.2 干法装配式卫浴典型工序（独立防水层体系）'),
        ('P3', 'examples.md', ex or '', '仅适用 SMC 底盘一体体系'),
        ('P4', 'SKILL.md', skill or '', '保护层与饰面施工前'),
    )
    for rule, name, hay, needle in anchors:
        if needle not in hay:
            findings.append(('P-MISS', name, 0, f'{rule} 正向锚缺失：{needle!r}'))
    return findings


# ---------- 合成基底：与修后运行时同构的最小干净文本 ----------

CLEAN_REF = (
    '### 2.2 干法装配式卫浴防水构造（独立防水层体系）\n\n'
    '> **体系边界**：本节层序仅适用于干法独立防水层体系；SMC 底盘一体体系见 §2.1 与 §5.1，不与本节层序混用；'
    '架空地面体系湿区（条件化示意）防水面以设计文件为准。\n\n'
    '地面层序（剖面自上→下）：\n\n'
    '```\n'
    '[饰面板/瓷砖]（表面坡向地漏）\n'
    '    ↓ 粘结层／二次找坡\n'
    '[保护层]（闭水试验合格后施工）\n'
    '    ↓\n'
    '[防水层（聚氨酯涂膜）]（翻包地漏法兰、管根、阴角）\n'
    '    ↓\n'
    '[找坡层／一次找坡]（坡度≥1%，淋浴区≥1.5%，坡向地漏）\n'
    '    ↓\n'
    '[结构楼板]\n'
    '```\n\n'
    '墙面（湿区）层序（剖面自外→内）：\n\n'
    '```\n'
    '[饰面板/瓷砖]（粘结层）\n'
    '    ↓\n'
    '[防水层]\n'
    '    ↓\n'
    '[基层板（硅酸钙板/水泥纤维板）]\n'
    '```\n\n'
    '| 节点部位 | 构造要求 | 常见失效模式 |\n'
    '|---------|---------|------------|\n'
    '| 地漏周围 | 地漏预埋本体／法兰先于防水层施工安装，防水层翻包法兰并密封；末端篦子于饰面完成后安装 | 密封老化 |\n\n'
    '### 5.1 SMC整体卫浴典型工序\n\n'
    '```\n'
    '3. 防水底盘就位、调平、固定\n'
    '5. 底盘闭水试验（蓄水≥20mm，≥24h）\n'
    '```\n\n'
    '### 5.2 干法装配式卫浴典型工序（独立防水层体系）\n\n'
    '```\n'
    '4. 找坡层施工（一次找坡，坡度≥1%，淋浴区≥1.5%，坡向地漏）\n'
    '5. 地漏预埋本体／法兰安装、管根与阴角节点处理\n'
    '6. 防水层施工（涂膜/卷材）\n'
    '7. 防水层闭水试验（蓄水≥20mm，≥24h；覆盖防水层与法兰、管根、阴角节点）\n'
    '8. 防水保护层施工\n'
    '9. 饰面板/瓷砖铺贴（表面坡向地漏）\n'
    '10. 地漏末端篦子安装\n'
    '```\n\n'
    '> **工序与试验覆盖口径**：第 7 步闭水试验覆盖对象为防水层及法兰、管根、阴角节点；'
    '对当时尚未形成的接口（饰面层、地漏末端篦子）不得宣称已验。\n'
)
CLEAN_SKILL = '□ 4. 闭水试验验证：蓄水≥20mm，时间≥24h；时点为防水层与节点加强完成后、保护层与饰面施工前\n'
CLEAN_EX = '> 本例闭水时点与地漏接口仅适用 SMC 底盘一体体系；干法体系见 reference.md §5.2。\n'

CLEAN_SET = {'SKILL.md': CLEAN_SKILL, 'reference.md': CLEAN_REF, 'examples.md': CLEAN_EX}

# 旧缺陷原文片段（改前反例，注入必须复红）
OLD_DIAG = (
    '地面层序（剖面自上→下）：\n\n'
    '```\n'
    '[饰面板/瓷砖]\n'
    '    ↓ 粘结/干挂\n'
    '[基层板（硅酸钙板/水泥纤维板）]\n'
    '    ↓ 满涂/粘贴\n'
    '[防水层（聚氨酯涂膜/聚合物水泥防水涂料）]\n'
    '    ↓ 基层处理\n'
    '[结构楼板/架空地面]\n'
    '    ↓\n'
    '[排水坡度找坡层]（坡度≥1%，淋浴区≥1.5%）\n'
    '```\n'
)
OLD_PROC = (
    '### 5.2 干法装配式卫浴典型工序\n\n'
    '```\n'
    '4. 防水层施工（涂膜/卷材）\n'
    '5. 防水层闭水试验（蓄水≥20mm，≥24h）\n'
    '6. 防水保护层施工\n'
    '7. 找坡层施工（坡度≥1%，淋浴区≥1.5%）\n'
    '8. 饰面板/瓷砖铺贴\n'
    '9. 地漏安装\n'
    '```\n'
)
OLD_NODE_ROW = '| 地漏周围 | 地漏法兰与底盘/防水层密封连接，周围50mm范围加强 | 密封老化、法兰松动 |\n'


def _inject(file_name, snippet):
    out = dict(CLEAN_SET)
    out[file_name] = CLEAN_SET[file_name] + snippet
    return out


class TestCleanBaseline(unittest.TestCase):
    def test_clean_set_passes(self):
        self.assertEqual(check_wetzone(CLEAN_SET), [])

    def test_real_runtime_files_pass(self):
        findings = check_wetzone(read_targets())
        self.assertEqual(findings, [], f'运行时真实文件报红：{findings}')

    def test_real_files_are_readable(self):
        texts = read_targets()
        for name in TARGET_FILES:
            self.assertIsNotNone(texts.get(name), f'{name} 不可读，守卫空跑')
            self.assertGreater(len(texts[name]), 1000, f'{name} 内容异常偏短')


class TestNegativeInjection(unittest.TestCase):
    def _rules(self, texts):
        return {f[0] for f in check_wetzone(texts)}

    def test_old_inverted_diagram_fires(self):
        got = self._rules(_inject('reference.md', OLD_DIAG))
        self.assertIn('R1', got)

    def test_old_process_fires(self):
        got = self._rules(_inject('reference.md', OLD_PROC))
        self.assertIn('R2', got)
        self.assertIn('R3', got)

    def test_old_node_row_fires(self):
        texts = dict(CLEAN_SET)
        texts['reference.md'] = CLEAN_REF.replace(
            '| 地漏周围 | 地漏预埋本体／法兰先于防水层施工安装，防水层翻包法兰并密封；末端篦子于饰面完成后安装 | 密封老化 |',
            OLD_NODE_ROW.strip())
        self.assertIn('R4', self._rules(texts))

    def test_missing_file_fires(self):
        texts = dict(CLEAN_SET)
        texts['reference.md'] = None
        self.assertIn('MISSING', self._rules(texts))


class TestControlCases(unittest.TestCase):
    """控制例：证守卫非恒真、范围不过拦。"""

    def test_smc_process_outside_scope_not_fired(self):
        # §5.1 型 SMC 工序（底盘闭水早、无预埋步）追加在 §5.2 之外不得触发 R2/R3
        texts = dict(CLEAN_SET)
        texts['reference.md'] += (
            '### 5.3 某底盘体系工序\n\n```\n'
            '4. 底盘安装\n5. 底盘闭水试验（蓄水≥20mm，≥24h）\n6. 墙板安装\n```\n')
        got = {f[0] for f in check_wetzone(texts)}
        self.assertNotIn('R2', got)
        self.assertNotIn('R3', got)

    def test_wall_block_not_confused_with_floor(self):
        # 墙面层序块不含五锚，不得被当作地面层序块判红；删地面块才红
        wb = wall_block(CLEAN_REF)
        self.assertIsNotNone(wb)
        self.assertNotIn('结构楼板', wb)
        texts = dict(CLEAN_SET)
        texts['reference.md'] = CLEAN_REF.replace(
            '地面层序（剖面自上→下）：', '地面层序（已删除）：')
        self.assertIn('R1', {f[0] for f in check_wetzone(texts)})

    def test_dropped_slope_values_fire(self):
        # 撤数值本体（PL-063 责任面）须报 P-MISS，防静默撤值骗绿
        texts = dict(CLEAN_SET)
        texts['reference.md'] = CLEAN_REF.replace('（坡度≥1%，淋浴区≥1.5%，坡向地漏）', '（坡向地漏）')
        got = {f[0] for f in check_wetzone(texts)}
        self.assertIn('P-MISS', got)

    def test_positive_anchor_has_teeth(self):
        texts = dict(CLEAN_SET)
        texts['reference.md'] = CLEAN_REF.replace('不得宣称已验', '另行说明')
        self.assertIn('P-MISS', {f[0] for f in check_wetzone(texts)})

    def test_anchor_guard_covers_all_three_files(self):
        for name in TARGET_FILES:
            findings = check_wetzone({**CLEAN_SET, name: '（空文件）'})
            self.assertTrue(findings, f'{name} 清空后守卫未报红')


class TestRealFileEndToEnd(unittest.TestCase):
    """端到端：真实件副本干净、注入旧缺陷必红（证取数接线）。"""

    def setUp(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix='wetzone_guard_', dir=str(TMP_ROOT)))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for name in TARGET_FILES:
            shutil.copyfile(Path(RUNTIME_DEFAULT) / name, self.tmp / name)

    def test_copy_is_clean(self):
        self.assertEqual(check_wetzone(read_targets(self.tmp)), [])

    def test_injected_old_diagram_fails(self):
        p = self.tmp / 'reference.md'
        with io.open(p, encoding='utf-8') as f:
            text = f.read()
        with io.open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(text + OLD_DIAG)
        self.assertIn('R1', {f[0] for f in check_wetzone(read_targets(self.tmp))})

    def test_injected_old_process_fails(self):
        p = self.tmp / 'reference.md'
        with io.open(p, encoding='utf-8') as f:
            text = f.read()
        with io.open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(text + OLD_PROC)
        got = {f[0] for f in check_wetzone(read_targets(self.tmp))}
        self.assertIn('R2', got)
        self.assertIn('R3', got)


def main(argv):
    args = list(argv[1:])
    if '--runtime-dir' in args:
        i = args.index('--runtime-dir')
        global RUNTIME_DEFAULT
        RUNTIME_DEFAULT = Path(args[i + 1])
        del args[i:i + 2]
    unittest.main(argv=[sys.argv[0]] + [a for a in args if not a.startswith('--')],
                  verbosity=2)


if __name__ == '__main__':
    main(sys.argv)
