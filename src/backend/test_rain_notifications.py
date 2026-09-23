"""Offline tests; temporary storage and mocked radar/mail only."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import rain_notifications as rain

class RainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.user = SimpleNamespace(last_lat=36.6,last_lng=117,last_address='测试位置',email='test@example.invalid',push_enable=1)
        now=time.time()
        self.result=dict(status='approaching',eta_minutes=20,frames=[dict(time=now-1200,distance_km=20),dict(time=now-600,distance_km=15),dict(time=now,distance_km=10)])
        self.patches=[patch.object(rain.storage,'DB_PATH',Path(self.tmp.name)/'test.db'),patch.object(rain.storage,'profile',return_value=self.user),patch.object(rain,'get_radar_approach',return_value=self.result),patch.object(rain,'send_briefing_email')]
        self.mocks=[p.start() for p in self.patches]
    def tearDown(self):
        for p in reversed(self.patches): p.stop()
        self.tmp.cleanup()
    def retry(self):
        with closing(rain.connect()) as c:
            c.execute('DELETE FROM rain_checks')
            c.commit()
    def test_delivery_dedup_and_read_isolation(self):
        rain.check_rain(1); self.retry(); rain.check_rain(1)
        self.assertEqual(self.mocks[-1].call_count,1)
        messages=rain.inbox(1); self.assertEqual(len(messages),1)
        self.assertEqual(messages[0]['email_status'],'sent')
        self.assertEqual(rain.inbox(2),[])
        rain.mark_read(2,[messages[0]['id']]); self.assertFalse(rain.inbox(1)[0]['read'])
        rain.mark_read(1,[messages[0]['id']]); self.assertTrue(rain.inbox(1)[0]['read'])
    def test_raining_and_non_approaching_do_not_notify(self):
        for status in ['raining','no_echo','unknown','uncertain','not_approaching']:
            self.result['status']=status
            self.retry();rain.check_rain(1)
        self.assertEqual(rain.inbox(1),[]); self.mocks[-1].assert_not_called()
    def test_invalid_eta_stale_and_local_rain_rejected(self):
        for eta in [None,0,61,float('nan')]:
            self.result['eta_minutes']=eta
            self.assertFalse(rain.eligible(self.result,time.time()))
        self.result['eta_minutes']=20
        self.assertFalse(rain.eligible(self.result,time.time()+3600))
        self.result['frames'][-1]['distance_km']=1
        self.assertFalse(rain.eligible(self.result,time.time()))
    def test_email_optout_keeps_inbox(self):
        self.user.push_enable=0;rain.check_rain(1)
        self.assertEqual(rain.inbox(1)[0]['email_status'],'disabled');self.mocks[-1].assert_not_called()
    def test_email_failure_keeps_inbox(self):
        self.mocks[-1].side_effect=RuntimeError('test failure')
        with self.assertLogs(rain.logger,level='ERROR'): rain.check_rain(1)
        self.assertEqual(rain.inbox(1)[0]['email_status'],'failed')
    def test_concurrent_checks_send_once(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(rain.check_rain, [1]*4))
        self.assertEqual(self.mocks[-1].call_count, 1)
        self.assertEqual(len(rain.inbox(1)), 1)
    def test_missing_location_skips(self):
        self.user.last_lat=None;rain.check_rain(1)
        self.mocks[-2].assert_not_called();self.assertEqual(rain.inbox(1),[])

if __name__=='__main__': unittest.main()
