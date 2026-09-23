"""Bounded background collection shared by all map clients; never block a GET
on hundreds of upstream calls. Missing/old measurements are never zero-filled.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from threading import Lock, Thread
import math
import time
from qweather_spider import get_realtime_weather, get_today_weather, get_history_weather

CHINA = timezone(timedelta(hours=8))
LIMITS = {'temperature': (-70, 60), 'humidity': (0, 100), 'pressure': (500, 1100),
          'rain_1h': (0, 500), 'rain_24h': (0, 2000)}
FIELDS = ('temperature', 'humidity', 'rain_1h', 'rain_24h')

def number(value, field):
    try:
        value = float(str(value).strip().replace('−', '-'))
        lo, hi = LIMITS[field]
        return value if math.isfinite(value) and lo <= value <= hi else None
    except (ValueError, TypeError): return None

def timestamp(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M %z')
    except (ValueError, TypeError):
        return None

def fresh(value, now):
    return value is not None and -timedelta(minutes=10) <= now - value <= timedelta(hours=3)

def collect_station(station, changes=False, now=None):
    now = now or datetime.now(CHINA)
    result = {'id': station['id'], 'name': station['name'], 'lon': station['lon'], 'lat': station['lat'], 'values': {}, 'times': {}}
    if not changes:
        data = get_realtime_weather(station['id'])
        for key in FIELDS:
            at = timestamp(data.get('measurement_times', {}).get(key))
            value = number(data.get(key), key)
            if value is not None and fresh(at, now):
                result['values'][key] = value
                result['times'][key] = at.isoformat()
        return result
    rows = [(timestamp(row.get('time')), row) for row in get_today_weather(station['id'])]
    rows = sorted([(at, row) for at, row in rows if fresh(at, now)], key=lambda pair: pair[0], reverse=True)
    if not rows: return result
    at, current = rows[0]
    target = at - timedelta(days=1)
    # Upstream daily archive runs 01:00 through next day's 00:00.
    archive_day = (target - timedelta(seconds=1)).date() if target.hour == 0 else target.date()
    history = get_history_weather(station['id'], archive_day.isoformat())
    previous = next((row for row in history if timestamp(row.get('time')) == target), None)
    if previous:
        for source, key in [('temperature', 'temperature_change'), ('pressure', 'pressure_change')]:
            a, b = number(current.get(source), source), number(previous.get(source), source)
            if a is not None and b is not None:
                result['values'][key] = round(a-b, 2)
                result['times'][key] = at.isoformat()
        result['comparison_time'] = target.isoformat()
    return result

class FieldCollector:
    def __init__(self):
        self.lock = Lock()
        self.states = {}

    def snapshot(self, stations, changes=False):
        key = 'changes' if changes else 'realtime'
        with self.lock:
            state = self.states.setdefault(key, {'running': False, 'finished': 0, 'items': {}, 'processed': 0, 'failed': 0, 'total': len(stations), 'version': 0})
            if not state['running'] and (state['finished'] == 0 or time.monotonic() - state['finished'] > 300):
                state.update(running=True, processed=0, failed=0, total=len(stations))
                Thread(target=self.refresh, args=(key, list(stations), changes), daemon=True).start()
            now = datetime.now(CHINA)
            items = []
            for row in state['items'].values():
                row = {**row, 'values': dict(row['values']), 'times': dict(row['times'])}
                for field in list(row['values']):
                    try: at = datetime.fromisoformat(row['times'][field])
                    except (ValueError, KeyError): at = None
                    if not fresh(at, now): row['values'].pop(field); row['times'].pop(field, None)
                items.append(row)
            return {'stations': items, 'loading': state['running'], 'processed': state['processed'],
                    'total': state['total'], 'failed': state['failed'], 'version': state['version'],
                    'source': 'q-weather.info 国家站观测', 'comparison': '最近整点与昨天同一整点相减' if changes else None}

    def refresh(self, key, stations, changes):
        try:
            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = {pool.submit(collect_station, station, changes): station['id'] for station in stations}
                for future in as_completed(futures):
                    station_id = futures[future]
                    try: row = future.result()
                    except Exception: row = None
                    with self.lock:
                        state = self.states[key]
                        state['processed'] += 1
                        state['version'] += 1
                        if row is None:
                            state['failed'] += 1
                            state['items'].pop(station_id, None)
                        else: state['items'][station_id] = row
        finally:
            with self.lock:
                state = self.states[key]
                allowed = {s['id'] for s in stations}
                state['items'] = {k: v for k, v in state['items'].items() if k in allowed}
                state.update(running=False, finished=time.monotonic())

collector = FieldCollector()
