import os
import requests
import re
import html
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

ARTICLE_FILE = Path(__file__).resolve().parent / "wechat_latest.json"


def get_article_url():
    import json

    if not ARTICLE_FILE.exists():
        return None

    with open(
        ARTICLE_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    return data.get("url")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Referer": "https://mp.weixin.qq.com/"
}


def clean_text(value):
    if not value:
        return None

    value = html.unescape(value)
    value = value.replace("\\x26", "&")
    value = value.replace("\\x3c", "<")
    value = value.replace("\\x3e", ">")
    value = value.replace("\\/", "/")
    value = value.replace('\\"', '"')
    value = value.replace("\\'", "'")

    return value.strip()


def extract_variable(text, variable_name):
    pattern = (
        rf'var\s+{re.escape(variable_name)}\s*=\s*'
        rf'(["\'])(.*?)\1'
        rf'(?:\.html\(false\))?\s*;'
    )

    match = re.search(
        pattern,
        text,
        re.S
    )

    if match:
        return clean_text(
            match.group(2)
        )

    return None


def extract_meta(text, property_name):
    patterns = [
        (
            rf'<meta[^>]+(?:property|name)=["\']'
            rf'{re.escape(property_name)}["\'][^>]+'
            rf'content=["\'](.*?)["\']'
        ),
        (
            rf'<meta[^>]+content=["\'](.*?)["\'][^>]+'
            rf'(?:property|name)=["\']'
            rf'{re.escape(property_name)}["\']'
        )
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.I | re.S
        )

        if match:
            return clean_text(
                match.group(1)
            )

    return None


def get_wechat_article():
    article_url = get_article_url()

    if not article_url:
        return {
            "success": False,
            "error": "未配置公众号文章 URL"
        }

    try:
        response = requests.get(
            article_url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        text = response.text

        title = (
            extract_meta(text, "og:title")
            or extract_variable(text, "msg_title")
        )

        author = (
            extract_variable(text, "nickname")
            or extract_meta(
                text,
                "og:article:author"
            )
        )

        cover = (
            extract_meta(text, "og:image")
            or extract_variable(
                text,
                "msg_cdn_url"
            )
        )

        publish_timestamp = (
            extract_variable(text, "ct")
        )

        publish_time = None

        if (
            publish_timestamp
            and publish_timestamp.isdigit()
        ):
            publish_time = (
                datetime.fromtimestamp(
                    int(publish_timestamp)
                ).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        return {
            "success": True,
            "title": title,
            "author": author,
            "cover": cover,
            "publish_time": publish_time,
            "url": article_url
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "url": article_url
        }

def update_wechat_article_url(new_url):
    import json

    if not new_url:
        return {
            "success": False,
            "error": "文章链接不能为空"
        }

    if not new_url.startswith(
        "https://mp.weixin.qq.com/"
    ):
        return {
            "success": False,
            "error": "请输入正确的微信公众号文章链接"
        }

    try:
        response = requests.get(
            new_url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        text = response.text

        title = (
            extract_meta(text, "og:title")
            or extract_variable(text, "msg_title")
        )

        if not title:
            return {
                "success": False,
                "error": "无法识别这篇微信文章"
            }

        with open(
            ARTICLE_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                {"url": new_url},
                f,
                ensure_ascii=False,
                indent=2
            )

        return {
            "success": True,
            "message": "最新文章更新成功",
            "title": title,
            "url": new_url
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    result = get_wechat_article()

    print("抓取结果：")

    for key, value in result.items():
        print(f"{key}：{value}")