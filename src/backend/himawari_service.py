import io
import requests
from PIL import Image

HIMAWARI_URL = (
    "https://www.data.jma.go.jp/mscweb/data/"
    "himawari/img/jpn/jpn_tre_0640.jpg"
)

def download_himawari_image():
    response = requests.get(
        HIMAWARI_URL,
        timeout=15
    )
    response.raise_for_status()

    return Image.open(
        io.BytesIO(response.content)
    ).convert("RGB")

def crop_shandong(image):
    return image.crop(
        (
            25,
            165,
            255,
            350
        )
    )

def get_shandong_himawari():
    image = download_himawari_image()

    cropped = crop_shandong(image)

    output = io.BytesIO()

    cropped.save(
        output,
        format="JPEG",
        quality=92
    )

    output.seek(0)

    return output
