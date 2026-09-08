import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_24h_forecast(latitude: float, longitude: float):
    """
    获取指定经纬度未来24小时天气预报
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,

        # 我们首页目前需要的数据
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m"
        ]),

        # 中国时间
        "timezone": "Asia/Shanghai",

        # 从当前时刻向后取24小时
        "forecast_hours": 24
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    hourly = data.get("hourly", {})

    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidity = hourly.get("relative_humidity_2m", [])
    precipitation_probability = hourly.get(
        "precipitation_probability",
        []
    )
    precipitation = hourly.get("precipitation", [])
    weather_codes = hourly.get("weather_code", [])
    pressure = hourly.get("surface_pressure", [])
    wind_speed = hourly.get("wind_speed_10m", [])
    wind_direction = hourly.get("wind_direction_10m", [])

    result = []

    for i in range(len(times)):
        result.append({
            "time": times[i],
            "temperature": temperatures[i],
            "humidity": humidity[i],
            "precipitation_probability":
                precipitation_probability[i],
            "precipitation": precipitation[i],
            "weather_code": weather_codes[i],
            "pressure": pressure[i],
            "wind_speed": wind_speed[i],
            "wind_direction": wind_direction[i]
        })

    return result


def get_2h_forecast(latitude: float, longitude: float):
    """
    获取未来2小时天气，用于首页“短时天气”
    """

    forecast = get_24h_forecast(
        latitude,
        longitude
    )

    # 只取最前面的两个小时
    next_two_hours = forecast[:2]

    if not next_two_hours:
        return {
            "text": "暂无短时天气预报数据"
        }

    temperatures = [
        item["temperature"]
        for item in next_two_hours
        if item["temperature"] is not None
    ]

    rain_probabilities = [
        item["precipitation_probability"]
        for item in next_two_hours
        if item["precipitation_probability"] is not None
    ]

    precipitation = [
        item["precipitation"]
        for item in next_two_hours
        if item["precipitation"] is not None
    ]

    wind_speeds = [
        item["wind_speed"]
        for item in next_two_hours
        if item["wind_speed"] is not None
    ]

    # -------------------------
    # 生成一段简单短时天气文字
    # -------------------------

    parts = []

    if temperatures:
        min_temp = min(temperatures)
        max_temp = max(temperatures)

        if min_temp == max_temp:
            parts.append(
                f"未来2小时气温约{min_temp:.0f}℃"
            )
        else:
            parts.append(
                f"未来2小时气温约"
                f"{min_temp:.0f}～{max_temp:.0f}℃"
            )

    if rain_probabilities:
        max_rain_probability = max(
            rain_probabilities
        )

        if max_rain_probability >= 70:
            parts.append("降水可能性较高")
        elif max_rain_probability >= 40:
            parts.append("有一定降水可能")
        elif max_rain_probability >= 20:
            parts.append("有小概率出现降水")
        else:
            parts.append("降水概率较低")

    if precipitation:
        total_rain = sum(precipitation)

        if total_rain > 0:
            parts.append(
                f"预计降水量约{total_rain:.1f}毫米"
            )

    if wind_speeds:
        max_wind = max(wind_speeds)

        parts.append(
            f"最大风速约{max_wind:.1f}km/h"
        )

    return {
        "text": "，".join(parts) + "。",
        "hours": next_two_hours
    }

def get_7d_forecast(latitude: float, longitude: float):
    """
    获取指定经纬度未来7天天气预报
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "precipitation_sum",
            "wind_speed_10m_max"
        ]),

        "timezone": "Asia/Shanghai",

        "forecast_days": 7
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    daily = data.get("daily", {})

    times = daily.get("time", [])
    weather_codes = daily.get("weather_code", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    rain_probability = daily.get(
        "precipitation_probability_max",
        []
    )
    precipitation_sum = daily.get(
        "precipitation_sum",
        []
    )
    max_wind_speed = daily.get(
        "wind_speed_10m_max",
        []
    )

    result = []

    for i in range(len(times)):
        result.append({
            "date": times[i],
            "weather_code": weather_codes[i],
            "temperature_max": max_temps[i],
            "temperature_min": min_temps[i],
            "precipitation_probability":
                rain_probability[i],
            "precipitation_sum":
                precipitation_sum[i],
            "wind_speed_max":
                max_wind_speed[i]
        })

    return result