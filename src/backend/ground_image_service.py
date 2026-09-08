from datetime import datetime, timedelta
import requests

BASE_URL = "https://jnapp.weathermate.com.cn:8009/media/data/product_img/blend"

def build_image_url(start_time: datetime, end_time: datetime):
    date_str = end_time.strftime("%Y%m%d")
    start_str = start_time.strftime("%Y%m%d%H%M%S")
    end_str = end_time.strftime("%Y%m%d%H%M%S")

    return (
        f"{BASE_URL}/{date_str}/"
        f"total_pre_济南市_{start_str}_{end_str}_1.png"
    )

def find_latest_ground_image():
    now = datetime.now()

    # 从最近一个完整整点开始向前找
    end_time = now.replace(
        minute=0,
        second=0,
        microsecond=0
    )

    # 最多往前查 12 小时
    for _ in range(12):
        start_time = end_time - timedelta(hours=1)
        image_url = build_image_url(
            start_time,
            end_time
        )

        try:
            response = requests.head(
                image_url,
                timeout=5,
                verify=False
            )

            if response.status_code == 200:
                return {
                    "url": image_url,
                    "start_time":
                        start_time.strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    "end_time":
                        end_time.strftime(
                            "%Y-%m-%d %H:%M"
                        )
                }

        except requests.RequestException:
            pass

        end_time = start_time

    return None