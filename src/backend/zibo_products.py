"""Fixed-origin image proxy: keeps HTTP upstream usable on HTTPS pages."""
import re
import time
from collections import OrderedDict
from threading import Lock
import requests
from fastapi import APIRouter, HTTPException, Response

router = APIRouter()
cache = OrderedDict()
lock = Lock()


@router.get('/weather/zibo-product/{day}/{filename}')
def zibo_product(day: str, filename: str):
    match = re.fullmatch(r'370300_(pre|tem_max|tem_min|wind|vis)_(\d{14})_(\d{14})\.png', filename)
    if not re.fullmatch(r'\d{8}', day) or not match or not match[3].startswith(day):
        raise HTTPException(400, '无效的淄博产品路径')
    key = (day, filename)
    with lock:
        entry = cache.get(key)
        if entry and time.monotonic() - entry[0] < 300:
            return Response(entry[1], media_type='image/png', headers={'Cache-Control': 'public, max-age=300'})
    try:
        with requests.get(f'http://wxzibo2.zbszyqxt.cn/data/product/cmap/{day}/{filename}',
                          timeout=8, stream=True, allow_redirects=False) as response:
            if response.status_code != 200:
                raise HTTPException(404, '该时次产品尚未发布')
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > 5 * 1024 * 1024:
                    raise HTTPException(502, '产品图片过大')
                chunks.append(chunk)
            data = b''.join(chunks)
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                raise HTTPException(502, '上游未返回PNG图片')
    except requests.RequestException as exc:
        raise HTTPException(502, '淄博产品暂时无法访问') from exc
    with lock:
        cache[key] = (time.monotonic(), data)
        cache.move_to_end(key)
        while len(cache) > 24:
            cache.popitem(last=False)
    return Response(data, media_type='image/png', headers={'Cache-Control': 'public, max-age=300'})
