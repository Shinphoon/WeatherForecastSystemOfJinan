import io
import math
import requests

from PIL import Image
from datetime import datetime, timezone


RAINVIEWER_API = (
    "https://api.rainviewer.com/"
    "public/weather-maps.json"
)

ZOOM = 7
TILE_SIZE = 256


def lonlat_to_pixel(
    lng,
    lat,
    zoom=ZOOM
):
    n = 2 ** zoom

    x = (
        (lng + 180.0)
        / 360.0
        * n
        * TILE_SIZE
    )

    lat_rad = math.radians(lat)

    y = (
        (
            1
            -
            math.asinh(
                math.tan(lat_rad)
            )
            / math.pi
        )
        / 2
        * n
        * TILE_SIZE
    )

    return x, y


def meters_per_pixel(
    lat,
    zoom=ZOOM
):
    return (
        156543.03392804097
        * math.cos(
            math.radians(lat)
        )
        / (2 ** zoom)
    )


def get_frame_distance(
    session,
    host,
    frame,
    lat,
    lng,
    search_radius_km=100
):
    user_x, user_y = lonlat_to_pixel(
        lng,
        lat
    )

    mpp = meters_per_pixel(lat)

    radius_px = math.ceil(
        search_radius_km
        * 1000
        / mpp
    )

    min_x = math.floor(
        (user_x - radius_px)
        / TILE_SIZE
    )

    max_x = math.floor(
        (user_x + radius_px)
        / TILE_SIZE
    )

    min_y = math.floor(
        (user_y - radius_px)
        / TILE_SIZE
    )

    max_y = math.floor(
        (user_y + radius_px)
        / TILE_SIZE
    )

    tile_count = 2 ** ZOOM
    nearest_sq = None

    for raw_tx in range(
        min_x,
        max_x + 1
    ):
        for ty in range(
            min_y,
            max_y + 1
        ):
            if (
                ty < 0
                or ty >= tile_count
            ):
                continue

            tx = raw_tx % tile_count

            tile_url = (
                f"{host}"
                f"{frame['path']}"
                f"/256/"
                f"{ZOOM}/"
                f"{tx}/"
                f"{ty}/"
                f"2/1_1.png"
            )

            try:
                response = session.get(
                    tile_url,
                    timeout=10
                )

                if response.status_code != 200:
                    response.raise_for_status()

                image = Image.open(
                    io.BytesIO(
                        response.content
                    )
                ).convert("RGBA")

            except Exception as e:
                print(
                    "雷达瓦片读取失败：",
                    e
                )
                raise RuntimeError("雷达瓦片不完整，跳过判断") from e

            pixels = image.load()

            base_x = (
                raw_tx
                * TILE_SIZE
            )

            base_y = (
                ty
                * TILE_SIZE
            )

            for py in range(
                TILE_SIZE
            ):
                global_y = (
                    base_y + py
                )

                dy = (
                    global_y
                    - user_y
                )

                if abs(dy) > radius_px:
                    continue

                for px in range(
                    TILE_SIZE
                ):
                    global_x = (
                        base_x + px
                    )

                    dx = (
                        global_x
                        - user_x
                    )

                    distance_sq = (
                        dx * dx
                        + dy * dy
                    )

                    if (
                        distance_sq
                        >
                        radius_px
                        * radius_px
                    ):
                        continue

                    alpha = pixels[
                        px,
                        py
                    ][3]

                    if alpha < 40:
                        continue

                    if (
                        nearest_sq is None
                        or
                        distance_sq
                        < nearest_sq
                    ):
                        nearest_sq = (
                            distance_sq
                        )

    if nearest_sq is None:
        return None

    return (
        math.sqrt(nearest_sq)
        * mpp
        / 1000
    )


def get_nearest_radar_echo(
    lat,
    lng,
    search_radius_km=100
):
    session = requests.Session()

    response = session.get(
        RAINVIEWER_API,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    frames = (
        data
        .get("radar", {})
        .get("past", [])
    )

    if not frames:
        raise RuntimeError(
            "RainViewer暂无雷达数据"
        )

    frame = frames[-1]

    distance = get_frame_distance(
        session,
        data["host"],
        frame,
        lat,
        lng,
        search_radius_km
    )

    radar_time = (
        datetime
        .fromtimestamp(
            frame["time"],
            timezone.utc
        )
        .isoformat()
    )

    if distance is None:
        return {
            "has_echo": False,
            "distance_km": None,
            "raining_here": False,
            "within_radius_km":
                search_radius_km,
            "radar_time":
                radar_time
        }

    return {
        "has_echo": True,

        "distance_km":
            round(distance, 1),

        "raining_here":
            distance <= 2,

        "within_radius_km":
            search_radius_km,

        "radar_time":
            radar_time
    }


def get_radar_approach(
    lat,
    lng,
    search_radius_km=100
):
    session = requests.Session()

    response = session.get(
        RAINVIEWER_API,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    frames = (
        data
        .get("radar", {})
        .get("past", [])
    )

    if len(frames) < 3:
        raise RuntimeError(
            "雷达历史帧不足"
        )

    # 取最近3帧
    selected_frames = frames[-3:]
    now = datetime.now(timezone.utc).timestamp()
    if any(not 0 <= now - f["time"] <= 1800 for f in selected_frames):
        raise RuntimeError("雷达数据已过期，跳过判断")

    records = []

    for frame in selected_frames:

        distance = get_frame_distance(
            session,
            data["host"],
            frame,
            lat,
            lng,
            search_radius_km
        )

        records.append({
            "time": frame["time"],
            "distance_km": (
                round(distance, 1)
                if distance is not None
                else None
            )
        })

    latest = records[-1]

    if latest["distance_km"] is None:
        return {
            "status": "no_echo",
            "approaching": False,
            "distance_km": None,
            "speed_kmh": None,
            "eta_minutes": None,
            "frames": records
        }

    if latest["distance_km"] <= 2:
        return {
            "status": "raining",
            "approaching": True,
            "distance_km":
                latest["distance_km"],
            "speed_kmh": None,
            "eta_minutes": 0,
            "frames": records
        }

    valid_records = [
        item
        for item in records
        if item["distance_km"]
        is not None
    ]

    if len(valid_records) < 2:
        return {
            "status": "unknown",
            "approaching": False,
            "distance_km":
                latest["distance_km"],
            "speed_kmh": None,
            "eta_minutes": None,
            "frames": records
        }

    first = valid_records[0]
    last = valid_records[-1]

    time_hours = (
        last["time"]
        - first["time"]
    ) / 3600

    if time_hours <= 0:
        return {
            "status": "unknown",
            "approaching": False,
            "distance_km":
                latest["distance_km"],
            "speed_kmh": None,
            "eta_minutes": None,
            "frames": records
        }

    distance_change = (
        first["distance_km"]
        - last["distance_km"]
    )

    speed_kmh = (
        distance_change
        / time_hours
    )

    # 变化太小，当作基本不动
    if speed_kmh <= 3:
        return {
            "status": "not_approaching",
            "approaching": False,
            "distance_km":
                latest["distance_km"],
            "speed_kmh":
                round(speed_kmh, 1),
            "eta_minutes": None,
            "frames": records
        }

    # 防止回波形态变化导致离谱速度
    if speed_kmh > 120:
        return {
            "status": "uncertain",
            "approaching": True,
            "distance_km":
                latest["distance_km"],
            "speed_kmh":
                round(speed_kmh, 1),
            "eta_minutes": None,
            "frames": records
        }

    eta_minutes = (
        latest["distance_km"]
        / speed_kmh
        * 60
    )

    return {
        "status": "approaching",
        "approaching": True,

        "distance_km":
            latest["distance_km"],

        "speed_kmh":
            round(
                speed_kmh,
                1
            ),

        "eta_minutes":
            max(
                1,
                round(eta_minutes)
            ),

        "frames":
            records
    }