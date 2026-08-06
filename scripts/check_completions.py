# maxkb-v3/scripts/check_completions.py
"""用官方 openai SDK 验证兼容端点。运行：uv run python scripts/check_completions.py <app_id> <access_token>"""
import sys
from openai import OpenAI

app_id, token = sys.argv[1], sys.argv[2]
client = OpenAI(base_url=f"http://127.0.0.1:8080/api/chat/{app_id}", api_key=token)
resp = client.chat.completions.create(
    model=app_id,                                     # 服务端按 app_id 路由，model 任意
    messages=[{"role": "user", "content": "你好，请介绍你自己"}],
    stream=True,
)
for chunk in resp:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print("\n[OK] OpenAI 兼容端点可被标准客户端调用")