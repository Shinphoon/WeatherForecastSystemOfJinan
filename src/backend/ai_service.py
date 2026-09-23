import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

ENV_PATH = BASE_DIR / ".env"

load_dotenv(
    ENV_PATH,
    override=True
)


API_KEY = os.getenv(
    "DEEPSEEK_API_KEY"
)

if not API_KEY:
    raise RuntimeError(
        "未配置 DEEPSEEK_API_KEY"
    )


client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"
)


SYSTEM_PROMPT = """
你是“济南天气AI助手”。

你可以根据系统提供的实时天气、天气预报、
用户位置、雷达回波等数据回答用户。

回答要求：

1. 使用自然、简洁、易懂的中文。

2. 优先使用系统提供的天气数据，
不要虚构不存在的实时数据。

3. 回答尽量紧凑。
不要使用过多空行，
不要为了排版频繁换行。

4. 可以使用 Markdown，
但不要使用过多标题。
简单问题优先使用短段落或简短列表。

5. 如果用户询问今天、明天、
未来天气，应直接总结天气状况、
气温、降水、风和出行建议。

6. 如果系统没有气象预警，
不要主动提到“没有预警”
“未获取到预警”
“无法确认预警”等内容。
只有用户主动询问预警时，
才说明预警情况。

7. 如果雷达显示没有降水回波，
除非用户询问降雨、雷达或出行风险，
否则不必主动提及雷达。

8. 雷达外推属于系统自动估计，
不能描述为官方天气预报。

9. 不要反复提醒用户
“请查看官方气象台”，
除非系统数据不足以回答
或涉及正式气象预警。
"""


def ask_deepseek(
    message,
    history=None,
    context=None,
    stream=False
):
    if history is None:
        history = []

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    if context:
        weather_context = json.dumps(
            context,
            ensure_ascii=False,
            default=str
        )

        messages.append({
            "role": "system",
            "content": f"""
    以下是本系统实时获取的天气数据。

    请优先根据这些数据回答用户问题。
    不要声称自己没有实时天气数据。
    如果某项数据缺失，再明确说明该项缺失。

    系统天气数据：
    {weather_context}
    """
        })

    for item in history[-10:]:
        role = item.get("role")
        content = item.get("content")

        if (
            role in ["user", "assistant"]
            and content
        ):
            messages.append({
                "role": role,
                "content": content
            })

    messages.append({
        "role": "user",
        "content": message
    })

    response = (
        client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            temperature=0.4,
            max_tokens=1200,
            stream=stream
        )
    )

    if stream:
        return response

    return (
        response
        .choices[0]
        .message
        .content
    )