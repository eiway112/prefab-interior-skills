# -*- coding: utf-8 -*-
"""收纳锚固承载面专项守卫（CG-20260923-005，承接 PL-061 首批静态面）。

判据（结构模式，零文件白名单）：
  R1 单点数值承载保证（`单点≥Nkg` 族）→ FAIL
  R2 通用安全系数数值化（`安全系数≥N`）→ FAIL
  R3 倍数承载保证（`≥N倍`）→ FAIL
  R4 点承载数值（`Nkg/点`）→ FAIL
  R5 标准号占据承载数值直接来源位（`S1：JGJ 145` 族字面）→ FAIL
     （判据性质：锚固承载力无普适单值，任何标准都给不出可无条件套用的单点承载值，
      故标准号不得直接充当承载数值的来源位；此为内容性质判据，与标准是否被索引收录无关）
  P  正向锚：核查入口参数、缺参停止判据、承载确定方式列名必须在场（防"撤了值也没立入口"）
负向注入以合成文本直调 check_storage_anchor，不落盘、不改任何技能件；
控制例证守卫非恒真：家具使用荷载（挂衣杆/换鞋凳 kg 值）与不带数值的"安全系数"字样不得误伤。
临时面落与本仓同级的 _tmp-scripts\\（不落 C 盘），跑后自清。
"""
import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TMP_ROOT = REPO.parent / '_tmp-scripts'
RUNTIME_DEFAULT = Path.home() / '.qoder' / 'skills' / 'prefab-storage-system'
TARGET_FILES = ('SKILL.md', 'reference.md', 'examples.md')

RULES = (
    ('R1', re.compile(r'单点\s*[≥≤><=]{1,2}\s*\d+(?:\.\d+)?\s*kg'), '单点数值承载保证'),
    ('R2', re.compile(r'安全系数[\s|]*[≥>]=?\s*\d'), '通用安全系数数值化'),
    ('R3', re.compile(r'[≥>]=?\s*\d+(?:\.\d+)?\s*倍|\d+(?:\.\d+)?\s*倍的?[^|\n]{0,10}荷载'), '倍数承载保证'),
    ('R4', re.compile(r'\d+(?:\.\d+)?\s*kg\s*/\s*点'), '点承载数值'),
    ('R5', re.compile(r'S[12]：JGJ\s?145'), '标准号占据承载数值直接来源位（承载力无普适单值）'),
)

# 正向锚：(文件, 必须存在的字面, 语义)
ANCHORS = (
    ('reference.md', '有效埋深', '锚固核查入口参数：埋深'),
    ('reference.md', '边距', '锚固核查入口参数：边距'),
    ('reference.md', '受力方向', '锚固核查入口参数：受力方向'),
    ('reference.md', '偏心', '锚固核查入口参数：偏心'),
    ('reference.md', '停止确定性承载结论', '缺参停止判据'),
    ('reference.md', '不提供通用单点承载值', '撤数值出口的明示'),
    ('reference.md', '承载确定方式', '接口表列名已改判定路径'),
    ('SKILL.md', '结构验算', '承载指标以验算为准'),
    ('SKILL.md', '停止确定性承载结论', '缺参停止判据（决策流程层）'),
    ('SKILL.md', '不得以通用倍数或单点经验值替代验算', '反通用倍数纪律'),
    ('examples.md', '结构验算确定的锚固承载要求', '示例层与正文同口径'),
)

FORBIDDEN_COLUMNS = (
    ('reference.md', '承载力参考', '接口表数值化列名回归'),
)


def read_targets(runtime_dir=None):
    root = Path(runtime_dir) if runtime_dir is not None else RUNTIME_DEFAULT
    texts = {}
    for name in TARGET_FILES:
        p = root / name
        if not p.is_file():
            texts[name] = None
        else:
            with io.open(p, encoding='utf-8') as f:
                texts[name] = f.read()
    return texts


def check_storage_anchor(texts):
    """texts: {文件名: 内容或 None}。返回 findings 列表（空＝绿）。"""
    findings = []
    for name in TARGET_FILES:
        text = texts.get(name)
        if text is None:
            findings.append(('MISSING', name, 0, '目标文件缺失或不可读'))
            continue
        for rule, pat, desc in RULES:
            for m in pat.finditer(text):
                line = text.count('\n', 0, m.start()) + 1
                findings.append((rule, name, line, f'{desc}：{m.group(0)!r}'))
        for col_file, col_literal, col_desc in FORBIDDEN_COLUMNS:
            if col_file == name:
                for m in re.finditer(col_literal, text):
                    line = text.count('\n', 0, m.start()) + 1
                    findings.append(('P-COL', name, line, f'{col_desc}：{m.group(0)!r}'))
    for name, needle, desc in ANCHORS:
        text = texts.get(name)
        if text is not None and needle not in text:
            findings.append(('P-MISS', name, 0, f'正向锚缺失（{desc}）：{needle!r}'))
    return findings


# ---------- 合成基底：与运行时同构的最小干净文本 ----------

CLEAN_REF = (
    '#### 壁挂式柜体\n\n'
    '| 技术要求 | 具体参数 | 检验方法 | 数据来源 |\n'
    '|---|---|---|---|\n'
    '| 锚固核查入口 | 锚栓类型与直径、有效埋深、边距与间距、基材类型与强度、受力方向（拉/剪）、柜体偏心与荷载分配 | 结构验算文件核查 | S1：需结构验算 |\n'
    '| 承载结论纪律 | 缺任一关键参数时停止确定性承载结论 | 计算书 | S1：需结构验算 |\n\n'
    '| 墙面类型 | 固定方法 | 承载确定方式 | 数据来源 |\n'
    '|---|---|---|---|\n'
    '| 混凝土墙 | 按锚固设计选用 | 本表不提供通用单点承载值 | S1：需结构验算 |\n'
)
CLEAN_SKILL = (
    '| 壁挂柜体承载力 | 以结构验算结论为准；不得以通用倍数或单点经验值替代验算 | 拉拔试验 | S1：需结构验算 |\n'
    '- 壁挂柜体锚固核查须齐备关键参数；缺参时停止确定性承载结论，转结构工程师验算\n'
)
CLEAN_EX = '| 固定件 | 未说明 | 须满足结构验算确定的锚固承载要求 | ❓ 待确认 |\n'

CLEAN_SET = {'SKILL.md': CLEAN_SKILL, 'reference.md': CLEAN_REF, 'examples.md': CLEAN_EX}

# 旧表原文片段（改前反例，注入必须复红）
OLD_REF_126 = '| 混凝土墙 | 膨胀螺栓/化学锚栓 | M8~M12膨胀螺栓 | 单点≥50kg（M10，C30混凝土） | 避开钢筋 | S1：JGJ 145-2013 |\n'
OLD_REF_127 = '| 实心砖墙 | 膨胀螺栓 | M8~M10 | 单点≥30kg（经验值） | 避开灰缝 | S3：经验数据 |\n'
OLD_REF_128 = '| 轻钢龙骨隔墙 | 预埋加固件 | 自攻螺钉 | 须设计确认（一般≤20kg/点） | 必须预埋 | S2：设计文件 |\n'
OLD_REF_72 = '| 安全系数 | ≥2.0（设计荷载的2倍） | 计算+试验 | S2：设计文件 |\n'
OLD_REF_71 = '| 锚固方式 | 膨胀螺栓/化学锚栓 | 拉拔试验 | S1：JGJ 145-2013 |\n'
OLD_SKILL_57 = '| 壁挂柜体承载力 | 满足设计荷载（一般≥1.5倍额定荷载），安全系数≥2.0 | 拉拔试验+荷载试验 | S2：设计文件 |\n'
OLD_EX_86 = '| 固定件 | 未说明 | 须满足设计荷载，安全系数≥2.0 | ❓ 待确认 |\n'
OLD_REF_HEADER = '| 墙面类型 | 接口方式 | 固定方法 | 承载力参考 | 注意事项 | 数据来源 |\n'


def _inject(file_name, snippet):
    out = dict(CLEAN_SET)
    out[file_name] = CLEAN_SET[file_name] + snippet
    return out


class TestCleanBaseline(unittest.TestCase):
    def test_clean_set_passes(self):
        self.assertEqual(check_storage_anchor(CLEAN_SET), [])

    def test_real_runtime_files_pass(self):
        texts = read_targets()
        findings = check_storage_anchor(texts)
        self.assertEqual(findings, [], f'运行时真实文件报红：{findings}')

    def test_real_files_are_readable(self):
        texts = read_targets()
        for name in TARGET_FILES:
            self.assertIsNotNone(texts.get(name), f'{name} 不可读，守卫空跑')
            self.assertGreater(len(texts[name]), 1000, f'{name} 内容异常偏短')


class TestNegativeInjection(unittest.TestCase):
    def _assert_rules(self, texts, expected_rules):
        findings = check_storage_anchor(texts)
        got = {f[0] for f in findings}
        for rule in expected_rules:
            self.assertIn(rule, got, f'注入未复红 {rule}：{findings}')

    def test_old_126_single_point_fires(self):
        self._assert_rules(_inject('reference.md', OLD_REF_126), {'R1', 'R5'})

    def test_old_127_brick_single_point_fires(self):
        self._assert_rules(_inject('reference.md', OLD_REF_127), {'R1'})

    def test_old_128_per_point_value_fires(self):
        self._assert_rules(_inject('reference.md', OLD_REF_128), {'R4'})

    def test_old_72_safety_factor_fires(self):
        self._assert_rules(_inject('reference.md', OLD_REF_72), {'R2'})

    def test_old_71_source_label_fires(self):
        self._assert_rules(_inject('reference.md', OLD_REF_71), {'R5'})

    def test_old_skill57_multiplier_fires(self):
        self._assert_rules(_inject('SKILL.md', OLD_SKILL_57), {'R2', 'R3'})

    def test_old_examples86_safety_factor_fires(self):
        self._assert_rules(_inject('examples.md', OLD_EX_86), {'R2'})

    def test_old_column_header_fires(self):
        self._assert_rules(_inject('reference.md', OLD_REF_HEADER), {'P-COL'})

    def test_missing_file_fires(self):
        texts = dict(CLEAN_SET)
        texts['reference.md'] = None
        got = {f[0] for f in check_storage_anchor(texts)}
        self.assertIn('MISSING', got)


class TestControlCases(unittest.TestCase):
    """控制例：证守卫非恒真、不过拦截。"""

    def test_furniture_load_values_pass(self):
        # 挂衣杆/换鞋凳为家具使用荷载（非锚固承载保证），不得误伤
        texts = dict(CLEAN_SET)
        texts['reference.md'] += (
            '| 挂衣杆 | 承载力≥50kg（均布） | 荷载试验 | S3：经验数据 |\n'
            '| 换鞋凳 | 坐面承载力≥150kg | 荷载试验 | S3：经验数据 |\n'
        )
        findings = [f for f in check_storage_anchor(texts) if f[0] in ('R1', 'R2', 'R3', 'R4')]
        self.assertEqual(findings, [])

    def test_words_without_numbers_pass(self):
        texts = dict(CLEAN_SET)
        texts['reference.md'] += '| 安全系数 | 安全系数按结构验算文件确定，不设通用值 | 计算书核查 | S1：需结构验算 |\n'
        texts['SKILL.md'] += '单点承载由结构设计确定；固定点数量按验算布置。\n'
        findings = [f for f in check_storage_anchor(texts) if f[0] in ('R1', 'R2', 'R3', 'R4')]
        self.assertEqual(findings, [])

    def test_jgj_mention_with_annotation_passes(self):
        # JGJ 145 以"验算方法依据"出现（非承载数值直接来源位）不得误伤，只有占据 S1/S2 直接来源位才红
        texts = dict(CLEAN_SET)
        texts['reference.md'] += '| 锚固方式 | 膨胀螺栓（混凝土）/化学锚栓/专用挂件 | 拉拔试验 | S2：设计文件与产品技术资料；锚固承载力系多参数派生量、无普适单值，JGJ 145-2013《混凝土结构后锚固技术规程》提供验算方法（混凝土锥体/钢材/胶筋界面/劈裂破坏及群锚折减），据以验算而非套用无条件单值 |\n'
        findings = [f for f in check_storage_anchor(texts) if f[0] == 'R5']
        self.assertEqual(findings, [])

    def test_positive_anchor_guard_has_teeth(self):
        # 撤掉停止判据锚 → 必须报 P-MISS（防"撤值不立入口"骗绿）
        texts = dict(CLEAN_SET)
        texts['reference.md'] = CLEAN_REF.replace('停止确定性承载结论', '另行处理')
        got = {f[0] for f in check_storage_anchor(texts)}
        self.assertIn('P-MISS', got)

    def test_anchor_guard_covers_all_three_files(self):
        for name in TARGET_FILES:
            findings = check_storage_anchor({**CLEAN_SET, name: '（空文件）'})
            self.assertTrue(findings, f'{name} 清空后守卫未报红')


class TestRealFileEndToEnd(unittest.TestCase):
    """端到端：真实文件副本注入旧行必红（证取数接线，不依赖合成基底）。"""

    def setUp(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix='storage_anchor_', dir=str(TMP_ROOT)))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for name in TARGET_FILES:
            shutil.copyfile(Path(RUNTIME_DEFAULT) / name, self.tmp / name)

    def test_copy_is_clean(self):
        self.assertEqual(check_storage_anchor(read_targets(self.tmp)), [])

    def test_injected_copy_fails(self):
        p = self.tmp / 'reference.md'
        text = io.open(p, encoding='utf-8').read()
        io.open(p, 'w', encoding='utf-8', newline='').write(text + OLD_REF_126)
        findings = check_storage_anchor(read_targets(self.tmp))
        got = {f[0] for f in findings}
        self.assertIn('R1', got)
        self.assertIn('R5', got)


def main(argv):
    if '--runtime-dir' in argv:
        global RUNTIME_DEFAULT
        RUNTIME_DEFAULT = Path(argv[argv.index('--runtime-dir') + 1])
    unittest.main(argv=[sys.argv[0]] + [a for a in argv[1:] if not a.startswith('--')],
                  verbosity=2)


if __name__ == '__main__':
    main(sys.argv)
