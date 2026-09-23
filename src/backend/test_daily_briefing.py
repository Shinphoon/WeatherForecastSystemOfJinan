"""Offline tests: no production database access or real mail deliveries."""
import importlib.util
import sys
import tempfile
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

stubs = {name: types.ModuleType(name) for name in ('database', 'forecast_service', 'email_service')}
stubs['database'].get_connection = Mock()
stubs['forecast_service'].get_7d_forecast = Mock()
stubs['email_service'].send_briefing_email = Mock()
spec = importlib.util.spec_from_file_location('briefing_under_test', Path(__file__).with_name('daily_briefing.py'))
b = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, stubs):
    spec.loader.exec_module(b)


class DailyBriefingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        b.DB_PATH = Path(self.tmp.name) / 'test.sqlite3'
        self.user = types.SimpleNamespace(last_lat=36.6, last_lng=117.0,
            last_address='测试位置', email='test@example.invalid', push_enable=1)
        b.profile = Mock(return_value=self.user)
        self.day = datetime.now(b.CHINA).date().isoformat()
        b.get_7d_forecast = Mock(return_value=[dict(date=self.day, weather_code=61,
            temperature_min=18, temperature_max=28, precipitation_probability=80,
            precipitation_sum=3, wind_speed_max=12)])
        b.send_briefing_email = Mock()

    def tearDown(self): self.tmp.cleanup()

    def test_repeat_and_read_isolation(self):
        b.ensure_daily_briefing(1)
        b.ensure_daily_briefing(1)
        self.assertEqual(b.send_briefing_email.call_count, 1)
        self.assertEqual(len(b.inbox(1)), 1)
        self.assertIn('带伞', b.inbox(1)[0]['description'])
        self.assertEqual(b.inbox(2), [])
        b.mark_read(2, ['briefing:' + self.day])
        self.assertFalse(b.inbox(1)[0]['read'])
        b.mark_read(1, ['briefing:' + self.day])
        self.assertTrue(b.inbox(1)[0]['read'])

    def test_concurrent_login_sends_once(self):
        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(b.ensure_daily_briefing, [1] * 5))
        self.assertEqual(b.send_briefing_email.call_count, 1)
        self.assertEqual(len(b.inbox(1)), 1)

    def test_email_failure_keeps_inbox_without_duplicate_retry(self):
        b.send_briefing_email.side_effect = RuntimeError('SMTP failure')
        with self.assertLogs(b.logger, level='ERROR'): b.ensure_daily_briefing(1)
        b.ensure_daily_briefing(1)
        self.assertEqual(b.inbox(1)[0]['email_status'], 'failed')
        self.assertEqual(b.send_briefing_email.call_count, 1)

    def test_missing_email_and_disabled_push(self):
        self.user.email = None
        b.ensure_daily_briefing(1)
        self.assertEqual(b.inbox(1)[0]['email_status'], 'no_email')
        self.user.email = 'test@example.invalid'
        self.user.push_enable = 0
        b.ensure_daily_briefing(1)
        self.assertEqual(b.inbox(1)[0]['email_status'], 'disabled')
        b.send_briefing_email.assert_not_called()
        self.user.push_enable = 1
        b.ensure_daily_briefing(1)
        self.assertEqual(b.inbox(1)[0]['email_status'], 'sent')

    def test_missing_location_or_forecast_does_not_fabricate_report(self):
        self.user.last_lat = None
        b.ensure_daily_briefing(1)
        self.assertEqual(b.inbox(1), [])
        self.user.last_lat = 36.6
        b.get_7d_forecast.return_value = []
        with self.assertLogs(b.logger, level='ERROR'): b.ensure_daily_briefing(1)
        self.assertEqual(b.inbox(1), [])

    def test_next_day_creates_new_report(self):
        b.ensure_daily_briefing(1)
        tomorrow = datetime.now(b.CHINA) + timedelta(days=1)
        b.get_7d_forecast.return_value[0]['date'] = tomorrow.date().isoformat()
        with patch.object(b, 'datetime') as clock:
            clock.now.return_value = tomorrow
            b.ensure_daily_briefing(1)
        self.assertEqual(len(b.inbox(1)), 2)
        self.assertEqual(b.send_briefing_email.call_count, 2)

if __name__ == '__main__': unittest.main()
