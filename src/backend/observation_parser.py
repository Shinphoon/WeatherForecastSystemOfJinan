from bs4 import BeautifulSoup

FIELDS = {
    '瞬时温度': 'temperature', '地面气压': 'pressure', '相对湿度': 'humidity',
    '瞬时风向': 'wind_direction', '瞬时风速': 'wind_speed',
    '1小时降水': 'rain_1h', '24小时降水': 'rain_24h',
    '10分钟平均能见度': 'visibility', '能见度': 'visibility',
    '2分钟平均风向': 'wind_direction', '2分钟平均风速': 'wind_speed'
}

def parse_realtime(html, station_id):
    table = BeautifulSoup(html, 'html.parser').find('table')
    if table is None: raise ValueError('没有找到实时天气表格')
    data = {'station': station_id, 'measurement_times': {}}
    for row in table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2: continue
        key = FIELDS.get(cells[0].get_text(strip=True))
        if key:
            data[key] = cells[1].get_text(strip=True)
            if len(cells) >= 3: data['measurement_times'][key] = cells[2].get_text(strip=True)
    return data

def parse_hourly(html):
    table = BeautifulSoup(html, 'html.parser').find('table')
    if table is None: return []
    rows = table.find_all('tr')
    if not rows: return []
    headers = [cell.get_text(strip=True) for cell in rows[0].find_all(['td','th'])]
    result = []
    for row in rows[1:]:
        cells = row.find_all('td')
        if not cells: continue
        item = {'time': cells[0].get_text(strip=True)}
        for header, cell in zip(headers[1:], cells[1:]):
            key = FIELDS.get(header)
            if key: item[key] = cell.get_text(strip=True)
        result.append(item)
    return result
