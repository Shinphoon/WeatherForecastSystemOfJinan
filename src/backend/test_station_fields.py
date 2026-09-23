import unittest
from datetime import datetime
from unittest.mock import patch
from observation_parser import parse_realtime, parse_hourly
from station_fields import collect_station, number, timestamp

class StationFieldTests(unittest.TestCase):
    station={'id':'54830','name':'淄博','lon':117.94,'lat':36.83}
    now=timestamp('2026-09-17 15:15 +0800')
    def test_parser_does_not_confuse_gust_with_rain(self):
        html='<table><tr><th>时间</th><th>瞬时温度</th><th>地面气压</th><th>1小时极大风速</th><th>1小时降水</th></tr><tr><td>2026-09-17 15:00 +0800</td><td>30.8</td><td>1011.0</td><td>4.3</td><td>0.0</td></tr></table>'
        row=parse_hourly(html)[0]
        self.assertEqual(row['rain_1h'],'0.0')
        self.assertEqual(row['pressure'],'1011.0')
    def test_realtime_parser_retains_per_field_time(self):
        row=parse_realtime('<table><tr><td>相对湿度</td><td>40</td><td>2026-09-17 15:15 +0800</td></tr></table>','54830')
        self.assertEqual(row['measurement_times']['humidity'],'2026-09-17 15:15 +0800')
    def test_numeric_quality_control(self):
        for v in ['-', '', '999999', 'NaN', None]: self.assertIsNone(number(v,'temperature'))
        self.assertEqual(number('0.0','rain_1h'),0)
        self.assertIsNone(number('-1','rain_1h'))
    def test_exact_24_hour_difference_uses_hourly_both_sides(self):
        current=[{'time':'2026-09-17 15:00 +0800','temperature':'30.8','pressure':'1011.0'}]
        previous=[{'time':'2026-09-16 15:00 +0800','temperature':'33.0','pressure':'1009.4'}]
        with patch('station_fields.get_today_weather',return_value=current),patch('station_fields.get_history_weather',return_value=previous):
            row=collect_station(self.station,True,self.now)
        self.assertEqual(row['values'],{'temperature_change':-2.2,'pressure_change':1.6})
    def test_wrong_hour_and_missing_comparison_are_not_used(self):
        current=[{'time':'2026-09-17 15:00 +0800','temperature':'30.8','pressure':'1011.0'}]
        previous=[{'time':'2026-09-16 14:00 +0800','temperature':'33.0','pressure':'1009.4'}]
        with patch('station_fields.get_today_weather',return_value=current),patch('station_fields.get_history_weather',return_value=previous):
            self.assertEqual(collect_station(self.station,True,self.now)['values'],{})
    def test_realtime_missing_time_and_stale_data_excluded(self):
        data={'temperature':'30','humidity':'40','rain_1h':'0','measurement_times':{'temperature':'2026-09-16 15:15 +0800','rain_1h':'2026-09-17 15:15 +0800'}}
        with patch('station_fields.get_realtime_weather',return_value=data):
            self.assertEqual(collect_station(self.station,False,self.now)['values'],{'rain_1h':0})
    def test_midnight_uses_correct_daily_archive(self):
        current=[{'time':'2026-09-17 00:00 +0800','temperature':'20','pressure':'1000'}]
        with patch('station_fields.get_today_weather',return_value=current),patch('station_fields.get_history_weather',return_value=[]) as history:
            collect_station(self.station,True,timestamp('2026-09-17 00:15 +0800'))
        history.assert_called_once_with('54830','2026-09-15')

if __name__=='__main__':unittest.main()
