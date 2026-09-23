"""Per-account saved locations, restricted to the Shandong boundary."""
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
import requests
from auth import get_token_user, update_location, LocationUpdateRequest

router = APIRouter(prefix='/auth/locations', tags=['保存地点'])
DB_PATH = Path(os.getenv('SAVED_LOCATIONS_DB_PATH', str(Path(__file__).with_name('saved_locations.sqlite3'))))
BOUNDARY_PATH = Path(__file__).parent.parent / 'data' / 'shandong.geojson'
BOUNDARY = json.loads(BOUNDARY_PATH.read_text(encoding='utf-8'))

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS saved_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        name TEXT NOT NULL, address TEXT NOT NULL, lng REAL NOT NULL, lat REAL NOT NULL,
        station_id TEXT, station_name TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn

def inside_ring(lng, lat, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][:2]; xj, yj = ring[j][:2]
        if (yi > lat) != (yj > lat) and lng < (xj-xi)*(lat-yi)/(yj-yi)+xi:
            inside = not inside
        j = i
    return inside

def in_shandong(lng, lat):
    geometry = BOUNDARY['features'][0]['geometry']
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    return any(inside_ring(lng, lat, rings[0]) and
               not any(inside_ring(lng, lat, hole) for hole in rings[1:]) for rings in polygons)

def rows(user_id):
    with closing(connect()) as conn:
        return [dict(row) for row in conn.execute(
            'SELECT id,name,address,lng,lat,station_id,station_name FROM saved_locations WHERE user_id=? ORDER BY id',
            (user_id,)).fetchall()]

class SavedLocationRequest(BaseModel):
    lng: float
    lat: float
    name: str = Field(default='', max_length=40)

@router.get('')
def list_locations(authorization: str = Header(default=None)):
    return {'locations': rows(get_token_user(authorization)), 'limit': 5}

@router.get('/search')
def search_locations(q: str, authorization: str = Header(default=None)):
    get_token_user(authorization)
    query = q.strip()
    if len(query) < 2 or len(query) > 60:
        raise HTTPException(400, '请输入2—60个字的山东地点名称')
    try:
        response = requests.get('https://nominatim.openstreetmap.org/search', params={
            'q': f'{query}, 山东省', 'format': 'jsonv2', 'limit': 8,
            'countrycodes': 'cn', 'accept-language': 'zh-CN'
        }, headers={'User-Agent':'jinan-weather-course-project/1.0'}, timeout=8)
        response.raise_for_status()
        results=[]
        for item in response.json():
            lng,lat=float(item['lon']),float(item['lat'])
            if in_shandong(lng,lat):
                results.append({'name':item.get('name') or query,'address':item.get('display_name') or query,
                                'lng':lng,'lat':lat})
        return {'results':results[:5]}
    except requests.RequestException as exc:
        raise HTTPException(502, '地点搜索暂时不可用') from exc

@router.post('')
def add_location(data: SavedLocationRequest, authorization: str = Header(default=None)):
    user_id = get_token_user(authorization)
    if not in_shandong(data.lng, data.lat):
        raise HTTPException(400, '只能保存山东省内的地点')
    with closing(connect()) as conn:
        if conn.execute('SELECT COUNT(*) FROM saved_locations WHERE user_id=?',(user_id,)).fetchone()[0] >= 5:
            raise HTTPException(400, '最多保存5个地点')
        duplicate = conn.execute('SELECT 1 FROM saved_locations WHERE user_id=? AND abs(lng-?)<0.0001 AND abs(lat-?)<0.0001',
                                 (user_id,data.lng,data.lat)).fetchone()
        if duplicate: raise HTTPException(409, '这个地点已经保存')
    located = update_location(LocationUpdateRequest(lng=data.lng, lat=data.lat, alt=None), authorization)
    station = located.get('nearest_station') or {}
    name = data.name.strip() or located.get('address') or '保存地点'
    with closing(connect()) as conn:
        cursor = conn.execute('''INSERT INTO saved_locations
            (user_id,name,address,lng,lat,station_id,station_name) VALUES(?,?,?,?,?,?,?)''',
            (user_id,name,located.get('address') or name,data.lng,data.lat,station.get('id'),station.get('name')))
        conn.commit(); location_id = cursor.lastrowid
    return {'location': next(item for item in rows(user_id) if item['id']==location_id)}

@router.put('/{location_id}/select')
def select_location(location_id: int, authorization: str = Header(default=None)):
    user_id = get_token_user(authorization)
    with closing(connect()) as conn:
        row = conn.execute('SELECT * FROM saved_locations WHERE id=? AND user_id=?',(location_id,user_id)).fetchone()
    if not row: raise HTTPException(404, '地点不存在')
    located = update_location(LocationUpdateRequest(lng=row['lng'],lat=row['lat'],alt=None),authorization)
    return {'location': dict(row), **located}

@router.delete('/{location_id}')
def delete_location(location_id: int, authorization: str = Header(default=None)):
    user_id = get_token_user(authorization)
    with closing(connect()) as conn:
        count=conn.execute('DELETE FROM saved_locations WHERE id=? AND user_id=?',(location_id,user_id)).rowcount
        conn.commit()
    if not count: raise HTTPException(404, '地点不存在')
    return {'success': True}
