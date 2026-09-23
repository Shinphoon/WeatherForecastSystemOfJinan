"""Station-to-city metadata shared with the frontend, keyed by station ID.

The supplied screenshots are authoritative. The three rows between cropped
screenshots are Wenshang 54912, Ningyang 54913, and Juye 54914.
"""
import json
from pathlib import Path

CITY_STATIONS = json.loads(
    (Path(__file__).resolve().parents[1] / 'data' / 'station-cities.json').read_text(encoding='utf-8')
)
STATION_CITY = {station: city for city, stations in CITY_STATIONS.items() for station in stations}


def station_city(station_id, city):
    station_id = str(station_id).strip()
    if station_id in STATION_CITY:
        return STATION_CITY[station_id]
    value = (city or '').strip()
    return value if value and value not in ('未知', '其他', '未设置') else '其他站点'
