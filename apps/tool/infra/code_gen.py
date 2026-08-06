# apps/tool/infra/code_gen.py
# coding=utf-8
"""AI 生成工具代码骨架：提示词工程 + ModelGateway 调用 + Python 代码抽取"""
import json
import re
from model_platform.service.gateway import gateway

_SYSTEM = """你是一名资深 Python 工程师。根据「工具描述」与「输入参数 JSON Schema」生成一个可运行的 Python 工具函数。
要求：
1. 输出纯 Python 代码，只允许使用标准库，禁止网络/文件/子进程/反射等敏感操作（沙箱会拦截）。
2. 入参从 `_inputs` 字典读取，键与 JSON Schema 的 properties 一致。
3. 通过 `_maxkb_returns(**kwargs)` 把计算结果返回（服务端会收集该变量）。
4. 用```python```代码块包裹输出。"""


def extract_python(text: str) -> str:
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


class CodeGenService:
    @staticmethod
    def generate(desc: str, input_schema: dict, model_id: str) -> str:
        model = gateway.get_model(model_id)
        prompt = f"工具描述：{desc}\n输入参数 Schema：\n{json.dumps(input_schema, ensure_ascii=False, indent=2)}"
        resp = model.invoke([{"role": "system", "content": _SYSTEM},
                             {"role": "user", "content": prompt}])   # invoke 返回字符串
        return extract_python(resp)