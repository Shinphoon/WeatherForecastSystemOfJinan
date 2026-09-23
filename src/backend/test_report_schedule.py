import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timedelta
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from fastapi import HTTPException
import report_schedule as r

class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.now=datetime(2026,9,18,7,0,tzinfo=r.b.CHINA)
        self.user=SimpleNamespace(last_lat=36.8,last_lng=118,last_address='淄博',email='user@example.invalid',push_enable=1)
        self.forecast=[dict(date='2026-09-18',weather_code=0,temperature_min=15,temperature_max=25),dict(date='2026-09-19',weather_code=61,temperature_min=14,temperature_max=24)]
        self.patches=[patch.object(r.b,'DB_PATH',Path(self.tmp.name)/'reports.db'),patch.object(r.b,'profile',return_value=self.user),patch.object(r.b,'get_7d_forecast',return_value=self.forecast),patch.object(r.b,'send_briefing_email')]
        self.mocks=[p.start() for p in self.patches]
        with r.connect() as c: pass
        c.close()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def test_settings_api_validates_and_isolates_accounts(self):
        import auth
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        app=FastAPI();app.include_router(r.router);client=TestClient(app)
        with patch.object(auth,'get_token_user',return_value=1):
            self.assertEqual(client.put('/auth/report-schedule',json={'morning':'04:59','noon':'15:20','evening':'18:00'}).status_code,400)
            self.assertEqual(client.put('/auth/report-schedule',json={'morning':'09:15','noon':'15:20','evening':'21:45'}).status_code,200)
            self.assertEqual(client.get('/auth/report-schedule').json()['morning'],'09:15')
        with patch.object(auth,'get_token_user',return_value=2):
            self.assertEqual(client.get('/auth/report-schedule').json()['morning'],'07:00')
    def test_boundaries(self):
        for morning,noon,evening in [('05:00','11:00','16:30'),('11:00','16:30','22:30')]:r.validate(r.ScheduleRequest(morning=morning,noon=noon,evening=evening))
        for morning,evening in [('04:59','18:00'),('11:01','18:00'),('07:00','16:29'),('07:00','22:31'),('7:00','18:00')]:
            with self.assertRaises(HTTPException):r.validate(r.ScheduleRequest(morning=morning,noon='15:20',evening=evening))
        for noon in ('10:59','16:31'):
            with self.assertRaises(HTTPException):r.validate(r.ScheduleRequest(morning='07:00',noon=noon,evening='18:00'))
    def test_not_early_then_both_reports(self):
        r.ensure_reports(1,self.now-timedelta(minutes=1));self.assertEqual(r.b.inbox(1),[])
        r.ensure_reports(1,self.now);r.ensure_reports(1,self.now)
        r.ensure_reports(1,self.now.replace(hour=18));r.ensure_reports(1,self.now.replace(hour=18))
        messages=r.b.inbox(1);self.assertEqual(len(messages),2);self.assertEqual(self.mocks[-1].call_count,2)
        evening=next(m for m in messages if m['kind']=='晚间天气报告')
        self.assertIn('明日天气：有雨',evening['description'])
        r.b.mark_read(2,[evening['id']]);self.assertFalse(next(m for m in r.b.inbox(1) if m['id']==evening['id'])['read'])
        r.b.mark_read(1,[evening['id']]);self.assertTrue(next(m for m in r.b.inbox(1) if m['id']==evening['id'])['read'])
    def test_concurrent_claim(self):
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda _:r.ensure_reports(1,self.now),range(4)))
        self.assertEqual(self.mocks[-1].call_count,1)
    def test_noon_default_and_switches(self):
        r.ensure_reports(1,self.now.replace(hour=15,minute=20))
        self.assertEqual(r.b.inbox(1)[0]['kind'],'午间天气报告')
        from contextlib import closing
        with closing(r.connect()) as c:
            c.execute('DELETE FROM briefings');c.execute('''INSERT INTO report_schedule
                (user_id,morning,noon,evening,morning_enabled,noon_enabled,evening_enabled)
                VALUES(1,'07:00','15:20','18:00',0,0,0)
                ON CONFLICT(user_id) DO UPDATE SET morning_enabled=0,noon_enabled=0,evening_enabled=0''');c.commit()
        for moment in (self.now,self.now.replace(hour=15,minute=20),self.now.replace(hour=18)):
            r.ensure_reports(1,moment)
        self.assertEqual(r.b.inbox(1),[])
    def test_custom_time_and_no_email(self):
        from contextlib import closing
        with closing(r.connect()) as c:
            c.execute("INSERT INTO report_schedule(user_id,morning,noon,evening) VALUES(1,'10:30','15:20','21:30')");c.commit()
        r.ensure_reports(1,self.now);self.assertEqual(r.b.inbox(1),[])
        self.user.email=None;r.ensure_reports(1,self.now.replace(hour=10,minute=30))
        self.assertEqual(r.b.inbox(1)[0]['email_status'],'no_email');self.mocks[-1].assert_not_called()
    def test_failed_email_keeps_report_and_reason(self):
        self.mocks[-1].side_effect=TimeoutError()
        with self.assertLogs(r.logger,level='ERROR'):r.ensure_reports(1,self.now)
        self.assertIn('超时',r.b.inbox(1)[0]['email_error'])
        r.ensure_reports(1,self.now);self.assertEqual(self.mocks[-1].call_count,1)
    def test_after_window_does_not_send(self):
        r.ensure_reports(1,self.now.replace(hour=23));self.assertEqual(r.b.inbox(1),[])

if __name__=='__main__':unittest.main()
