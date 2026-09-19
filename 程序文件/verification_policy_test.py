import re
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import validate_governance as governance


class TestVerificationMaintenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (Path(__file__).resolve().parent.parent
                    / "_专题_技能合集策划/standards-index.md").read_text(encoding="utf-8")

    def report_at(self, when, text=None):
        report = governance.Report()
        with patch.object(governance, "datetime", wraps=datetime) as clock:
            clock.now.return_value = when
            governance.check_standards(self.text if text is None else text, report)
        return [item for section in report.sections for item in section["items"]]

    def with_date(self, text, std_no, date):
        pattern = rf"(?m)^(\|\s*\d+\s*\|\s*{re.escape(std_no)}\s*\|\s*)\d{{4}}-\d{{2}}-\d{{2}}(?=\s*\|)"
        changed, count = re.subn(pattern, lambda match: match[1] + date, text)
        self.assertEqual(count, 1, "必须唯一命中核验日期行，不能改主表或空跑")
        return changed

    def latest_verify_date(self):
        # 核验记录表的「核验日期」恒为第三个单元（序号|标准编号|核验日期|…）；主表同位置是名称，
        # 故该形制只命中核验记录表。钟点取「数据里最新的核验日期」而非硬编码日，否则任何比它新的
        # 补录行都会在该钟点被判为未来日期，把本用例的全局 WARN 集比对变成对索引最新日期的隐式耦合。
        dates = re.findall(r"(?m)^\|\s*\d+\s*\|\s*[^|]*\|\s*(\d{4}-\d{2}-\d{2})\s*\|", self.text)
        self.assertTrue(dates, "索引须含核验记录表的「核验日期」列，否则本用例无被测面")
        return max(datetime.strptime(d, "%Y-%m-%d") for d in dates)

    def test_expiry_is_info_with_stable_warning_set(self):
        boundary = self.latest_verify_date()
        date = (boundary - timedelta(days=governance.REVIEW_DAYS_MANDATORY)).strftime("%Y-%m-%d")
        text = self.with_date(self.text, "GB 55037-2022", date)
        before = self.report_at(boundary, text)
        after = self.report_at(boundary + timedelta(days=1), text)
        self.assertFalse(any("GB 55037-2022：复查提醒" in msg for _, msg in before))
        reminders = [(level, msg) for level, msg in after
                     if "GB 55037-2022：复查提醒" in msg]
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0][0], "INFO")
        self.assertIn("不代表本次已核实最新状态", reminders[0][1])
        self.assertEqual([(lv, msg) for lv, msg in before if lv in ("WARN", "FAIL")],
                         [(lv, msg) for lv, msg in after if lv in ("WARN", "FAIL")])
        self.assertEqual(sum(lv == "PASS" for lv, _ in before),
                         sum(lv == "PASS" for lv, _ in after))

    def test_review_tiers_remain_distinct(self):
        today = datetime(2026, 9, 17)
        self.assertLess(governance.REVIEW_DAYS_MANDATORY, governance.REVIEW_DAYS_OTHER)
        for std_no, tier in (("GB 55037-2022", governance.REVIEW_DAYS_MANDATORY),
                             ("GB/T 11981-2024", governance.REVIEW_DAYS_OTHER)):
            for age, expected in ((tier, False), (tier + 1, True)):
                with self.subTest(std_no=std_no, age=age):
                    date = (today - timedelta(days=age)).strftime("%Y-%m-%d")
                    report = self.report_at(today, self.with_date(self.text, std_no, date))
                    reminders = [(lv, msg) for lv, msg in report if f"{std_no}：复查提醒" in msg]
                    self.assertEqual(bool(reminders), expected)
                    self.assertTrue(all(lv == "INFO" for lv, _ in reminders))

    def test_missing_record_still_warns(self):
        text = self.with_date(self.text, "GB 55037-2022", "")
        report = self.report_at(datetime(2026, 9, 18), text)
        warnings = [msg for lv, msg in report if lv == "WARN" and "无有效「核验日期」" in msg]
        self.assertEqual(len(warnings), 1)
        self.assertIn("依据链未确认", warnings[0])
        self.assertTrue(any("无「核验日期」清单" in msg and "GB 55037-2022" in msg
                            for _, msg in report))

    def test_invalid_and_future_dates_still_warn(self):
        for date in ("2026-02-30", "2099-01-01"):
            with self.subTest(date=date):
                report = self.report_at(datetime(2026, 9, 18),
                                        self.with_date(self.text, "GB 55037-2022", date))
                self.assertTrue(any(lv == "WARN" and "GB 55037-2022：核验日期" in msg
                                    and "记录须核实" in msg for lv, msg in report))
                self.assertFalse(any("GB 55037-2022：复查提醒" in msg for _, msg in report))

    def test_explicit_review_task_is_reported_without_waiving_missing_date(self):
        pattern = r"(?m)^(\|\s*GB 55037-2022\s*\|\s*)已官方核验(?=\s*\|)"
        text, count = re.subn(pattern, lambda match: match[1] + "到期需复核", self.text)
        self.assertEqual(count, 1, "须唯一命中核验状态列")
        for date in ("2026-06-17", ""):
            with self.subTest(date=date):
                report = self.report_at(datetime(2026, 9, 17),
                                        self.with_date(text, "GB 55037-2022", date))
                reminders = [(lv, msg) for lv, msg in report if "GB 55037-2022：复查提醒" in msg]
                self.assertEqual(len(reminders), 1)
                self.assertEqual(reminders[0][0], "INFO")
                self.assertIn("显式复查任务", reminders[0][1])
                self.assertFalse(any("无到期复查任务" in msg for _, msg in report))
                if not date:
                    self.assertTrue(any(lv == "WARN" and "依据链未确认" in msg for lv, msg in report))
                    self.assertTrue(any("无「核验日期」清单" in msg and "GB 55037-2022" in msg
                                        for _, msg in report))

    def test_actual_status_drift_still_fails(self):
        pattern = r"(?m)^(\|\s*2\s*\|\s*GB 55037-2022\s*\|[^\n]*?\|\s*)现行有效(?=\s*\|)"
        text, count = re.subn(pattern, lambda match: match[1] + "即将实施", self.text)
        self.assertEqual(count, 1, "必须命中主表状态而非核验表")
        report = self.report_at(datetime(2026, 9, 18), text)
        self.assertTrue(any(lv == "FAIL" and "GB 55037-2022" in msg
                            and "状态仍为'即将实施'" in msg for lv, msg in report))


if __name__ == "__main__":
    unittest.main(verbosity=2)
