import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import validate_governance as vg


class DataClassTest(unittest.TestCase):
    def inspect(self, text, kind='N', source=None, date=None):
        files = {'skill/reference.md': text.encode()}
        units = vg.data_content_units('skill/reference.md', files['skill/reference.md'])['units']
        review = {'version': 1, 'records': {}}
        for unit in units:
            segment = {'start': 0, 'end': len(unit['text']), 'class': kind, 'reason': '合成测试断言'}
            if unit['kind'] in ('heading', 'table_header'):
                segment['class'] = 'N'
            if source is not None and source in unit['text']:
                start = unit['text'].index(source)
                segment['source_spans'] = [[start, start + len(source)]]
            if date is not None:
                segment['verified_on'] = date
            review['records'][unit['id']] = {'segments': [segment]}
        return files, review

    def run_check(self, files, review):
        return vg.check_data_class_consistency(files, review, vg.Report())

    def codes(self, result):
        return {item['code'] for item in result['findings']}

    def test_positive_nondata(self):
        result = self.run_check(*self.inspect('这是操作入口，不含技术数据。'))
        self.assertEqual(result['counts']['fail'], 0)
        self.assertEqual(result['counts']['reviewed'], 1)

    def test_bc_s1_always_fails(self):
        for kind in ('B', 'C'):
            for source in ('S1', '**S1**', 'Ｓ１', 'S1–S4'):
                with self.subTest(kind=kind, source=source):
                    result = self.run_check(*self.inspect(f'| 参数 | 来源 |\n|---|---|\n| E=2 GPa | {source} |', kind))
                    self.assertIn('BC_SOURCE_LABEL', self.codes(result))

    def test_bc_standard_families(self):
        for source in ('GB/T 9775-2025', 'JC/T 564.1-2018', 'EN 520', 'ISO 1234', 'ASTM D638', 'T/CECS 123-2020', '08J931'):
            with self.subTest(source=source):
                result = self.run_check(*self.inspect('弹性模量E=2 GPa，来源：' + source, 'B', source))
                self.assertIn('BC_SOURCE_LABEL', self.codes(result))

    def test_method_reference_not_a_source_exemption(self):
        text = '| 参数 | 数据来源 | 检测方法 |\n|---|---|---|\n| E=2 GPa | 文献甲与乙 | GB/T 50081 |'
        result = self.run_check(*self.inspect(text, 'B'))
        self.assertNotIn('BC_SOURCE_LABEL', self.codes(result))
        bad = text.replace('文献甲与乙', 'GB/T 50081')
        result = self.run_check(*self.inspect(bad, 'B'))
        self.assertIn('BC_SOURCE_LABEL', self.codes(result))

    def test_a_missing_date_warn_only(self):
        result = self.run_check(*self.inspect('限值依据GB 55016-2021', 'A', 'GB 55016-2021'))
        self.assertEqual(result['counts']['fail'], 0)
        self.assertEqual(result['counts']['warn'], 1)
        self.assertIn('A_VERIFY_DATE', self.codes(result))

    def test_a_invalid_and_future_dates_warn(self):
        for date in ('2020-02-30', '9999-01-01', '2020-1-1', 20200101):
            result = self.run_check(*self.inspect('依据GB 55016-2021', 'A', 'GB 55016-2021', date))
            self.assertEqual(result['counts']['fail'], 0)
            self.assertIn('A_VERIFY_DATE', self.codes(result))

    def test_a_existing_date_does_not_imply_expiry(self):
        result = self.run_check(*self.inspect('依据GB 55016-2021', 'A', 'GB 55016-2021', '2020-01-01'))
        self.assertEqual(result['counts']['fail'], 0)
        self.assertEqual(result['counts']['warn'], 0)

    def test_s10_not_s1(self):
        result = self.run_check(*self.inspect('参数来源样本S10', 'B', '样本S10'))
        self.assertNotIn('BC_SOURCE_LABEL', self.codes(result))

    def test_unknown_without_number_or_source_is_not_silently_omitted(self):
        result = self.run_check({'new.md': '取值见未说明的附件。'.encode()}, {'version': 1, 'records': {}})
        self.assertIn('UNREVIEWED', self.codes(result))
        self.assertEqual(result['counts']['units'], 1)
        self.assertEqual(result['counts']['confirmed_mislabel_findings'], 0)
        self.assertEqual(result['counts']['missing_source_findings'], 0)

    def test_no_source_data_fails_after_classification(self):
        result = self.run_check(*self.inspect('弹性模量约2 GPa', 'B'))
        self.assertIn('MISSING_SOURCE', self.codes(result))

    def test_placeholder_source_fails(self):
        for value in ('—', '-', '未提供', '待补', '无'):
            result = self.run_check(*self.inspect('| 数值 | 来源 |\n|---|---|\n| 2 | ' + value + ' |', 'B'))
            self.assertIn('MISSING_SOURCE', self.codes(result))

    def test_changed_content_invalidates_review(self):
        files, review = self.inspect('参数E=2 GPa')
        files['skill/reference.md'] = '参数E=3 GPa'.encode()
        result = self.run_check(files, review)
        self.assertTrue({'STALE_REVIEW', 'UNREVIEWED'} <= self.codes(result))

    def test_changed_heading_invalidates_child_review(self):
        files, review = self.inspect('# 实测数据\n\n参数E=2 GPa')
        files['skill/reference.md'] = files['skill/reference.md'].replace('实测'.encode(), '计算'.encode())
        result = self.run_check(files, review)
        self.assertEqual(result['counts']['unreviewed'], 2)

    def test_changed_table_header_invalidates_row_review(self):
        files, review = self.inspect('| 参数 | 来源 |\n|---|---|\n| 2 | 论文 |')
        files['skill/reference.md'] = files['skill/reference.md'].replace('参数'.encode(), '限值'.encode())
        result = self.run_check(files, review)
        self.assertEqual(result['counts']['unreviewed'], 2)

    def test_added_duplicate_requires_new_review(self):
        files, review = self.inspect('同一说明')
        files['skill/reference.md'] = '同一说明\n\n同一说明'.encode()
        result = self.run_check(files, review)
        self.assertIn('UNREVIEWED', self.codes(result))

    def test_table_blank_break_becomes_visible_paragraph(self):
        text = '| 参数 | 来源 |\n|---|---|\n| 1 | 论文 |\n\n| 2 | S1 |'
        result = self.run_check(*self.inspect(text))
        self.assertEqual(result['counts']['fail'], 0)
        self.assertTrue(any('| 2 | S1 |' in u['text'] and u['kind'] == 'paragraph' for u in result['units']))
        result = self.run_check({'x.md': text.encode()}, {'version': 1, 'records': {}})
        self.assertEqual(result['counts']['unreviewed'], 3)

    def test_escaped_pipe_and_extra_cells_preserve_raw_text(self):
        text = '| 参数 | 来源 |\n|---|---|\n| E\\|ρ | 文献 |'
        result = self.run_check(*self.inspect(text))
        self.assertEqual(result['counts']['fail'], 0)
        result = self.run_check(*self.inspect(text.replace('E\\|ρ', 'E|ρ')))
        self.assertEqual(result['counts']['fail'], 0)
        self.assertIn('E|ρ', result['units'][-1]['text'])
        self.assertIn('文献', result['units'][-1]['text'])

    def test_fenced_payload_is_reviewed(self):
        text = '```json\n{"参数": 7}\n```\n'
        result = self.run_check({'sample.md': text.encode()}, {'version': 1, 'records': {}})
        self.assertIn('UNREVIEWED', self.codes(result))
        self.assertEqual(result['units'][0]['text'], text)
        result = self.run_check(*self.inspect('```\n未闭合'))
        self.assertEqual(result['counts']['fail'], 0)
        self.assertEqual(result['units'][0]['kind'], 'code')
        result = self.run_check(*self.inspect('```\nE=2 GPa', 'B'))
        self.assertIn('MISSING_SOURCE', self.codes(result))

    def test_span_gaps_overlap_and_tail_fail(self):
        files, review = self.inspect('完整内容')
        key = next(iter(review['records']))
        for start, end in ((1, 4), (0, 3), (0, 5), (True, 4)):
            altered = copy.deepcopy(review)
            altered['records'][key]['segments'][0].update(start=start, end=end)
            self.assertIn('SEGMENT_COVERAGE', self.codes(self.run_check(files, altered)))

    def test_mixed_class_segments(self):
        text = '规范GB 55016；物理数据取文献'
        files, review = self.inspect(text)
        key = next(iter(review['records']))
        cut = text.index('物理')
        review['records'][key]['segments'] = [
            {'start': 0, 'end': cut, 'class': 'A', 'reason': '规范断言', 'source_spans': [[2, 10]], 'verified_on': '2020-01-01'},
            {'start': cut, 'end': len(text), 'class': 'B', 'reason': '物理断言', 'source_spans': [[len(text)-2, len(text)]]}]
        result = self.run_check(files, review)
        self.assertEqual(result['counts']['fail'], 0)

    def test_malformed_review_fails(self):
        for review in (None, [], {'version': 2, 'records': {}}, {'version': 1, 'records': {}, 'exempt': '*'}):
            result = self.run_check({'x.md': b'x'}, review)
            self.assertIn('REVIEW_SCHEMA', self.codes(result))

    def test_empty_and_invalid_encoding_fail(self):
        for files, code in (({}, 'EMPTY'), ({'x.md': b'\xff'}, 'ENCODING'), ({'x.md': b'\n---\n'}, 'EMPTY')):
            self.assertIn(code, self.codes(self.run_check(files, {'version': 1, 'records': {}})))

    def test_complete_content_lines_accounted(self):
        text = '# 标题\n\n文本\n继续\n\n| 列 |\n|---|\n| 3 |\n\n~~~\n代码\n~~~\n---\n'
        result = vg.data_content_units('x.md', text.encode())
        owned = []
        for unit in result['units']:
            owned.extend(range(unit['line'], unit['end_line'] + 1))
        owned.extend(item['line'] for item in result['excluded_lines'])
        self.assertEqual(sorted(owned), list(range(1, len(text.splitlines()) + 1)))
        self.assertEqual(len(owned), len(set(owned)))

    def test_collector_detects_missing_and_extra_scope(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            root = Path(directory)
            (root/'skill').mkdir()
            (root/'shared').mkdir()
            (root/'extra').mkdir()
            (root/'skill/new.md').write_bytes(b'new')
            (root/'skill/note.txt').write_bytes(b'not markdown')
            sync = root/'sync.py'
            sync.write_bytes(b"SKILL_DIRS=['skill']\nROOT_FILES=['root.md']\nSHARED_FILES=['rules.md']\n")
            files, excluded, problems = vg.collect_data_class_inventory(root, sync)
            self.assertIn('skill/new.md', files)
            self.assertTrue(any('root.md' in p for p in problems))
            self.assertTrue(any('rules.md' in p for p in problems))
            self.assertTrue(any('extra' in p for p in problems))
            self.assertTrue(any(p['path'].endswith('note.txt') for p in excluded))

    def test_formatted_sources_cannot_bypass_checks(self):
        for source, code in (('GB **55016**-2021', 'BC_SOURCE_LABEL'), ('**待补**', 'MISSING_SOURCE'), ('标准T/CECS 123-2020', 'BC_SOURCE_LABEL'), ('图集08J931', 'BC_SOURCE_LABEL')):
            with self.subTest(source=source):
                result = self.run_check(*self.inspect('参数来源：' + source, 'B', source))
                self.assertIn(code, self.codes(result))

    def test_table_without_outer_pipes(self):
        text = '前言\n\n参数 | 来源\n---|---\n2 | S1\n'
        result = self.run_check(*self.inspect(text, 'B'))
        self.assertIn('BC_SOURCE_LABEL', self.codes(result))
        row = next(u for u in result['units'] if u['kind'] == 'table_row')
        self.assertEqual(row['source_cells'][0]['text'], 'S1')
        self.assertNotIn('PARSE', self.codes(result))

    def test_mixed_table_sources_are_bound_per_assertion(self):
        text = '| 限值 | A来源 | 参数 | B来源 |\n|---|---|---|---|\n| 5 | GB 55016 | 2 | 文献甲 |'
        files, review = self.inspect(text)
        unit = vg.data_content_units('skill/reference.md', files['skill/reference.md'])['units'][-1]
        cells = vg.data_table_cells(unit['text'])
        cut = cells[2]['start']
        segments = [
            {'start': 0, 'end': cut, 'class': 'A', 'reason': '规范限值', 'source_spans': [[cells[1]['start'], cells[1]['end']]], 'verified_on': '2020-01-01'},
            {'start': cut, 'end': len(unit['text']), 'class': 'B', 'reason': '物性参数', 'source_spans': [[cells[3]['start'], cells[3]['end']]]}]
        review['records'][unit['id']] = {'segments': segments}
        result = self.run_check(files, review)
        self.assertEqual(result['counts']['fail'], 0)
        output = result['units'][-1]
        self.assertEqual(output['review_record'], {'segments': segments})
        self.assertEqual(output['resolved_sources'][1]['raw_sources'], ['文献甲'])
        bad = copy.deepcopy(review)
        del bad['records'][unit['id']]['segments'][1]['source_spans']
        self.assertIn('AMBIGUOUS_SOURCE', self.codes(self.run_check(files, bad)))
        bad = copy.deepcopy(review)
        bad['records'][unit['id']]['segments'][1]['source_spans'][0][0] += 1
        self.assertIn('SOURCE_BINDING', self.codes(self.run_check(files, bad)))
        bad = copy.deepcopy(review)
        bad['records'][unit['id']]['segments'][1]['source_spans'] = segments[0]['source_spans']
        self.assertIn('BC_SOURCE_LABEL', self.codes(self.run_check(files, bad)))

    def test_method_source_column_cannot_replace_value_source(self):
        text = '| 参数 | 数据来源 | 检测方法来源 |\n|---|---|---|\n| 2 | 文献甲 | GB/T 50081 |'
        self.assertEqual(self.run_check(*self.inspect(text, 'B'))['counts']['fail'], 0)
        result = self.run_check(*self.inspect(text, 'B', 'GB/T 50081'))
        self.assertIn('SOURCE_BINDING', self.codes(result))
        result = self.run_check(*self.inspect(text.replace('文献甲', '待补'), 'B'))
        self.assertIn('MISSING_SOURCE', self.codes(result))

    def test_setext_and_reference_changes_invalidate_usage(self):
        for before, after in (
            ('实测\n====\n\n参数2', '估算\n====\n\n参数2'),
            ('参数见[报告][ref]\n\n[ref]: report-A.pdf', '参数见[报告][ref]\n\n[ref]: report-B.pdf')):
            files, review = self.inspect(before)
            files['skill/reference.md'] = after.encode()
            result = self.run_check(files, review)
            self.assertEqual(result['counts']['reviewed'], 0)
            self.assertTrue({'STALE_REVIEW', 'UNREVIEWED'} <= self.codes(result))

    def test_collector_includes_new_root_shared_and_hidden_markdown(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            root = Path(directory)
            (root/'skill').mkdir()
            (root/'shared').mkdir()
            for name in ('root.md', 'shared/rules.md', 'new.md', 'shared/new.md', 'skill/.new.md'):
                (root/name).write_bytes(b'new assertion')
            sync = root/'sync.py'
            sync.write_bytes(b"SKILL_DIRS=['skill']\nROOT_FILES=['root.md']\nSHARED_FILES=['rules.md']\n")
            files, excluded, problems = vg.collect_data_class_inventory(root, sync)
            self.assertFalse(problems)
            self.assertTrue({'new.md', 'shared/new.md', 'skill/.new.md'} <= set(files))
            result = self.run_check(files, {'version': 1, 'records': {}})
            self.assertEqual(result['counts']['unreviewed'], len(files))

    def test_bad_declarations_produce_structured_input_failure(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            root = Path(directory)
            sync = root/'sync.py'
            for values in ([1], ['../skill'], ['a/b'], ['a\\b'], ['C:'], ['skill', 'skill'], []):
                with self.subTest(values=values):
                    sync.write_bytes((f'SKILL_DIRS={values!r}\nROOT_FILES=["root.md"]\nSHARED_FILES=["rules.md"]\n').encode())
                    result = vg.run_data_class_check(root, sync, root/'missing.json', vg.Report())
                    self.assertIn('INPUT', self.codes(result))
                    self.assertEqual(result['counts']['fail'], 1)

    def test_duplicate_json_keys_fail_at_input_boundary(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            review = Path(directory)/'review.json'
            for raw in ('{"version":1,"version":1,"records":{}}', '{"version":1,"records":{"x":{},"x":{}}}'):
                review.write_bytes(raw.encode())
                with patch.object(vg, 'collect_data_class_inventory', return_value=({}, [], [])):
                    result = vg.run_data_class_check(Path(directory), Path(directory)/'sync.py', review, vg.Report())
                self.assertIn('INPUT', self.codes(result))
                self.assertIn('重复', result['findings'][0]['detail'])

    def test_markdown_entities_links_and_code_preserve_source_labels(self):
        sources = (
            '文献甲及&lt;GB 55016&gt;',
            '文献甲及&amp;lt;GB 55016&amp;gt;',
            '`文献甲及<GB 55016>`',
            '`文献甲及&lt;GB 55016&gt;`',
            '[GB](https://example.org) 55016',
            r'GB\/T 9775',
            '<span>GB</span> 55016',
        )
        for source in sources:
            with self.subTest(source=source):
                result = self.run_check(*self.inspect('|参数|来源|\n|---|---|\n|2|' + source + '|', 'B'))
                self.assertIn('BC_SOURCE_LABEL', self.codes(result))
                self.assertIn(source, result['units'][-1]['resolved_sources'][0]['raw_sources'])
        for source in ('<https://example.org/report.pdf>', '&lt;https://example.org/report.pdf&gt;'):
            result = self.run_check(*self.inspect('来源：' + source, 'B', source))
            self.assertEqual(result['counts']['fail'], 0)

    def test_reference_link_resolves_with_document_context(self):
        text = '|参数|来源|\n|---|---|\n|2|[GB][std] 55016|\n\n[std]: https://example.org'
        files, review = self.inspect(text)
        row = next(u for u in vg.data_content_units('skill/reference.md', files['skill/reference.md'])['units'] if u['kind'] == 'table_row')
        review['records'][row['id']]['segments'][0]['class'] = 'B'
        self.assertIn('BC_SOURCE_LABEL', self.codes(self.run_check(files, review)))

    def test_legal_markdown_is_not_a_parser_failure(self):
        for text in ('| 普通文本', '```text\n普通代码', '|项目|说明|\n|---|---|\n|普通说明|'):
            with self.subTest(text=text):
                result = self.run_check(*self.inspect(text))
                self.assertEqual(result['counts']['fail'], 0)
        result = self.run_check(*self.inspect('|参数|来源|\n|---|---|\n|2|', 'B'))
        self.assertIn('MISSING_SOURCE', self.codes(result))

    def test_nested_table_uses_original_source_offsets(self):
        for text in (
            '> |参数|来源|\n> |---|---|\n> |2|S1|',
            '- 条目\n\n  |参数|来源|\n  |---|---|\n  |2|S1|',
        ):
            result = self.run_check(*self.inspect(text, 'B'))
            row = next(u for u in result['units'] if u['kind'] == 'table_row')
            cell = row['source_cells'][0]
            self.assertEqual(row['text'][cell['start']:cell['end']], 'S1')
            self.assertIn('BC_SOURCE_LABEL', self.codes(result))

    def test_original_line_endings_and_unicode_are_preserved(self):
        for ending in ('\n', '\r\n', '\r'):
            text = ending.join(('|参数|来源|', '|---|---|', '|2|文献甲|')) + ending
            result = self.run_check(*self.inspect(text, 'B'))
            self.assertEqual(result['counts']['fail'], 0)
            self.assertEqual(result['units'][-1]['text'], '|2|文献甲|' + ending)
        text = '保留\u2028同一物理行'
        result = self.run_check(*self.inspect(text))
        self.assertEqual(result['units'][0]['text'], text)
        self.assertEqual(result['units'][0]['end_line'], 1)

    def test_directory_read_error_is_never_silently_ignored(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            root = Path(directory)
            (root/'skill').mkdir()
            (root/'shared').mkdir()
            for name in ('root.md', 'shared/rules.md', 'skill/data.md'):
                (root/name).write_bytes(b'content')
            sync = root/'sync.py'
            sync.write_bytes(b"SKILL_DIRS=['skill']\nROOT_FILES=['root.md']\nSHARED_FILES=['rules.md']\n")
            real_scandir = vg.os.scandir
            def denied(path):
                if Path(path) == root/'skill':
                    raise PermissionError(13, 'permission denied', str(path))
                return real_scandir(path)
            with patch.object(vg.os, 'scandir', side_effect=denied):
                files, excluded, problems = vg.collect_data_class_inventory(root, sync)
                self.assertTrue(any('目录读取失败' in problem for problem in problems))
                result = vg.run_data_class_check(root, sync, root/'absent.json', vg.Report())
                self.assertIn('SCOPE', self.codes(result))
                self.assertGreater(result['counts']['fail'], 0)

    def test_nonhashable_literal_is_structured_input_failure(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            root = Path(directory)
            sync = root/'sync.py'
            sync.write_bytes(b'SKILL_DIRS={[]:1}\nROOT_FILES=["root.md"]\nSHARED_FILES=["rules.md"]\n')
            result = vg.run_data_class_check(root, sync, root/'absent.json', vg.Report())
            self.assertIn('INPUT', self.codes(result))
            self.assertEqual(result['counts']['fail'], 1)

    def test_missing_parser_dependency_fails_explicitly(self):
        with patch.object(vg, 'collect_data_class_inventory', return_value=({'x.md': b'content'}, [], [])), patch.object(vg, 'data_markdown_parser', side_effect=ModuleNotFoundError('markdown_it')), patch.object(Path, 'exists', return_value=False):
            result = vg.run_data_class_check(Path('unused'), Path('unused'), Path('unused'), vg.Report())
        self.assertIn('INPUT', self.codes(result))
        self.assertEqual(result['counts']['fail'], 1)

    def test_source_spans_inherit_code_context(self):
        for source, must_fail in (('文献甲<!-- GB 55016 -->', True), ('文献甲&#83;1', False)):
            for text in (
                '```text\n参数=2；来源：' + source + '\n```',
                '    参数=2；来源：' + source,
                '参数=2；来源：`' + source + '`',
                '参数=2；来源：``' + source + '``',
            ):
                with self.subTest(source=source, text=text):
                    result = self.run_check(*self.inspect(text, 'B', source))
                    self.assertEqual('BC_SOURCE_LABEL' in self.codes(result), must_fail)
                    self.assertEqual(result['units'][0]['resolved_sources'][0]['visible_sources'], [source])
                    if not must_fail:
                        self.assertEqual(result['counts']['fail'], 0)
        plain = self.run_check(*self.inspect('参数=2；来源：文献甲&#83;1', 'B', '文献甲&#83;1'))
        self.assertIn('BC_SOURCE_LABEL', self.codes(plain))

    def test_partial_code_boundary_is_rejected(self):
        text = '参数=2；来源：`文献甲S1`。'
        result = self.run_check(*self.inspect(text, 'B', '`文献甲S1'))
        self.assertIn('SOURCE_CONTEXT', self.codes(result))
        result = self.run_check(*self.inspect(text, 'B', '文献甲S1'))
        self.assertIn('BC_SOURCE_LABEL', self.codes(result))
        self.assertNotIn('SOURCE_CONTEXT', self.codes(result))

    def test_inline_code_offset_after_crlf_is_original_offset(self):
        text = '参数=2\r\n来源：`文献甲<!-- GB 55016 -->`'
        source = '文献甲<!-- GB 55016 -->'
        result = self.run_check(*self.inspect(text, 'B', source))
        self.assertIn('BC_SOURCE_LABEL', self.codes(result))
        self.assertEqual(result['units'][0]['resolved_sources'][0]['visible_sources'], [source])

    def test_separate_confidence_is_checked_even_inside_nondata_segment(self):
        for kind in ('B', 'C'):
            for label in ('S1', '**S1**', 'Ｓ１', '&#83;1', '[S1](https://example.org)'):
                text = f'| 参数 | 来源 | 置信度 |\n|---|---|---|\n| 2 | 行业典型值 | {label} |'
                files, review = self.inspect(text)
                row = vg.data_content_units('skill/reference.md', files['skill/reference.md'])['units'][-1]
                pos = row['text'].index('2')
                review['records'][row['id']]['segments'] = [
                    {'start': 0, 'end': pos, 'class': 'N', 'reason': '分隔'},
                    {'start': pos, 'end': pos + 1, 'class': kind, 'reason': '参数'},
                    {'start': pos + 1, 'end': len(row['text']), 'class': 'N', 'reason': '来源与等级元数据'},
                ]
                result = self.run_check(files, review)
                self.assertIn('BC_CONFIDENCE_LABEL', self.codes(result))
                self.assertNotIn('BC_SOURCE_LABEL', self.codes(result))
                self.assertEqual(result['counts']['confirmed_mislabel_findings'], 1)
        for label in ('S2', 'S4', 'S10'):
            result = self.run_check(*self.inspect(text.replace('[S1](https://example.org)', label), 'B'))
            self.assertEqual(result['counts']['fail'], 0)

    def test_confidence_does_not_replace_source(self):
        for header in ('置信度', '来源等级', '**数据源可信度**', '证据等级', 'S等级'):
            result = self.run_check(*self.inspect(f'| 参数 | {header} |\n|---|---|\n| 2 | S1 |', 'B'))
            self.assertIn('BC_CONFIDENCE_LABEL', self.codes(result))
            self.assertIn('MISSING_SOURCE', self.codes(result))
            self.assertEqual(result['units'][-1]['source_cells'], [])

    def test_multiple_confidence_columns_require_binding(self):
        text = '| 参数 | 来源 | 甲置信度 | 乙置信度 |\n|---|---|---|---|\n| 2 | 文献甲 | S1 | S4 |'
        result = self.run_check(*self.inspect(text, 'B'))
        self.assertIn('AMBIGUOUS_CONFIDENCE', self.codes(result))
        self.assertIn('UNBOUND_CONFIDENCE', self.codes(result))

    def test_mixed_classes_bind_confidence_without_broadcast(self):
        text = '| 规范值 | 物性值 | 规范来源 | 参数来源 | 规范置信度 | 参数置信度 |\n|---|---|---|---|---|---|\n| 5 | 2 | GB 55016 | 文献甲 | S1 | S4 |'
        files, review = self.inspect(text)
        row = vg.data_content_units('skill/reference.md', files['skill/reference.md'])['units'][-1]
        first, second = row['text'].index('5'), row['text'].index('2')
        source, confidence = row['source_cells'], row['confidence_cells']
        a = {'start': first, 'end': first + 1, 'class': 'A', 'reason': '规范限值', 'verified_on': '2020-01-01',
             'source_spans': [[source[0]['start'], source[0]['end']]],
             'confidence_spans': [[confidence[0]['start'], confidence[0]['end']]]}
        b = {'start': second, 'end': second + 1, 'class': 'B', 'reason': '物性值',
             'source_spans': [[source[1]['start'], source[1]['end']]],
             'confidence_spans': [[confidence[1]['start'], confidence[1]['end']]]}
        review['records'][row['id']]['segments'] = [
            {'start': 0, 'end': first, 'class': 'N', 'reason': '分隔'}, a,
            {'start': first + 1, 'end': second, 'class': 'N', 'reason': '分隔'}, b,
            {'start': second + 1, 'end': len(row['text']), 'class': 'N', 'reason': '元数据'},
        ]
        self.assertEqual(self.run_check(files, review)['counts']['fail'], 0)
        a['confidence_spans'], b['confidence_spans'] = b['confidence_spans'], a['confidence_spans']
        self.assertIn('BC_CONFIDENCE_LABEL', self.codes(self.run_check(files, review)))
        a['confidence_spans'] = b['confidence_spans'] = [[confidence[1]['start'], confidence[1]['end']]]
        self.assertIn('UNBOUND_CONFIDENCE', self.codes(self.run_check(files, review)))

    def test_one_shared_confidence_cannot_be_consumed_only_by_a(self):
        text = '|规范值|物性值|规范来源|参数来源|置信度|\n|---|---|---|---|---|\n|5|2|GB 55016|行业典型值|S1|'
        files, review = self.inspect(text)
        row = vg.data_content_units('skill/reference.md', files['skill/reference.md'])['units'][-1]
        first, second = row['text'].index('5'), row['text'].index('2')
        source, label = row['source_cells'], row['confidence_cells'][0]
        a = {'start': first, 'end': first + 1, 'class': 'A', 'reason': '规范值', 'verified_on': '2020-01-01',
             'source_spans': [[source[0]['start'], source[0]['end']]], 'confidence_spans': [[label['start'], label['end']]]}
        b = {'start': second, 'end': second + 1, 'class': 'B', 'reason': '物性值',
             'source_spans': [[source[1]['start'], source[1]['end']]], 'confidence_spans': []}
        review['records'][row['id']]['segments'] = [
            {'start': 0, 'end': first, 'class': 'N', 'reason': '分隔'}, a,
            {'start': first + 1, 'end': second, 'class': 'N', 'reason': '分隔'}, b,
            {'start': second + 1, 'end': len(row['text']), 'class': 'N', 'reason': '元数据'},
        ]
        self.assertIn('UNBOUND_CONFIDENCE', self.codes(self.run_check(files, review)))
        del b['confidence_spans']
        self.assertIn('BC_CONFIDENCE_LABEL', self.codes(self.run_check(files, review)))

    def test_confidence_binding_cannot_skip_or_slice_label(self):
        text = '| 参数 | 来源 | 置信度 |\n|---|---|---|\n| 2 | 文献甲 | S1 |'
        for binding in ([], 'S1', [[True, 1]], [[0, 1]], None):
            files, review = self.inspect(text, 'B')
            row = vg.data_content_units('skill/reference.md', files['skill/reference.md'])['units'][-1]
            if binding is None:
                cell = row['confidence_cells'][0]
                binding = [[cell['start'], cell['end'] - 1]]
            review['records'][row['id']]['segments'][0]['confidence_spans'] = binding
            self.assertIn('UNBOUND_CONFIDENCE', self.codes(self.run_check(files, review)))

    def test_nested_confidence_preserves_offsets_and_code_literals(self):
        for prefix in ('> ', '  '):
            text = ('- 条目\n\n' if prefix == '  ' else '') + '\n'.join(prefix + line for line in (
                '|参数|来源|置信度|', '|---|---|---|', '|2|文献甲|`S1`|'))
            result = self.run_check(*self.inspect(text, 'B'))
            self.assertIn('BC_CONFIDENCE_LABEL', self.codes(result))
            label = result['units'][-1]['resolved_confidence'][0]['labels'][0]
            self.assertEqual(label['raw'], '`S1`')
            self.assertEqual(label['visible'], 'S1')
        text = '|参数|来源|置信度|\n|---|---|---|\n|2|文献甲|`&#83;1`|'
        self.assertEqual(self.run_check(*self.inspect(text, 'B'))['counts']['fail'], 0)

    def test_nonempty_source_does_not_certify_evidence(self):
        result = self.run_check(*self.inspect('|参数|来源|\n|---|---|\n|2|行业典型值|', 'B'))
        self.assertEqual(result['counts']['fail'], 0)
        self.assertEqual(result['units'][-1]['review_state'], '分类记录有效（不等于证据真实或工程合格）')

    def test_only_cli_never_calls_existing_checks(self):
        argv = ['validate_governance.py', '--data-class-only', '--data-json']
        result = {'counts': {'fail': 1}}
        with patch.object(sys, 'argv', argv), patch.object(vg, 'run_data_class_check', return_value=result), patch.object(vg, 'check_redlines', side_effect=AssertionError('越界调用')), patch('builtins.print'):
            with self.assertRaises(SystemExit) as stopped:
                vg.main()
            self.assertEqual(stopped.exception.code, 1)


class FrozenBaselineTest(unittest.TestCase):
    ROW = '| 检测项目 | 标准要求 | 标准编号 |\n|---|---|---|\n| 空气声隔声量 | ≥45 dB | GB 55038-2025 |'

    def units(self, text):
        return vg.data_content_units('skill/reference.md', text.encode())['units']

    def review(self, units, mode='baseline', entry=None):
        rec = entry or {'deferred_to': 'PL-060', 'registered_on': '2026-09-23'}
        if mode == 'record':
            return {'version': 1, 'records': {u['id']: {'segments': [
                {'start': 0, 'end': len(u['text']), 'class': 'A', 'reason': '合成', 'verified_on': '2026-09-01'}]} for u in units}}
        return {'version': 2, 'records': {}, 'baseline': {u['id']: dict(rec) for u in units}}

    def codes(self, result):
        return {item['code'] for item in result['findings']}

    def run_check(self, files, review):
        return vg.check_data_class_consistency(files, review, vg.Report())

    def test_baseline_freezes_without_reviewed_record(self):
        units = self.units(self.ROW)
        result = self.run_check({'skill/reference.md': self.ROW.encode()}, self.review(units))
        self.assertEqual(result['counts']['fail'], 0)
        self.assertEqual(result['counts']['deferred'], len(units))
        self.assertEqual(result['counts']['reviewed'], 0)
        self.assertNotIn('UNREVIEWED', self.codes(result))

    def test_edited_row_reopens_as_unreviewed(self):
        units = self.units(self.ROW)
        baseline = self.review(units)['baseline']
        edited = self.ROW.replace('≥45 dB', '≥50 dB')
        result = self.run_check({'skill/reference.md': edited.encode()},
                                {'version': 2, 'records': {}, 'baseline': baseline})
        self.assertIn('STALE_BASELINE', self.codes(result))
        self.assertIn('UNREVIEWED', self.codes(result))
        self.assertGreater(result['counts']['fail'], 0)

    def test_baseline_cannot_cover_a_different_unit(self):
        units = self.units(self.ROW)
        other = self.ROW.replace('空气声隔声量', '撞击声改良量')
        result = self.run_check({'skill/reference.md': other.encode()},
                                {'version': 2, 'records': {}, 'baseline': {units[0]['id']: {'deferred_to': 'PL-060', 'registered_on': '2026-09-23'}}})
        self.assertIn('UNREVIEWED', self.codes(result))

    def test_double_registration_rejected(self):
        units = self.units(self.ROW)
        review = self.review(units)
        review['records'] = self.review(units, 'record')['records']
        result = self.run_check({'skill/reference.md': self.ROW.encode()}, review)
        self.assertIn('DOUBLE_REGISTRATION', self.codes(result))

    def test_baseline_entry_must_carry_ledger_ref_and_past_date(self):
        units = self.units(self.ROW)
        for bad in ({'deferred_to': 'TODO', 'registered_on': '2026-09-23'},
                    {'deferred_to': 'PL-60', 'registered_on': '2026-09-23'},
                    {'deferred_to': 'PL-060', 'registered_on': '2099-01-01'},
                    {'deferred_to': 'PL-060', 'registered_on': '不是日期'},
                    {'deferred_to': 'PL-060'}):
            with self.subTest(entry=bad):
                result = self.run_check({'skill/reference.md': self.ROW.encode()},
                                        {'version': 2, 'records': {}, 'baseline': {units[0]['id']: bad}})
                self.assertIn('BASELINE_SCHEMA', self.codes(result))

    def test_version_two_requires_baseline_mapping(self):
        units = self.units(self.ROW)
        result = self.run_check({'skill/reference.md': self.ROW.encode()},
                                {'version': 2, 'records': self.review(units, 'record')['records']})
        self.assertIn('REVIEW_SCHEMA', self.codes(result))

    def test_empty_baseline_is_noop(self):
        result = self.run_check({'skill/reference.md': self.ROW.encode()},
                                {'version': 2, 'records': {}, 'baseline': {}})
        self.assertIn('UNREVIEWED', self.codes(result))

    def test_provenance_header_binds_a_row_without_source_column(self):
        units = {u['text']: u for u in self.units(self.ROW)}
        row = [u for u in units.values() if u['kind'] == 'table_row'][0]
        self.assertEqual([c['header'] for c in row['source_cells']], ['标准编号'])
        review = {'version': 1, 'records': {u['id']: {'segments': [
            {'start': 0, 'end': len(u['text']),
             'class': 'A' if u['kind'] == 'table_row' else 'N',
             'reason': '合成', 'verified_on': '2026-09-01'}]} for u in units.values()}}
        result = self.run_check({'skill/reference.md': self.ROW.encode()}, review)
        self.assertEqual(result['counts']['fail'], 0)

    def test_acceptance_limit_column_is_not_provenance(self):
        text = '| 检查项 | 验收标准 |\n|---|---|\n| 平整度 | 2m 靠尺 ≤3mm |'
        units = self.units(text)
        review = {'version': 1, 'records': {u['id']: {'segments': [
            {'start': 0, 'end': len(u['text']), 'class': 'A', 'reason': '合成', 'verified_on': '2026-09-01'}]} for u in units}}
        result = self.run_check({'skill/reference.md': text.encode()}, review)
        self.assertIn('MISSING_SOURCE', self.codes(result))

    def test_two_provenance_columns_require_explicit_binding(self):
        text = '| 参数 | 来源 | 标准编号 |\n|---|---|---|\n| E=2 GPa | 厂家检测报告 | GB/T 9775 |'
        units = {u['text']: u for u in self.units(text)}
        row = [u for u in units.values() if u['kind'] == 'table_row'][0]
        self.assertEqual([c['header'] for c in row['source_cells']], ['来源', '标准编号'])
        broadcast = {'version': 1, 'records': {u['id']: {'segments': [
            {'start': 0, 'end': len(u['text']),
             'class': 'A' if u['kind'] == 'table_row' else 'N',
             'reason': '合成', 'verified_on': '2026-09-01'}]} for u in units.values()}}
        self.assertIn('AMBIGUOUS_SOURCE', self.codes(self.run_check({'skill/reference.md': text.encode()}, broadcast)))
        cells = row['source_cells']
        bound = {'version': 1, 'records': {u['id']: {'segments': [
            {'start': 0, 'end': len(u['text']),
             'class': 'A' if u['kind'] == 'table_row' else 'N',
             'reason': '合成', 'verified_on': '2026-09-01',
             'source_spans': [[cells[0]['start'], cells[0]['end']]]}]} for u in units.values()}}
        self.assertEqual(self.run_check({'skill/reference.md': text.encode()}, bound)['counts']['fail'], 0)


class UnitIdGranularityTest(unittest.TestCase):
    """单元身份绑到「本单元自身」而非整件：治理登记面每次追加行不得把全件打成重审。"""

    DOC = ('# 隔声参数\n\n'
           '| 检测项目 | 标准要求 | 标准编号 |\n|---|---|---|\n'
           '| 空气声隔声量 | ≥45 dB | GB 55038-2025 |\n'
           '| 撞击声隔声量 | ≤75 dB | GB 55038-2025 |\n\n'
           '本节为路由说明，不含数值。\n')

    def units(self, text):
        return vg.data_content_units('skill/reference.md', text.encode())['units']

    def codes(self, result):
        return {item['code'] for item in result['findings']}

    def run_check(self, text, review):
        return vg.check_data_class_consistency({'skill/reference.md': text.encode()},
                                               review, vg.Report())

    def review_for(self, units, mode='record'):
        if mode == 'record':
            records = {}
            for u in units:
                if u['kind'] == 'table_row':
                    seg = {'start': 0, 'end': len(u['text']), 'class': 'A', 'reason': '合成',
                           'verified_on': '2026-09-01',
                           'source_spans': [[c['start'], c['end']] for c in u['source_cells']]}
                else:
                    seg = {'start': 0, 'end': len(u['text']), 'class': 'N', 'reason': '合成'}
                records[u['id']] = {'segments': [seg]}
            return {'version': 1, 'records': records}
        return {'version': 2, 'records': {}, 'baseline': {
            u['id']: {'deferred_to': 'PL-060', 'registered_on': '2026-09-23'} for u in units}}

    def test_appending_a_row_does_not_reopen_other_units(self):
        base = self.units(self.DOC)
        extended = self.DOC + '\n| 表面平整度 | ≤2mm/2m | GB 50210-2018 |\n'
        for mode in ('record', 'baseline'):
            with self.subTest(mode=mode):
                review = self.review_for(base, mode)
                result = self.run_check(extended, review)
                stale = {'STALE_REVIEW', 'STALE_BASELINE'} & self.codes(result)
                label = '冻结存量' if mode == 'baseline' else '复核记录'
                self.assertEqual(set(), stale, '追加无关行使既有' + label + '整件失配')
                unreviewed = [f for f in result['findings'] if f['code'] == 'UNREVIEWED']
                self.assertEqual(len(self.units(extended)) - len(base), len(unreviewed),
                                 '只有新增单元该回到必判定态')

    def test_editing_one_row_reopens_only_that_row(self):
        base = self.units(self.DOC)
        edited = self.DOC.replace('≥45 dB', '≥48 dB')
        for mode in ('record', 'baseline'):
            with self.subTest(mode=mode):
                result = self.run_check(edited, self.review_for(base, mode))
                unreviewed = [f['line'] for f in result['findings'] if f['code'] == 'UNREVIEWED']
                self.assertEqual(1, len(unreviewed), '改一行只该重开那一行')

    def test_heading_edit_reopens_units_under_it(self):
        base = self.units(self.DOC)
        result = self.run_check(self.DOC.replace('# 隔声参数', '# 隔声参数（修订）'),
                                self.review_for(base))
        self.assertIn('UNREVIEWED', self.codes(result))
        self.assertGreater(result['counts']['unreviewed'], 1,
                           '小节标题被理由文本引用，其下单元须随标题回到必判定态')

    def test_same_text_under_another_heading_is_a_different_unit(self):
        first = self.units(self.DOC)[0]
        second = self.units('# 另一小节\n\n' + self.DOC.split('\n', 1)[1])[0]
        self.assertNotEqual(first['id'], second['id'])


class SelfProducedScopeTest(unittest.TestCase):
    """镜像根上的工具自产件不入复核面，且豁免判据取产生侧 AST 声明而非文件名白名单。

    发布前模拟实测：`同步说明.md`（sync 每次整体覆写的哈希清单）若在复核面内，其 80 条
    判定单元全部 UNREVIEWED；而它每次同步都换字节，登记即产生「每发布一次就得重登一次」
    的自造红。反过来说，豁免只能是「脚本自己写的」，不能是「名字像清单的」。
    """

    SYNC = ("SKILL_DIRS=['skill']\nROOT_FILES=['root.md']\nSHARED_FILES=['rules.md']\n"
            "DST = Path('.')\nMANIFEST_NAME = \"同步说明.md\"\n"
            "(DST / MANIFEST_NAME).write_text('x', encoding='utf-8')\n")
    MANIFEST = ('# 技能仓备份 — 同步说明\n\n文件总数：2\n\n| 文件 | SHA-256 | 字节 |\n|---|---|---|\n'
                '| a.md | %s | 1,024 |\n' % ('0' * 64))

    def tree(self, root, sync_src=SYNC, manifest=True):
        (root/'skill').mkdir()
        (root/'shared').mkdir()
        (root/'skill/a.md').write_bytes('# 标题\n\n文本。\n'.encode())
        (root/'root.md').write_bytes('# 根治理\n\n文本。\n'.encode())
        (root/'shared/rules.md').write_bytes('# 规则\n\n文本。\n'.encode())
        if manifest:
            (root/'同步说明.md').write_bytes(self.MANIFEST.encode())
        (root/'sync.py').write_bytes(sync_src.encode())

    def codes_for(self, root, path):
        report = vg.Report()
        result = vg.run_data_class_check(root, root/'sync.py', root/'absent.json', report)
        return {c['code'] for c in result['findings'] if c['path'] == path}, result, report

    def test_generated_manifest_leaves_surface_and_is_disclosed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            root = Path(directory)
            self.tree(root)
            codes, result, report = self.codes_for(root, '同步说明.md')
            self.assertNotIn('UNREVIEWED', codes, '自产件不得进复核面')
            items = [m for sec in report.sections for _, m in sec['items']]
            self.assertTrue(any('自产件豁免' in m and '同步说明.md' in m for m in items),
                            '豁免须逐件披露，不得静默少扫')

    def test_handwritten_root_md_is_still_scanned(self):
        """控制例：同形态内容换个名字即必判定——豁免判据不是「长得像清单」。"""
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            root = Path(directory)
            self.tree(root)
            (root/'同步说明.md').rename(root/'人工说明.md')
            codes, _, _ = self.codes_for(root, '人工说明.md')
            self.assertIn('UNREVIEWED', codes)

    def test_exemption_dies_when_producer_stops_writing(self):
        """去掉写盘语句、文件名不变 → 豁免必须失效（证 AST 取产生侧、非名字白名单）。"""
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            root = Path(directory)
            self.tree(root, sync_src=self.SYNC.replace(
                "(DST / MANIFEST_NAME).write_text('x', encoding='utf-8')\n", ''))
            codes, _, _ = self.codes_for(root, '同步说明.md')
            self.assertIn('UNREVIEWED', codes)

    def test_collision_with_governance_declaration_is_a_problem(self):
        """自产名与 ROOT_FILES 重叠不得静默豁免：那意味着治理文件被脚本整体覆写。"""
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            root = Path(directory)
            self.tree(root, sync_src=self.SYNC.replace('MANIFEST_NAME = "同步说明.md"',
                                                       'MANIFEST_NAME = "root.md"'))
            _, excluded, problems = vg.collect_data_class_inventory(root, root/'sync.py')
            self.assertTrue(any('重叠' in p for p in problems), '重叠须报冲突')
            self.assertFalse(any(i.get('generated_by_sync') for i in excluded))


if __name__ == '__main__':
    unittest.main()
